"""
Capa de sistema operativo.
El resto del código solo usa `ejecutar(cmd, entrada, salida, limites) -> Resultado`, `Limites` y `Resultado`, y no sabe en qué sistema corre.
"""
import sys
from .tipos import Limites, Resultado


if sys.platform == 'win32': from .windows import ejecutar
else: from .linux import ejecutar
