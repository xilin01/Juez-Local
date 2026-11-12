"""Compila una vez por sesión las soluciones de `ejemplos/` y los programas de prueba de `tests/`."""
import subprocess
import sys
from pathlib import Path
import pytest


RAIZ = Path(__file__).parent.parent
EXE = '.exe' if sys.platform == 'win32' else ''


@pytest.fixture(scope='session')
def binarios(tmp_path_factory: pytest.TempPathFactory) -> Path:
    carpeta = tmp_path_factory.mktemp('bin')
    estatico = ['-static'] if sys.platform == 'win32' else [] # En Windows evita depender de que las DLL de MinGW estén en el PATH.

    for fuente in [*(RAIZ / 'ejemplos').glob('*.cpp'), *(RAIZ / 'tests').glob('*.cpp')]:
        subprocess.run(['g++', '-O2', *estatico, '-o', str(carpeta / (fuente.stem + EXE)), str(fuente)], check=True)
    return carpeta
