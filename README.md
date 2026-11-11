# Metaheurísticas para el Problema del Ciclo Hamiltoniano

Implementación experimental para resolver el **Problema del Ciclo Hamiltoniano
(HCP/FHCP)** mediante metaheurísticas de búsqueda y optimización combinatoria.
El proyecto carga grafos en formato HCP, construye permutaciones de vértices,
evalúa qué tan cerca están de formar un ciclo hamiltoniano y guarda los resultados
en CSV, JSON, imágenes y archivos TOUR.

El repositorio incluye el **FHCP Challenge Set real**, con 1001 grafos y sus 1001
soluciones de referencia.

---

## 1. Problema que se resuelve

Dado un grafo no dirigido \(G=(V,E)\), se busca una permutación:

```text
π = [v1, v2, ..., vn]
```

tal que todos los vértices aparezcan exactamente una vez y también existan las
aristas:

```text
(v1, v2), (v2, v3), ..., (v(n-1), vn), (vn, v1)
```

La función objetivo utilizada por todos los algoritmos es:

```text
c(π) = número de pares consecutivos del ciclo que no son aristas de G
```

- `c(π) = 0`: se encontró un ciclo hamiltoniano válido.
- `c(π) > 0`: la permutación todavía contiene aristas faltantes.
- El objetivo de todos los algoritmos es **minimizar** `c(π)`.

La solución se representa internamente con vértices numerados desde `0`. Los
archivos HCP y TOUR utilizan la numeración estándar desde `1`.

---

## 2. Requisitos e instalación

Se requiere Python 3.10 o superior.

```bash
python -m pip install numpy scipy pandas matplotlib
```

`elkai` es opcional y solo se necesita para ejecutar el algoritmo de referencia
LKH:

```bash
python -m pip install elkai
```

Si `elkai` no está instalado, se pueden ejecutar normalmente GA, SA, ACO, ABC,
DE y PSO.

---

## 3. Ejecución

Todos los comandos se ejecutan desde la raíz del proyecto.

### 3.1 Generar instancias pequeñas de prueba

Este comando crea una suite local con:

- El grafo `envelope`.
- Grafos de Petersen generalizados `GP(n,2)`.
- Grafos aleatorios con un ciclo hamiltoniano plantado.

```bash
python run_experiments.py --generate-suite instances
```

### 3.2 Ejecutar un experimento

El siguiente ejemplo ejecuta los seis algoritmos principales, con cinco semillas
por instancia y diez segundos por corrida:

```powershell
python run_experiments.py --instances instances --algos GA,SA,ACO,ABC,DE,PSO --runs 5 --time 10 --out results
```

Parámetros importantes:

| Opción | Descripción |
|---|---|
| `--instances` | Carpeta que contiene los archivos `.hcp`. |
| `--solutions` | Carpeta con soluciones de referencia `.tou` o `.tour`. |
| `--algos` | Algoritmos separados por comas. |
| `--runs` | Número de semillas por algoritmo. |
| `--time` | Tiempo máximo en segundos por corrida. |
| `--max-n` | Ignora grafos con más de `n` vértices. |
| `--workers` | Número de procesos paralelos. |
| `--out` | Carpeta de salida. |

El programa detiene una corrida cuando:

1. encuentra un ciclo hamiltoniano (`c(π) = 0`);
2. alcanza el tiempo límite.

Los algoritmos también aceptan un límite de evaluaciones cuando se invocan
directamente desde Python mediante el parámetro `max_evals`.

### 3.3 Ejecutar el dataset FHCP real

El dataset incluido tiene esta estructura:

```text
fhcp/
  graph1.hcp
  graph2.hcp
  ...
fhcp_sols/
  graph1.hcp.tou
  graph2.hcp.tou
  ...
```

Para comenzar con las 171 instancias que tienen como máximo 1000 vértices:

```powershell
python run_experiments.py --instances fhcp --solutions fhcp_sols --max-n 1000 --algos GA,SA,ACO,ABC,DE,PSO --runs 5 --time 30 --out results_fhcp
```

El conjunto completo contiene 1001 grafos y llega hasta 9528 vértices, por lo
que requiere más memoria, tiempo y espacio para guardar resultados.

Para incluir también la referencia LKH:

```bash
python run_experiments.py --instances fhcp --solutions fhcp_sols --max-n 1000 --algos GA,SA,ACO,ABC,DE,PSO,LKH --runs 5 --time 30 --out results_fhcp
```

