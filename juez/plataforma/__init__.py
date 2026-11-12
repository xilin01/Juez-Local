"""Capa de sistema operativo: el resto del código solo usa `ejecutar`, `Limites` y `Resultado`."""
import subprocess
import time
from pathlib import Path
from .tipos import Limites, Resultado


def ejecutar(cmd: list[str], entrada: Path, salida: Path, limites: Limites) -> Resultado:
    """Versión provisional y portable: no aplica límites y mide tiempo de reloj."""
    with open(entrada, 'rb') as f_in, open(salida, 'wb') as f_out:
        t0 = time.perf_counter()
        codigo = subprocess.run(cmd, stdin=f_in, stdout=f_out, stderr=subprocess.DEVNULL).returncode
    return Resultado(codigo, time.perf_counter() - t0, 0, False, False)
