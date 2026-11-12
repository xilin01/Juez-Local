"""Comparador, diff y veredictos básicos, con programas triviales en Python para no depender del compilador."""
from pathlib import Path
import pytest
from juez.cli import main
from juez.juzgar import diff_legible


def escribir_caso(carpeta: Path, programa: str) -> Path:
    """Crea en `carpeta` un programa y un caso cuya respuesta correcta es el doble de la entrada."""
    sol = carpeta / 'sol.py'
    sol.write_text(programa)
    (carpeta / 'caso.in').write_text('21\n')
    (carpeta / 'caso.out').write_text('42\n')
    return sol


def test_lineas_ignora_espacios_y_lineas_vacias_finales(tmp_path: Path) -> None:
    archivo = tmp_path / 'salida.txt'
    archivo.write_text('1 2  \n\n3\n\n\n')
    from juez.juzgar import lineas
    assert lineas(archivo) == ['1 2', '', '3']


def test_diff_senala_la_primera_linea_distinta() -> None:
    diff = diff_legible(['1', '2', '3'], ['1', '5', '3'])
    assert 'línea 2' in diff
    assert '-2' in diff.splitlines() and '+5' in diff.splitlines()


def test_diff_cuando_falta_salida() -> None:
    diff = diff_legible(['1', '2'], ['1'])
    assert 'línea 2' in diff and '-2' in diff.splitlines()


@pytest.mark.parametrize('programa, veredicto', [('print(int(input()) * 2)', 'AC'), ('print(int(input()) + 2)', 'WA'), ('raise SystemExit(3)', 'RTE')])
def test_veredictos_basicos(tmp_path: Path, programa: str, veredicto: str) -> None:
    sol = escribir_caso(tmp_path, programa)
    import sys
    from juez.juzgar import juzgar_caso
    from juez.plataforma import Limites
    informe = juzgar_caso([sys.executable, str(sol)], tmp_path / 'caso.in', tmp_path / 'caso.out', Limites())
    assert informe.veredicto == veredicto
    assert (informe.detalle != '') == (veredicto in ('WA', 'RTE'))


def test_run_informa_por_caso_y_devuelve_estado(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sol = escribir_caso(tmp_path, 'print(int(input()) + 2)')
    assert main(['run', str(sol), str(tmp_path)]) == 1
    salida = capsys.readouterr().out
    assert 'caso | WA' in salida and '-42' in salida and '+23' in salida and '0/1 AC' in salida


def test_run_falla_si_falta_un_out(tmp_path: Path) -> None:
    sol = escribir_caso(tmp_path, 'print(42)')
    (tmp_path / 'caso.out').unlink()
    with pytest.raises(SystemExit): main(['run', str(sol), str(tmp_path)])