LKH utiliza una sola semilla por instancia y no depende del parámetro `--time`
de la misma forma que las metaheurísticas internas.

### 3.4 Analizar los resultados

Después de ejecutar un experimento:

```bash
python analyze.py --results results_fhcp
```

Se generan:

```text
resultados.csv
historias.json
resumen_instancia_algoritmo.csv
resumen_algoritmos.csv
estadistica.json
figuras/
  tasa_exito.png
  costo_promedio.png
  convergencia_*.png
```

El análisis calcula tasas de éxito, costos medios, precisión, tiempo promedio,
ranking por instancia, prueba de Friedman y comparaciones pareadas de
Wilcoxon con corrección de Holm.

### 3.5 Ejecutar un algoritmo sobre un solo grafo

```bash
python -c "from hcp.io import read_hcp, write_tour; from hcp.algorithms import sa; g = read_hcp('instances/GP_33_2.hcp'); r = sa.solve(g, time_limit=10, seed=1); print(r['mejor_costo']); write_tour('sol.tour', g.name, r['perm'])"
```

---

## 4. Arquitectura del proyecto

```text
hcp/
  core.py
  io.py
  generators.py
  algorithms/
    base.py
    moves.py
    ga.py
    sa.py
    aco.py
    abc.py
    de.py
    pso.py
    lkh_ref.py

run_experiments.py
analyze.py
instances/
fhcp/
fhcp_sols/
results/
```

### `hcp/core.py`

Contiene la representación `Graph`, las listas de adyacencia, la matriz booleana
cuando el tamaño lo permite, la función objetivo `cost`, la validación
`is_hamiltonian`, la construcción inicial de Warnsdorff y las métricas de
aristas.

Para grafos de hasta 12000 vértices se mantiene una matriz booleana de
adyacencia. En grafos mayores se utilizan listas de adyacencia para reducir el
consumo de memoria.

### `hcp/io.py`

Lee archivos `.hcp` y soluciones `.tou`/`.tour`, y escribe archivos HCP y TOUR.
La lectura acepta el formato del FHCP Challenge Set, incluyendo soluciones con
nombres como `graph1.hcp.tou`.

### `hcp/algorithms/base.py`

Define `Tracker`, el componente común que:

- registra la mejor permutación;
- cuenta evaluaciones e iteraciones;
- guarda la historia de convergencia;
- mide el tiempo hasta la mejor solución;
- aplica los criterios de parada.

### `hcp/algorithms/moves.py`

Implementa movimientos sobre permutaciones, como `swap`, inversión `2-opt` e
inversión guiada por la estructura del grafo. Las variaciones calculan el cambio
de costo incrementalmente cuando es posible.

### `run_experiments.py`

Orquesta el experimento completo:

1. descubre los archivos `.hcp`;
2. filtra por tamaño;
3. crea una corrida por combinación de instancia, algoritmo y semilla;
4. ejecuta las corridas en paralelo;
5. valida cada solución;
6. compara contra la referencia si está disponible;
7. guarda CSV, JSON e históricos.

### `analyze.py`

Consume `resultados.csv` e `historias.json` y genera tablas, estadísticas y
figuras comparativas. Puede analizar todos los algoritmos o un subconjunto.

---

## 5. Algoritmos utilizados

Todos los algoritmos trabajan sobre la misma representación: una permutación de
los `n` vértices. Esto permite comparar los métodos usando exactamente la misma
función objetivo y los mismos criterios de validación.

### 5.1 Construcción inicial: Warnsdorff

La inicialización por defecto construye un recorrido voraz:

1. elige un vértice inicial aleatorio;
2. considera vecinos no visitados;
3. selecciona preferentemente el vecino con menor cantidad de opciones libres;
4. si queda bloqueado, salta a un vértice no visitado.

La regla prioriza los vértices difíciles de visitar más adelante. Si el salto
produce una arista faltante, la metaheurística intenta repararla.

También se puede usar una permutación aleatoria como inicialización.

### 5.2 Algoritmo Genético (`GA`)

El GA mantiene una población de permutaciones y repite:

1. selección por torneo;
2. cruza `OX` (Order Crossover) o `ERX` (Edge Recombination);
3. mutación por inversión de un segmento;
4. evaluación del costo;
5. elitismo para conservar las mejores soluciones.

`OX` conserva el orden relativo de los padres y `ERX` intenta conservar sus
adyacencias. La mutación por inversión equivale a un movimiento 2-opt sobre el
recorrido.

