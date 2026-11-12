"""`-j N`: mismos veredictos, tiempos de CPU sin inflar y casos que de verdad corren a la vez."""
import re
import time
from pathlib import Path
import pytest
from conftest import EXE, RAIZ
from juez.cli import main


CASOS = RAIZ / 'ejemplos' / 'casos'


def tiempos(salida: str) -> list[float]:
    return [float(t) for t in re.findall(r'^\S+ +\| \w+ +\| +([0-9.]+) s \|', salida, re.MULTILINE)] # Solo las filas de caso, no la cabecera.


def test_paralelo_da_los_mismos_veredictos_y_en_orden(binarios: Path, capsys: pytest.CaptureFixture[str]) -> None:
    salidas = []

    for trabajos in ('1', '4'):
        assert main(['run', str(binarios / ('lenta' + EXE)), str(CASOS), '-j', trabajos]) == 1
        salidas.append(re.findall(r'^(\S+) +\| (\w+)', capsys.readouterr().out, re.MULTILINE))
    assert salidas[0] == salidas[1] and [veredicto for _, veredicto in salidas[0]] == ['AC', 'AC', 'AC', 'AC', 'TLE']


def test_paralelo_no_infla_el_tiempo_de_cpu(binarios: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Cuatro copias de un caso que cuesta unas décimas de CPU: cada una debe medir lo mismo sola que acompañada."""
    for i in range(4):
        (tmp_path / f'{i}.in').write_text(f'1500\n{" ".join(["1"] * 1500)}\n')
        (tmp_path / f'{i}.out').write_text('1500\n')
    medidas = []
    for trabajos in ('1', '2'):
        assert main(['run', str(binarios / ('lenta' + EXE)), str(tmp_path), '-t', '10', '-j', trabajos]) == 0
        medidas.append(tiempos(capsys.readouterr().out))
    assert len(medidas[1]) == 4 and max(medidas[1]) <= 1.5 * max(medidas[0]) + 0.15


def test_paralelo_ejecuta_a_la_vez(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Cuatro programas que esperan 0,7 s: en serie serían 2,8 s de reloj."""
    sol = tmp_path / 'espera.py'
    sol.write_text('import time\ntime.sleep(0.7)\nprint(1)')

    for i in range(4):
        (tmp_path / f'{i}.in').write_text('')
        (tmp_path / f'{i}.out').write_text('1\n')
    t0 = time.perf_counter()
    assert main(['run', str(sol), str(tmp_path), '-t', '2', '-j', '4']) == 0
    assert time.perf_counter() - t0 < 2.8


def test_j_debe_ser_positivo(tmp_path: Path) -> None:
    with pytest.raises(SystemExit): main(['run', 'x', str(tmp_path), '-j', '0'])
