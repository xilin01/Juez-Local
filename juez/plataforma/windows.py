"""Windows: los límites se aplican con un Job Object por ejecución, llamando a kernel32 con ctypes."""
import ctypes
import os
import subprocess
import time
import _winapi
from ctypes import wintypes
from pathlib import Path
from .tipos import Limites, Resultado


# Constantes de winnt.h y winbase.h.
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x0200
JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x0400 # Sin esto, un programa que revienta puede abrir un diálogo de error y quedarse colgado.
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000 # Al cerrar el job mueren también los procesos hijos que queden vivos.
JOB_OBJECT_MSG_JOB_MEMORY_LIMIT = 10
INFO_CONTABILIDAD, INFO_PUERTO, INFO_LIMITES = 1, 7, 9 # Valores de JOBOBJECTINFOCLASS.
CREATE_SUSPENDED = 0x4
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
RESUME_FALLIDO = 0xFFFFFFFF
SONDEO_MS = 10 # Cada cuánto se mira el tiempo de CPU; es lo máximo que un programa puede pasarse del límite antes de morir.


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [('PerProcessUserTimeLimit', ctypes.c_int64), ('PerJobUserTimeLimit', ctypes.c_int64), ('LimitFlags', wintypes.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t), ('MaximumWorkingSetSize', ctypes.c_size_t), ('ActiveProcessLimit', wintypes.DWORD),
                ('Affinity', ctypes.c_size_t), ('PriorityClass', wintypes.DWORD), ('SchedulingClass', wintypes.DWORD)]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(nombre, ctypes.c_uint64) for nombre in ('ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount',
                                                         'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION), ('IoInfo', IO_COUNTERS), ('ProcessMemoryLimit', ctypes.c_size_t),
                ('JobMemoryLimit', ctypes.c_size_t), ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]


class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
    _fields_ = [('TotalUserTime', ctypes.c_int64), ('TotalKernelTime', ctypes.c_int64), ('ThisPeriodTotalUserTime', ctypes.c_int64),
                ('ThisPeriodTotalKernelTime', ctypes.c_int64), ('TotalPageFaultCount', wintypes.DWORD), ('TotalProcesses', wintypes.DWORD),
                ('ActiveProcesses', wintypes.DWORD), ('TotalTerminatedProcesses', wintypes.DWORD)]


class JOBOBJECT_ASSOCIATE_COMPLETION_PORT(ctypes.Structure):
    _fields_ = [('CompletionKey', wintypes.LPVOID), ('CompletionPort', wintypes.HANDLE)]


def comprobar(resultado: int | None, funcion: object, argumentos: tuple) -> int | None:
    """`errcheck` de ctypes: convierte el fallo de una llamada de Win32 en una excepción con su mensaje."""
    if not resultado: raise ctypes.WinError(ctypes.get_last_error())
    return resultado


def cargar_kernel32() -> ctypes.WinDLL:
    """
    Declara los tipos de cada función que se usa.
    Sin `argtypes` y `restype`, ctypes trata los handles como enteros de 32 bits y en Windows de 64 los trunca.
    """
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    HANDLE, DWORD, LPVOID = wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID
    firmas = {'CreateJobObjectW': (HANDLE, [LPVOID, wintypes.LPCWSTR]),
              'SetInformationJobObject': (wintypes.BOOL, [HANDLE, ctypes.c_int, LPVOID, DWORD]),
              'QueryInformationJobObject': (wintypes.BOOL, [HANDLE, ctypes.c_int, LPVOID, DWORD, wintypes.LPDWORD]),
              'AssignProcessToJobObject': (wintypes.BOOL, [HANDLE, HANDLE]),
              'TerminateJobObject': (wintypes.BOOL, [HANDLE, wintypes.UINT]),
              'CreateIoCompletionPort': (HANDLE, [HANDLE, HANDLE, ctypes.c_size_t, DWORD])}

    for nombre, (retorno, argumentos) in firmas.items():
        funcion = getattr(k32, nombre)
        funcion.restype, funcion.argtypes, funcion.errcheck = retorno, argumentos, comprobar
    # Estas dos devuelven valores que no significan «error» cuando son cero, así que no llevan `errcheck`.
    k32.ResumeThread.restype, k32.ResumeThread.argtypes = DWORD, [HANDLE]
    k32.GetQueuedCompletionStatus.restype = wintypes.BOOL
    k32.GetQueuedCompletionStatus.argtypes = [HANDLE, wintypes.LPDWORD, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(LPVOID), DWORD]
    return k32


