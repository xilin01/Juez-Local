"""Interfaz de línea de comandos."""
import argparse
import shutil
import sys
from itertools import repeat
from pathlib import Path
from .plataforma import Limites


def comando(ruta: str) -> list[str]:
    """Los `.py` se lanzan con el intérprete actual; lo demás debe ser un ejecutable."""
    if ruta.endswith('.py') and Path(ruta).is_file(): return [sys.executable, ruta]
    # La segunda búsqueda cubre `juez run sol casos` en Linux, donde `which` no mira el directorio actual.
    ejecutable = shutil.which(ruta) or shutil.which(str(Path(ruta).resolve()))
    if ejecutable is None: sys.exit(f'juez: no encuentro el ejecutable {ruta}')
    return [str(Path(ejecutable).resolve())]


def buscar_casos(carpeta: Path) -> list[tuple[Path, Path]]:
    entradas = sorted(carpeta.glob('*.in'))
    sin_salida = [entrada.name for entrada in entradas if not entrada.with_suffix('.out').is_file()]

    if not entradas: sys.exit(f'juez: no hay archivos .in en {carpeta}')
    if sin_salida: sys.exit(f'juez: falta el .out de {", ".join(sin_salida)}')
    return [(entrada, entrada.with_suffix('.out')) for entrada in entradas]


def cmd_run(args: argparse.Namespace) -> int:
    cmd = comando(args.ejecutable)
    casos = buscar_casos(Path(args.carpeta_casos))
    limites = Limites(args.tiempo, args.memoria)
    ancho = max(len(entrada.stem) for entrada, _ in casos)
    aceptados = 0
    print(f'=== {Path(args.ejecutable).name}: {len(casos)} casos | {limites.tiempo_s:g} s | {limites.memoria_mb} MB ===')
    import os
    if args.trabajos > (os.cpu_count() or 1): print('juez: aviso: -j supera el número de núcleos; los tiempos medidos pueden crecer', file=sys.stderr)
    from concurrent.futures import ProcessPoolExecutor
    from contextlib import nullcontext
    # Procesos y no hilos: cada trabajador lanza sus programas desde un proceso de un solo hilo, que es lo que exige preexec_fn en Linux.
    # El tope de 61 es el máximo de trabajadores que admite ProcessPoolExecutor en Windows.
    with ProcessPoolExecutor(min(args.trabajos, len(casos), 61)) if args.trabajos > 1 else nullcontext() as pool:
        mapear = pool.map if pool else map
        from .juzgar import juzgar_caso
        # Los informes llegan en el orden de los casos, aunque terminen en otro.
        for informe in mapear(juzgar_caso, repeat(cmd), *zip(*casos), repeat(limites)):
            print(f'{informe.nombre:<{ancho}} | {informe.veredicto:<3} | {informe.cpu_s:7.3f} s | {informe.memoria_kb / 1024:7.1f} MB')
            if informe.detalle: print('    ' + informe.detalle.replace('\n', '\n    '))
            aceptados += informe.veredicto == 'AC'
    print(f'=== {aceptados}/{len(casos)} AC ===')
    return 0 if aceptados == len(casos) else 1


def cmd_stress(args: argparse.Namespace) -> int:
    import subprocess
    try:
        from .stress import stress
        return stress(comando(args.solucion), comando(args.fuerza_bruta), comando(args.generador), Limites(args.tiempo, args.memoria),
                      args.semilla, args.iteraciones, args.tam, Path(args.salida))
    except subprocess.CalledProcessError as error:
        sys.exit(f'juez: {error.cmd[0]} terminó con código {error.returncode}; el generador y la fuerza bruta no pueden fallar')


def main(argv: list[str] | None = None) -> int:
    # Al redirigir la salida en Windows, la codificación por defecto no es UTF-8 y los acentos salen mal.
    for flujo in (sys.stdout, sys.stderr):
        if not flujo.isatty(): flujo.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(prog='juez', description='Juez local para programación competitiva.')
    ordenes = parser.add_subparsers(dest='orden', required=True)
    limites = argparse.ArgumentParser(add_help=False) # Opciones que comparten todas las órdenes.
    limites.add_argument('-t', '--tiempo', type=float, default=1.0, metavar='S', help='límite de tiempo de CPU por caso, en segundos (por defecto, 1)')
    limites.add_argument('-m', '--memoria', type=int, default=256, metavar='MB', help='límite de memoria por caso, en MB (por defecto, 256)')
    run = ordenes.add_parser('run', parents=[limites], help='ejecuta un programa contra los casos de una carpeta')
    run.add_argument('ejecutable', help='programa a juzgar: un ejecutable o un .py')
    run.add_argument('carpeta_casos', help='carpeta con parejas nombre.in y nombre.out')
    run.add_argument('-j', '--trabajos', type=int, default=1, metavar='N', help='casos que se ejecutan a la vez (por defecto, 1)')
    run.set_defaults(funcion=cmd_run)
    estres = ordenes.add_parser('stress', parents=[limites], help='compara una solución con una fuerza bruta sobre entradas aleatorias')
    estres.add_argument('solucion', help='programa que se quiere comprobar')
    estres.add_argument('fuerza_bruta', help='programa lento pero correcto; su salida se toma como la esperada')
    estres.add_argument('generador', help='programa que recibe <semilla> <tamaño> y escribe una entrada')
    estres.add_argument('-n', '--iteraciones', type=int, default=200, metavar='N', help='entradas que se prueban como máximo (por defecto, 200)')
    estres.add_argument('--tam', type=int, default=10, metavar='T', help='tamaño que se pide al generador (por defecto, 10)')
    estres.add_argument('--semilla', type=int, default=1, metavar='S', help='primera semilla; las siguientes son consecutivas (por defecto, 1)')
    estres.add_argument('-o', '--salida', default='fallo', metavar='DIR', help='carpeta donde se guarda el caso que falla (por defecto, fallo)')
    estres.set_defaults(funcion=cmd_stress)
    args = parser.parse_args(argv)
    if args.tiempo <= 0 or args.memoria <= 0: parser.error('los límites de tiempo y memoria deben ser positivos')
    if getattr(args, 'trabajos', 1) < 1: parser.error('-j debe ser al menos 1')
    return args.funcion(args)
