# juez

[![tests](https://github.com/xilin01/Juez-Local/actions/workflows/tests.yml/badge.svg)](https://github.com/xilin01/Juez-Local/actions/workflows/tests.yml)

Juez local para programación competitiva. Ejecuta una solución contra casos de prueba y da un veredicto por caso (AC, WA, TLE, MLE, RTE) con el tiempo de CPU y la memoria máxima. También compara una solución con una fuerza bruta sobre entradas aleatorias hasta encontrar un contraejemplo.

Funciona en Windows y en Linux. Está escrito en Python sin dependencias externas.

## Instalación

Hace falta Python 3.10 o posterior.

```
git clone https://github.com/xilin01/Juez-Local.git
cd Juez-Local
python -m pip install -e .
```

Esto instala el comando `juez`. Sin instalar nada también se puede usar desde la carpeta del proyecto con `python -m juez`.

Para ejecutar los tests hacen falta `pytest` y `g++` en el PATH:

```
python -m pip install -e ".[test]"
python -m pytest
```

## Uso

### `juez run`

```
juez run <ejecutable> <carpeta_casos> [-t S] [-m MB] [-j N]
```

Ejecuta el programa con cada `nombre.in` de la carpeta y compara su salida con `nombre.out`.

| Opción | Significado | Por defecto |
|---|---|---|
| `-t`, `--tiempo` | Límite de tiempo de CPU por caso, en segundos. | 1 |
| `-m`, `--memoria` | Límite de memoria por caso, en MB. | 256 |
| `-j`, `--trabajos` | Casos que se ejecutan a la vez. | 1 |

El programa puede ser un ejecutable o un `.py`, que se lanza con el mismo Python que ejecuta `juez`.

Veredictos:

| Veredicto | Significado |
|---|---|
| AC | La salida coincide con la esperada. Se ignoran los espacios al final de cada línea y las líneas vacías al final. |
| WA | La salida no coincide. Se muestran las líneas que rodean a la primera diferencia. |
| TLE | Superó el tiempo de CPU, o estuvo esperando sin gastar CPU más de `2 × tiempo + 1` segundos. |
| MLE | Intentó usar más memoria de la permitida. |
| RTE | Terminó con un código de salida distinto de 0 o lo mató una señal. |

`juez run` termina con código 0 si todos los casos son AC y con 1 si no.

### `juez stress`

```
juez stress <solucion> <fuerza_bruta> <generador> [-n N] [--tam T] [--semilla S] [-o DIR] [-t S] [-m MB]
```

1. Llama al generador como `generador <semilla> <tamaño>` y toma su salida como entrada del problema.
2. Ejecuta la fuerza bruta y toma su salida como la esperada.
3. Juzga la solución con esa entrada. Si el veredicto no es AC, se detiene.
4. Intenta reducir el contraejemplo: prueba tamaños menores (1, 2, 4...) con 20 semillas cada uno y se queda con el menor que falle.
5. Guarda el caso en `DIR/caso.in` y `DIR/caso.out`.

| Opción | Significado | Por defecto |
|---|---|---|
| `-n`, `--iteraciones` | Entradas que se prueban como máximo. | 200 |
| `--tam` | Tamaño que se pide al generador. | 10 |
| `--semilla` | Primera semilla; las siguientes son consecutivas. | 1 |
| `-o`, `--salida` | Carpeta donde se guarda el caso que falla. | `fallo` |

El generador debe ser determinista: la misma semilla y el mismo tamaño dan siempre la misma entrada. Qué significa «tamaño» lo decide el generador; basta con que un tamaño menor produzca entradas más pequeñas.

La carpeta de salida es una carpeta de casos válida, así que `juez run solucion fallo` repite el contraejemplo.

`juez stress` termina con código 1 si encuentra un contraejemplo y con 0 si no.

## Ejemplo

La carpeta `ejemplos/` contiene un problema (`enunciado.md`), cinco soluciones, un generador y cinco casos. Para compilarlas en Windows con MinGW:

```
g++ -O2 -static -o correcta.exe ejemplos/correcta.cpp
g++ -O2 -static -o incorrecta.exe ejemplos/incorrecta.cpp
g++ -O2 -static -o lenta.exe ejemplos/lenta.cpp
g++ -O2 -static -o memoria.exe ejemplos/memoria.cpp
g++ -O2 -static -o revienta.exe ejemplos/revienta.cpp
```

En Linux sobra `-static` y el `.exe`, y los programas se indican con su ruta (`./correcta`).

Salida real en Windows 11:

```
> juez run incorrecta.exe ejemplos/casos
=== incorrecta.exe: 5 casos | 1 s | 256 MB ===
01-enunciado   | AC  |   0.000 s |     0.9 MB
02-negativos   | WA  |   0.016 s |     0.9 MB
    Primera diferencia en la línea 1 (- esperado, + obtenido):
    --2
    +0
03-un-elemento | AC  |   0.000 s |     0.8 MB
04-mediano     | AC  |   0.000 s |     0.9 MB
05-grande      | AC  |   0.016 s |     0.9 MB
=== 4/5 AC ===

> juez run lenta.exe ejemplos/casos -j 4
=== lenta.exe: 5 casos | 1 s | 256 MB ===
01-enunciado   | AC  |   0.016 s |     0.9 MB
02-negativos   | AC  |   0.016 s |     0.9 MB
03-un-elemento | AC  |   0.016 s |     0.9 MB
04-mediano     | AC  |   0.047 s |     0.9 MB
05-grande      | TLE |   1.000 s |     0.9 MB
=== 4/5 AC ===

> juez run memoria.exe ejemplos/casos
=== memoria.exe: 5 casos | 1 s | 256 MB ===
01-enunciado   | AC  |   0.016 s |     0.9 MB
02-negativos   | AC  |   0.000 s |     0.9 MB
03-un-elemento | AC  |   0.000 s |     0.9 MB
04-mediano     | AC  |   0.000 s |     9.3 MB
05-grande      | MLE |   0.109 s |   256.1 MB
=== 4/5 AC ===

> juez run revienta.exe ejemplos/casos
=== revienta.exe: 5 casos | 1 s | 256 MB ===
01-enunciado   | RTE |   0.016 s |     0.9 MB
    código de salida 0xc0000409
...
=== 0/5 AC ===

> juez stress incorrecta.exe lenta.exe ejemplos/gen.py
[stress] Discrepancia con semilla 2 y tamaño 10. Buscando un caso menor...
[stress] WA con semilla 2 y tamaño 1.
    Primera diferencia en la línea 1 (- esperado, + obtenido):
    --1
    +0
[stress] Caso guardado en fallo\caso.in y fallo\caso.out.
```

En la línea `--2`, el primer `-` marca «esperado» y `-2` es el contenido.

## Cómo se aplican los límites

| | Windows | Linux |
|---|---|---|
| Mecanismo | Un Job Object por ejecución | `setrlimit` en el proceso hijo |
| Tiempo | Se consulta la CPU del job cada 10 ms | `RLIMIT_CPU` y tiempo de `wait4` |
| Memoria que se limita | Memoria comprometida (commit) | Espacio de direcciones (`RLIMIT_AS`) |
| Memoria que se muestra | Pico de memoria comprometida | Pico de memoria residente (`ru_maxrss`) |
| Detección de MLE | Aviso del propio job | Fin anormal y `bad_alloc` o `MemoryError` en stderr |

Todo el código que depende del sistema está en `juez/plataforma/`. El resto solo usa la función `ejecutar(cmd, entrada, salida, limites)`.

## Limitaciones conocidas

**Generales**

- Solo Windows y Linux. En macOS no se ha probado y el límite de memoria no funcionaría.
- No es un entorno aislado. El programa juzgado puede leer y escribir archivos y usar la red como cualquier otro programa. Úsalo solo con código de confianza.
- La comparación es exacta salvo por los espacios finales. No hay comparación de decimales con tolerancia ni comprobadores para problemas con varias respuestas válidas.
- No hay límite de tamaño de salida. Un programa que escribe sin parar llena el disco hasta que salta el TLE.
- Lo que el programa escribe en stderr no se muestra.
- El tamaño de pila es el del sistema: 1 MB por defecto en un ejecutable de Windows y 8 MB en Linux. Una recursión profunda aparece como RTE.
- Con `-j` mayor que el número de núcleos, los programas compiten entre sí y el tiempo de CPU medido crece. `juez` avisa, pero no lo impide.

**Memoria**

- La memoria no significa lo mismo en los dos sistemas (ver la tabla anterior). Un programa que reserva mucha memoria y no la toca cuenta en Windows y apenas se ve en Linux.
- En Linux ningún programa aparece con menos de unos 12 MB: `ru_maxrss` incluye el instante en que el proceso hijo todavía es una copia del propio juez.
- En Linux el MLE es una deducción. Un programa en C que no comprueba el resultado de `malloc` y falla con una violación de segmento recibe RTE.
- En Windows, cuando una reserva falla, la memoria mostrada incluye el intento: un programa que pide 4 GB de golpe aparece con 4 GB.

**Tiempo**

- En Windows el tiempo de CPU avanza en pasos de unos 16 ms, y un programa puede pasarse del límite hasta ese margen antes de que se le corte.
- En Linux `RLIMIT_CPU` solo admite segundos enteros. Con `-t 0.5`, un programa que gasta 0,8 s llega a terminar, aunque recibe TLE.

**`stress`**

- El caso reducido es el menor que se encuentra con 20 semillas por tamaño, no necesariamente el mínimo.
- El generador y la fuerza bruta se ejecutan sin límites.
- En Windows con Python 3.10 o 3.11 hay que escribir la extensión `.exe` de los programas.

## Licencia

MIT. Ver [LICENSE](LICENSE).
