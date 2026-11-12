"""Tipos que comparten todas las implementaciones de la capa de plataforma."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Limites:
    tiempo_s: float = 1.0 # Tiempo de CPU, no de reloj.
    memoria_mb: int = 256


@dataclass(frozen=True)
class Resultado:
    codigo: int # Código de salida; en Linux, negativo si lo mató una señal.
    cpu_s: float # Tiempo de CPU consumido (usuario + núcleo).
    memoria_kb: int # Pico de memoria.
    tle: bool
    mle: bool
