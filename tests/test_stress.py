"""`juez stress`: encuentra la discrepancia, la reduce y la deja guardada."""
from pathlib import Path
import pytest
from conftest import EXE, RAIZ
from juez.cli import main
from juez.juzgar import juzgar_caso
from juez.plataforma import Limites


GEN = str(RAIZ / 'ejemplos' / 'gen.py')


def test_stress_encuentra_reduce_y_guarda(binarios: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    incorrecta, lenta, fallo = str(binarios / ('incorrecta' + EXE)), str(binarios / ('lenta' + EXE)), tmp_path / 'fallo'
    assert main(['stress', incorrecta, lenta, GEN, '--tam', '10', '-o', str(fallo)]) == 1
    salida = capsys.readouterr().out
    assert 'Discrepancia' in salida and 'WA con semilla' in salida and 'Primera diferencia' in salida
    # El error aparece con un solo número negativo, así que la reducción debe llegar a n = 1.
    assert (fallo / 'caso.in').read_text().split()[0] == '1'
    assert juzgar_caso([incorrecta], fallo / 'caso.in', fallo / 'caso.out', Limites()).veredicto == 'WA'
    assert juzgar_caso([lenta], fallo / 'caso.in', fallo / 'caso.out', Limites()).veredicto == 'AC'


def test_stress_sin_discrepancias_no_guarda_nada(binarios: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    correcta, lenta, fallo = str(binarios / ('correcta' + EXE)), str(binarios / ('lenta' + EXE)), tmp_path / 'fallo'
    assert main(['stress', correcta, lenta, GEN, '-n', '20', '-o', str(fallo)]) == 0
    assert 'Sin discrepancias en 20 casos' in capsys.readouterr().out and not fallo.exists()


def test_stress_con_un_error_en_ejecucion_tambien_es_fallo(binarios: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    revienta, lenta, fallo = str(binarios / ('revienta' + EXE)), str(binarios / ('lenta' + EXE)), tmp_path / 'fallo'
    assert main(['stress', revienta, lenta, GEN, '-o', str(fallo)]) == 1
    assert 'RTE con semilla' in capsys.readouterr().out and (fallo / 'caso.out').is_file()


def test_stress_guarda_el_caso_aunque_el_generador_no_admita_tamanos_menores(binarios: Path, tmp_path: Path) -> None:
    """Con tamaño 1 este generador falla: la reducción debe saltarse ese tamaño y no perder la discrepancia."""
    gen = tmp_path / 'gen.py'
    gen.write_text('import random, sys\nrng = random.Random(int(sys.argv[1]))\ntam = int(sys.argv[2])\nn = rng.randint(2, tam)\n'
                   'print(n)\nprint(*(rng.randint(-tam, tam) for _ in range(n)))')
    incorrecta, lenta, fallo = str(binarios / ('incorrecta' + EXE)), str(binarios / ('lenta' + EXE)), tmp_path / 'fallo'
    assert main(['stress', incorrecta, lenta, str(gen), '-o', str(fallo)]) == 1
    assert int((fallo / 'caso.in').read_text().split()[0]) >= 2
    assert juzgar_caso([incorrecta], fallo / 'caso.in', fallo / 'caso.out', Limites()).veredicto == 'WA'


def test_stress_avisa_si_el_generador_falla(binarios: Path, tmp_path: Path) -> None:
    gen = tmp_path / 'gen.py'
    gen.write_text('raise SystemExit(5)')
    correcta = str(binarios / ('correcta' + EXE))
    with pytest.raises(SystemExit, match='código 5'): main(['stress', correcta, correcta, str(gen), '-o', str(tmp_path / 'fallo')])
