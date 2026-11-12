"""Generador para `juez stress`: `gen.py <semilla> <tamaño>` escribe una entrada con n <= tamaño y valores entre -tamaño y tamaño."""
import random
import sys


if __name__ == '__main__':
    semilla, tam = int(sys.argv[1]), int(sys.argv[2])
    rng = random.Random(semilla)
    n = rng.randint(1, tam)
    print(n)
    print(*(rng.randint(-tam, tam) for _ in range(n)))
