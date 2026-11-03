# Metaheurísticas para el Problema del Ciclo Hamiltoniano (FHCP) — BORRADOR

Código fuente ejecutable de la práctica *Aula invertida — Algoritmos heurísticos*.
Carga grafos en formato HCP, ejecuta seis metaheurísticas y devuelve un arreglo de
vértices (formato TOUR) que constituye la solución propuesta.

## Requisitos

- Python 3.10 o superior
- `pip install numpy scipy pandas matplotlib elkai`
  (`elkai` es opcional: solo se usa para la referencia LKH)

## Estructura

```
hcp/
  core.py          Grafo, función de evaluación c(π), movimientos con evaluación incremental,
                   construcción voraz (Warnsdorff), métricas precisión / recall / F1
  io.py            Lectura de .hcp y lectura/escritura de .tour (formato del FHCP)
  generators.py    Instancias de prueba: envelope, Petersen generalizado GP(n,2), grafos plantados
  algorithms/
    ga.py          Algoritmo Genético (base de control): torneo, OX/ERX, inversión, elitismo
    sa.py          Recocido Simulado: swaps + 2-opt, Metropolis, enfriamiento geométrico lento
    aco.py         Colonia de Hormigas (MAX-MIN Ant System) con heurística de Warnsdorff
    abc.py         Colonia Artificial de Abejas (empleadas, observadoras, exploradoras)
    de.py          Evolución Diferencial DE/rand/1/bin con claves aleatorias
    pso.py         Enjambre de Partículas con claves aleatorias (regla SPV)
    lkh_ref.py     Referencia externa: LKH (vía elkai), reducción HCP -> TSP 0/1
run_experiments.py Corre los algoritmos sobre una carpeta de .hcp (en paralelo) -> CSV
analyze.py         Tablas resumen, pruebas de Friedman/Wilcoxon y figuras
instances/         Instancias del borrador (+ sols/ con ciclos de referencia)
results/           Resultados del borrador
```

## Uso rápido

```bash
# Instancias del borrador
python run_experiments.py --generate-suite instances

# Experimento completo (5 semillas, 10 s por corrida)
python run_experiments.py --instances instances --runs 5 --time 10 --out results
python analyze.py --results results

# Un solo algoritmo sobre un archivo
python -c "from hcp.io import read_hcp, write_tour; from hcp.algorithms import sa; \
g = read_hcp('instances/GP_33_2.hcp'); r = sa.solve(g, time_limit=10, seed=1); \
print(r['mejor_costo']); write_tour('sol.tour', g.name, r['perm'])"
```

## Correr sobre el FHCP Challenge Set real

1. Descargar `FHCPCS.7z` y `FHCPCS_sols.7z` de
   <https://sites.flinders.edu.au/flinders-hamiltonian-cycle-project/fhcp-challenge-set/>
2. Descomprimir los grafos en `fhcp/` y las soluciones en `fhcp_sols/`
   (las soluciones deben llamarse igual que el grafo, con extensión `.tour`).
3. Ejecutar, empezando por las instancias más pequeñas:

```bash
python run_experiments.py --instances fhcp --solutions fhcp_sols --max-n 1000 --runs 5 --time 30 --out results_fhcp
python analyze.py --results results_fhcp
```

## Notas del borrador

- La función de evaluación común es c(π) = número de pares consecutivos (con cierre) que no son
  aristas del grafo; c(π) = 0 si y solo si π es un ciclo hamiltoniano.
- Toda solución reportada como éxito se valida con `is_hamiltonian` (n vértices distintos y
  n aristas existentes) antes de escribir el archivo `.tour`.
- Los tiempos dependen de la máquina; el borrador se ejecutó con 2 núcleos.