def crear_suspendido(cmd: list[str], entrada: Path, salida: Path) -> tuple[int, int]:
    """
    Crea el proceso detenido, para poder meterlo en el job antes de que ejecute una sola instrucción.
    Devuelve los handles (proceso, hilo principal).
    Se llama a `CreateProcess` directamente porque `subprocess.Popen` cierra el handle del hilo, que hace falta para reanudarlo.
    """
    with open(entrada, 'rb') as f_in, open(salida, 'wb') as f_out, open(os.devnull, 'wb') as f_err:
        import msvcrt
        handles = [msvcrt.get_osfhandle(f.fileno()) for f in (f_in, f_out, f_err)]

        for handle in handles: os.set_handle_inheritable(handle, True)
        # `handle_list`: el hijo hereda solo estos tres handles y no cualquier otro heredable que tenga el juez abierto.
        inicio = subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESTDHANDLES, hStdInput=handles[0], hStdOutput=handles[1], hStdError=handles[2],
                                        lpAttributeList={'handle_list': handles})
        proceso, hilo, _, _ = _winapi.CreateProcess(None, subprocess.list2cmdline(cmd), None, None, True, CREATE_SUSPENDED, None, None, inicio)
    return (proceso, hilo)


def mensajes_del_job(puerto: int) -> set[int]:
    """Vacía el puerto de finalización: el job deja en él un mensaje cada vez que se alcanza uno de sus límites."""
    mensaje, clave, extra = wintypes.DWORD(), ctypes.c_size_t(), wintypes.LPVOID()
    mensajes = set()

    while K32.GetQueuedCompletionStatus(puerto, ctypes.byref(mensaje), ctypes.byref(clave), ctypes.byref(extra), 0): mensajes.add(mensaje.value)
    return mensajes


def cpu_del_job(job: int) -> float:
    """Segundos de CPU (usuario + núcleo) que llevan gastados todos los procesos del job."""
    contabilidad = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
    K32.QueryInformationJobObject(job, INFO_CONTABILIDAD, ctypes.byref(contabilidad), ctypes.sizeof(contabilidad), None)
    return (contabilidad.TotalUserTime + contabilidad.TotalKernelTime) / 1e7 # Vienen en unidades de 100 ns.


def ejecutar(cmd: list[str], entrada: Path, salida: Path, limites: Limites) -> Resultado:
    job = K32.CreateJobObjectW(None, None)
    puerto = K32.CreateIoCompletionPort(INVALID_HANDLE_VALUE, None, 0, 1)

    try:
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        info.JobMemoryLimit = limites.memoria_mb << 20
        asociacion = JOBOBJECT_ASSOCIATE_COMPLETION_PORT(None, puerto)
        K32.SetInformationJobObject(job, INFO_LIMITES, ctypes.byref(info), ctypes.sizeof(info))
        K32.SetInformationJobObject(job, INFO_PUERTO, ctypes.byref(asociacion), ctypes.sizeof(asociacion))
        proceso, hilo = crear_suspendido(cmd, entrada, salida)
        try:
            K32.AssignProcessToJobObject(job, proceso)
            if K32.ResumeThread(hilo) == RESUME_FALLIDO: raise ctypes.WinError(ctypes.get_last_error())
            t0, agotado = time.monotonic(), False
            # El límite de tiempo propio del job no sirve: Windows solo lo revisa cada varios segundos. Se sondea la contabilidad del job.
            while not agotado and _winapi.WaitForSingleObject(proceso, SONDEO_MS) == _winapi.WAIT_TIMEOUT:
                agotado = cpu_del_job(job) >= limites.tiempo_s or time.monotonic() - t0 >= limites.reloj_s
            if agotado:
                K32.TerminateJobObject(job, 1)
                _winapi.WaitForSingleObject(proceso, _winapi.INFINITE)
            codigo = _winapi.GetExitCodeProcess(proceso)
        except BaseException:
            _winapi.TerminateProcess(proceso, 1) # Si no llegó a entrar en el job, cerrar el job no lo mataría.
            raise
        finally:
            _winapi.CloseHandle(hilo)
            _winapi.CloseHandle(proceso)
        cpu_s = cpu_del_job(job)
        K32.QueryInformationJobObject(job, INFO_LIMITES, ctypes.byref(info), ctypes.sizeof(info), None)
        mensajes = mensajes_del_job(puerto)
    finally:
        _winapi.CloseHandle(puerto)
        _winapi.CloseHandle(job)
    return Resultado(codigo, cpu_s, info.PeakJobMemoryUsed // 1024, agotado or cpu_s >= limites.tiempo_s, JOB_OBJECT_MSG_JOB_MEMORY_LIMIT in mensajes)


K32 = cargar_kernel32()
