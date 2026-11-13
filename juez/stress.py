"""Prueba de estrés: busca una entrada aleatoria en la que la solución discrepa de la fuerza bruta y después la reduce."""
import subprocess
import sys
from pathlib import Path
from .juzgar import Informe
from .plataforma import Limites


SEMILLAS_REDUCCION = 20 # Semillas que se prueban con cada tamaño menor.


def probar(sol: list[str], bruta: list[str], gen: list[str], semilla: int, tam: int, limites: Limites, carpeta: Path, stderr: int | None = None) -> Informe:
    """
    Escribe en `carpeta` el caso de esa semilla y ese tamaño, con la salida de la fuerza bruta como esperada, y juzga la solución contra él.
    El generador y la fuerza bruta se ejecutan sin límites: son programas de confianza.
    """
    entrada, esperada = carpeta / 'caso.in', carpeta / 'caso.out'

    with open(entrada, 'wb') as f: subprocess.run(gen + [str(semilla), str(tam)], stdout=f, stderr=stderr, check=True)
    with open(entrada, 'rb') as f_in, open(esperada, 'wb') as f_out: subprocess.run(bruta, stdin=f_in, stdout=f_out, stderr=stderr, check=True)
    from .juzgar import juzgar_caso
    return juzgar_caso(sol, entrada, esperada, limites)


def stress(sol: list[str], bruta: list[str], gen: list[str], limites: Limites, semilla: int, iteraciones: int, tam: int, carpeta: Path) -> int:
    """Devuelve 1 si encuentra una discrepancia, que deja guardada en `carpeta`, y 0 si no."""
    import tempfile
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        def falla(candidato: tuple[int, int], stderr: int | None = None) -> bool:
            if sys.stdout.isatty(): print(f'\r[stress] Semilla {candidato[0]}, tamaño {candidato[1]}...   ', end='', flush=True)
            return probar(sol, bruta, gen, *candidato, limites, Path(tmp), stderr).veredicto != 'AC'

        def falla_menor(candidato: tuple[int, int]) -> bool:
            # Un generador puede no admitir tamaños pequeños: ese candidato se descarta, en silencio, y la discrepancia ya encontrada sigue valiendo.
            try: return falla(candidato, subprocess.DEVNULL)
            except subprocess.CalledProcessError: return False

        primero = next((c for c in ((s, tam) for s in range(semilla, semilla + iteraciones)) if falla(c)), None)
        if sys.stdout.isatty(): print()
        if primero is None:
            print(f'[stress] Sin discrepancias en {iteraciones} casos de tamaño {tam}.')
            return 0
        print(f'[stress] Discrepancia con semilla {primero[0]} y tamaño {primero[1]}. Buscando un caso menor...')
        # Reducción: tamaños crecientes (1, 2, 4...) por debajo del original; el primer fallo que aparezca es el más pequeño.
        menores = [(s, t) for t in (2 ** k for k in range((tam - 1).bit_length())) for s in range(semilla, semilla + SEMILLAS_REDUCCION)]
        semilla, tam = next((c for c in menores if falla_menor(c)), primero)
        if sys.stdout.isatty(): print()
    # El generador es determinista: repetir el caso elegido lo deja escrito en la carpeta de salida.
    carpeta.mkdir(parents=True, exist_ok=True)
    informe = probar(sol, bruta, gen, semilla, tam, limites, carpeta)
    print(f'[stress] {informe.veredicto} con semilla {semilla} y tamaño {tam}.')
    if informe.detalle: print('    ' + informe.detalle.replace('\n', '\n    '))
    print(f'[stress] Caso guardado en {carpeta / "caso.in"} y {carpeta / "caso.out"}.')
    return 1
