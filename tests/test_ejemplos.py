"""Cada solución de `ejemplos/` recibe su veredicto, y los límites cortan lo que deben cortar."""
from pathlib import Path
import pytest
from conftest import EXE, RAIZ
from juez.juzgar import Informe
from juez.plataforma import Limites


CASOS = RAIZ / 'ejemplos' / 'casos'
# Veredicto de cada solución en los casos 01 a 05.
ESPERADO = {'correcta': ['AC', 'AC', 'AC', 'AC', 'AC'],
            'incorrecta': ['AC', 'WA', 'AC', 'AC', 'AC'],
            'lenta': ['AC', 'AC', 'AC', 'AC', 'TLE'],
            'memoria': ['AC', 'AC', 'AC', 'AC', 'MLE'],
            'revienta': ['RTE', 'RTE', 'RTE', 'RTE', 'RTE']}


def juzgar(cmd: list[str], caso: str, limites: Limites = Limites()) -> Informe:
    from juez.juzgar import juzgar_caso
    return juzgar_caso(cmd, CASOS / f'{caso}.in', CASOS / f'{caso}.out', limites)


def script(carpeta: Path, codigo: str) -> list[str]:
    ruta = carpeta / 'programa.py'
    ruta.write_text(codigo)
    import sys
    return [sys.executable, str(ruta)]


@pytest.mark.parametrize('solucion', ESPERADO)
def test_cada_solucion_recibe_su_veredicto(binarios: Path, solucion: str) -> None:
    casos = sorted(entrada.stem for entrada in CASOS.glob('*.in'))
    assert [juzgar([str(binarios / (solucion + EXE))], caso).veredicto for caso in casos] == ESPERADO[solucion]


def test_mide_tiempo_y_memoria(binarios: Path) -> None:
    informe = juzgar([str(binarios / ('correcta' + EXE))], '05-grande')
    assert 0 <= informe.cpu_s < 1 and informe.memoria_kb > 0


def test_tle_corta_cerca_del_limite(binarios: Path) -> None:
    informe = juzgar([str(binarios / ('lenta' + EXE))], '05-grande', Limites(tiempo_s=0.3))
    assert informe.veredicto == 'TLE' and 0.3 <= informe.cpu_s < 1.5


def test_reserva_unica_enorme_es_mle(binarios: Path) -> None:
    """La reserva falla de golpe, sin que el pico de memoria se acerque al límite: no debe confundirse con RTE."""
    assert juzgar([str(binarios / ('reserva_unica' + EXE))], '03-un-elemento').veredicto == 'MLE'


def test_programa_que_espera_sin_gastar_cpu_es_tle(tmp_path: Path) -> None:
    assert juzgar(script(tmp_path, 'import time\ntime.sleep(30)'), '03-un-elemento', Limites(tiempo_s=0.2)).veredicto == 'TLE'


def test_limite_de_memoria_configurable(tmp_path: Path) -> None:
    cmd = script(tmp_path, 'x = bytearray(200 << 20)\nprint(7)')
    assert juzgar(cmd, '03-un-elemento').veredicto == 'AC'
    assert juzgar(cmd, '03-un-elemento', Limites(memoria_mb=128)).veredicto == 'MLE'


def test_run_acepta_limites_por_opcion(binarios: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from juez.cli import main
    assert main(['run', str(binarios / ('lenta' + EXE)), str(CASOS), '-t', '0.3', '-m', '64']) == 1
    salida = capsys.readouterr().out
    assert '0.3 s | 64 MB' in salida and '05-grande      | TLE' in salida and '4/5 AC' in salida
