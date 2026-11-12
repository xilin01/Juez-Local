"""Interfaz de línea de comandos."""
import argparse
import shutil
import sys
from pathlib import Path
from .juzgar import juzgar_caso
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
    for entrada, esperada in casos:
        informe = juzgar_caso(cmd, entrada, esperada, limites)
        print(f'{informe.nombre:<{ancho}} | {informe.veredicto:<3} | {informe.cpu_s:7.3f} s | {informe.memoria_kb / 1024:7.1f} MB')
        if informe.detalle: print('    ' + informe.detalle.replace('\n', '\n    '))
        aceptados += informe.veredicto == 'AC'
    print(f'=== {aceptados}/{len(casos)} AC ===')
    return 0 if aceptados == len(casos) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='juez', description='Juez local para programación competitiva.')
    ordenes = parser.add_subparsers(dest='orden', required=True)
    limites = argparse.ArgumentParser(add_help=False) # Opciones que comparten todas las órdenes.
    limites.add_argument('-t', '--tiempo', type=float, default=1.0, metavar='S', help='límite de tiempo de CPU por caso, en segundos (por defecto, 1)')
    limites.add_argument('-m', '--memoria', type=int, default=256, metavar='MB', help='límite de memoria por caso, en MB (por defecto, 256)')
    run = ordenes.add_parser('run', parents=[limites], help='ejecuta un programa contra los casos de una carpeta')
    run.add_argument('ejecutable', help='programa a juzgar: un ejecutable o un .py')
    run.add_argument('carpeta_casos', help='carpeta con parejas nombre.in y nombre.out')
    run.set_defaults(funcion=cmd_run)
    args = parser.parse_args(argv)
    if args.tiempo <= 0 or args.memoria <= 0: parser.error('los límites de tiempo y memoria deben ser positivos')
    return args.funcion(args)
