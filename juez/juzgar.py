"""Juzga un caso: ejecuta el programa, clasifica cómo terminó y compara su salida con la esperada."""
import tempfile
from dataclasses import dataclass
from pathlib import Path
from .plataforma import Limites, ejecutar


@dataclass(frozen=True)
class Informe:
    nombre: str
    veredicto: str # AC, WA, TLE, MLE o RTE.
    cpu_s: float
    memoria_kb: int
    detalle: str # Diff en WA y causa en RTE; vacío en los demás.


def lineas(ruta: Path) -> list[str]:
    """Líneas del archivo sin espacios finales ni líneas vacías al final, que es lo que ignoran los jueces."""
    texto = ruta.read_text(encoding='utf-8', errors='replace')
    return [linea.rstrip() for linea in texto.rstrip().splitlines()]


def diff_legible(esperado: list[str], obtenido: list[str]) -> str:
    """Las líneas que rodean a la primera diferencia, con `-` para lo esperado y `+` para lo obtenido."""
    i = next((k for k, (a, b) in enumerate(zip(esperado, obtenido)) if a != b), min(len(esperado), len(obtenido)))
    ini, fin = max(0, i - 2), i + 8
    # Solo se compara una ventana: difflib es cuadrático y una salida puede tener cientos de miles de líneas.
    import difflib
    cuerpo = list(difflib.unified_diff(esperado[ini:fin], obtenido[ini:fin], lineterm='', n=2))[2:] # Sin las dos líneas de cabecera.
    return '\n'.join([f'Primera diferencia en la línea {i + 1} (- esperado, + obtenido):'] + [linea[:200] for linea in cuerpo if not linea.startswith('@@')])


def causa(codigo: int) -> str:
    if codigo < 0:
        import signal
        return f'señal {-codigo} ({signal.strsignal(-codigo)})'
    return f'código de salida {codigo:#x}' if codigo > 0xFFFF else f'código de salida {codigo}' # En hexadecimal se reconocen los de Windows, como 0xc0000005.


def juzgar_caso(cmd: list[str], entrada: Path, esperada: Path, limites: Limites) -> Informe:
    # En Windows el borrado puede fallar si un proceso recién muerto aún no ha soltado el archivo.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        salida = Path(tmp) / 'salida.txt'
        res = ejecutar(cmd, entrada, salida, limites)
        veredicto, detalle = 'AC', ''

        if res.tle: veredicto = 'TLE'
        elif res.mle: veredicto = 'MLE'
        elif res.codigo != 0: veredicto, detalle = 'RTE', causa(res.codigo)
        else:
            esperado, obtenido = lineas(esperada), lineas(salida)
            if esperado != obtenido: veredicto, detalle = 'WA', diff_legible(esperado, obtenido)
    return Informe(entrada.stem, veredicto, res.cpu_s, res.memoria_kb, detalle)