### 5.3 Recocido Simulado (`SA`)

Parte de una permutación y explora vecinos mediante:

- intercambio de dos posiciones;
- inversión aleatoria;
- inversión guiada por aristas del grafo.

Un movimiento que mejora se acepta siempre. Uno que empeora se acepta con
probabilidad:

```text
exp(-Δ / T)
```

La temperatura se enfría geométricamente durante un ciclo. Al terminar el ciclo,
se recalienta desde la mejor solución conocida para continuar explorando.

### 5.4 Colonia de Hormigas (`ACO`)

Implementa una variante **MAX-MIN Ant System**:

1. cada hormiga construye un recorrido;
2. prioriza vecinos no visitados que tengan feromona alta;
3. usa como heurística la regla de Warnsdorff;
4. evapora feromona;
5. deposita más feromona en las mejores rutas;
6. limita la feromona entre `tau_min` y `tau_max`.

Las hormigas recorren aristas existentes siempre que sea posible. Si se bloquean,
realizan un salto y se contabiliza una arista faltante.

### 5.5 Colonia Artificial de Abejas (`ABC`)

Representa cada fuente de alimento como una permutación:

- **Abejas empleadas:** exploran un vecino de su fuente.
- **Abejas observadoras:** eligen fuentes mediante ruleta proporcional a
  `1 / (1 + c(π))`.
- **Abejas exploradoras:** reemplazan fuentes que llevan demasiados intentos sin
  mejorar.

Los vecinos se generan con swap, 2-opt e inversión guiada. La selección local es
voraz: solo se conserva un movimiento que no empeora la solución.

### 5.6 Evolución Diferencial (`DE`)

DE utiliza una representación indirecta mediante **claves aleatorias**:

```text
vector real -> ordenar claves -> permutación de vértices
```

Cada generación aplica el esquema `DE/rand/1/bin`:

```text
v = x_r1 + F (x_r2 - x_r3)
u = cruza binomial(x_i, v)
```

El vector candidato se decodifica como permutación y se conserva si no empeora
el costo del individuo actual.

### 5.7 Enjambre de Partículas (`PSO`)

PSO también utiliza claves aleatorias para representar permutaciones. Cada
partícula mantiene:

- posición actual;
- velocidad;
- mejor posición individual (`pbest`);
- mejor posición global (`gbest`).

La actualización usa inercia, componente cognitiva y componente social:

```text
v <- wv + c1 r1 (pbest - x) + c2 r2 (gbest - x)
x <- x + v
```

Después de actualizar una partícula, sus claves se ordenan para obtener la
permutación evaluable.

### 5.8 Referencia LKH (`LKH`)

`lkh_ref.py` ofrece una referencia externa mediante `elkai`. Reduce el HCP a un
TSP con pesos:

- peso `0` si la pareja de vértices es una arista del grafo;
- peso `1` si no lo es.

Así, un tour TSP de costo cero equivale a un ciclo hamiltoniano. Este método se
incluye como referencia y no como una de las seis metaheurísticas principales.

---

## 6. Validación y métricas

Una solución se marca como exitosa solo si:

1. contiene exactamente `n` vértices;
2. no repite vértices;
3. todas las aristas consecutivas, incluido el cierre, existen.

Además del costo `c(π)`, se guardan:

- **precisión:** proporción de pares del recorrido que son aristas del grafo;
- **recall de referencia:** proporción de aristas del ciclo de referencia
  recuperadas;
- **F1:** media armónica entre precisión y recall de referencia;
- tiempo total y tiempo hasta la mejor solución;
- número de evaluaciones e iteraciones;
- criterio de parada;
- parámetros de la corrida.

---

## 7. Dataset incluido

```text
instances/   Suite pequeña generada para pruebas
fhcp/        1001 grafos reales en formato .hcp
fhcp_sols/   1001 soluciones reales en formato .hcp.tou
results/     Resultados y figuras de desarrollo
```

Las soluciones de referencia se validaron contra sus grafos correspondientes:
las 1001 instancias tienen una referencia disponible y válida.

---

## 8. Licencia y procedencia

El código corresponde a la práctica académica *Aula invertida — Algoritmos
heurísticos*. El conjunto de datos FHCP Challenge Set se conserva en los
directorios `fhcp/` y `fhcp_sols/` con el formato distribuido por el proyecto
FHCP.
