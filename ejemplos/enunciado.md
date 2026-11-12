# Subarray de suma máxima

Dada una secuencia de `n` enteros, calcula la mayor suma que puede obtenerse con un tramo contiguo y no vacío de la secuencia.

**Entrada.** Una línea con `n` (1 ≤ n ≤ 10 000) y otra con `n` enteros entre −10⁹ y 10⁹.

**Salida.** Una línea con la suma máxima.

**Límites.** 1 segundo y 256 MB.

| Entrada | Salida |
|---|---|
| `9`<br>`-2 1 -3 4 -1 2 1 -5 4` | `6` |

## Soluciones

| Archivo | Qué hace | Veredicto esperado |
|---|---|---|
| `correcta.cpp` | Algoritmo de Kadane, O(n). | AC en todos los casos |
| `incorrecta.cpp` | Kadane que empieza en 0: falla si todos los números son negativos. | WA en el caso 02 |
| `lenta.cpp` | Prueba todos los tramos sumando cada uno desde cero, O(n³). | TLE en el caso 05 |
| `memoria.cpp` | Guarda en una tabla la suma de todos los tramos, O(n²) de memoria. | MLE en el caso 05 |
| `revienta.cpp` | Recorre el vector una posición de más. | RTE en todos los casos |

`gen.py <semilla> <tamaño>` genera entradas aleatorias para `juez stress`: `n` entre 1 y `tamaño`, y valores entre `-tamaño` y `tamaño`.
