"""Linux: los límites se aplican con setrlimit en el proceso hijo y las medidas salen de wait4."""
import os
import resource
import time
from pathlib import Path
from .tipos import Limites, Resultado


PISTAS_SIN_MEMORIA = (b'bad_alloc', b'MemoryError') # Lo que escriben C++ y Python en stderr cuando les falla una reserva.


def limitar(limites: Limites) -> None:
    """Se ejecuta en el hijo, entre fork y exec: así los límites afectan al programa y no al juez."""
    import math
    cpu = math.ceil(limites.tiempo_s) # RLIMIT_CPU solo admite segundos enteros; el veredicto usa el tiempo medido.
    memoria = limites.memoria_mb << 20
    resource.setrlimit(resource.RLIMIT_AS, (memoria, memoria))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1)) # Límite blando: SIGXCPU. Límite duro: SIGKILL, por si el programa ignora la señal.
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0)) # Sin volcado de memoria, que retrasa la muerte del proceso.


def ejecutar(cmd: list[str], entrada: Path, salida: Path, limites: Limites) -> Resultado:
    import tempfile
    with open(entrada, 'rb') as f_in, open(salida, 'wb') as f_out, tempfile.TemporaryFile() as f_err:
        t0 = time.monotonic()
        import subprocess
        proc = subprocess.Popen(cmd, stdin=f_in, stdout=f_out, stderr=f_err, preexec_fn=lambda: limitar(limites))
        import threading
        vigilante = threading.Timer(limites.reloj_s, proc.kill)
        vigilante.start()
        _, estado, uso = os.wait4(proc.pid, 0) # wait4 y no proc.wait: además del estado devuelve el consumo de recursos del hijo.
        vigilante.cancel()
        vigilante.join() # El hilo debe haber terminado antes del próximo fork: preexec_fn no es seguro con otros hilos vivos.
        agotado = time.monotonic() - t0 >= limites.reloj_s
        proc.returncode = codigo = os.waitstatus_to_exitcode(estado) # Popen no sabe que wait4 ya recogió al hijo.
        errores = os.pread(f_err.fileno(), 4096, max(0, os.fstat(f_err.fileno()).st_size - 4096))
    import signal
    cpu_s = uso.ru_utime + uso.ru_stime
    tle = agotado or codigo == -signal.SIGXCPU or cpu_s >= limites.tiempo_s
    # RLIMIT_AS no avisa: la reserva falla y el programa muere como en cualquier otro error. La única pista es lo que deja en stderr.
    mle = not tle and codigo != 0 and any(pista in errores for pista in PISTAS_SIN_MEMORIA)
    return Resultado(codigo, cpu_s, uso.ru_maxrss, tle, mle)
