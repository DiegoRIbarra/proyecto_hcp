"""Núcleo del proyecto: representación del grafo, función de evaluación y utilidades.

Convenciones
------------
* Los vértices se numeran internamente desde 0 (en los archivos HCP/TOUR van desde 1).
* Una solución es una permutación `perm` de los n vértices (representación de camino).
* El costo c(perm) es el número de pares consecutivos (incluido el cierre) que NO son
  aristas del grafo. perm es un ciclo hamiltoniano  <=>  c(perm) == 0.
"""
from __future__ import annotations

import random
import numpy as np


class Graph:
    """Grafo simple no dirigido con lista de adyacencia y, si cabe en memoria, matriz booleana."""

    MATRIX_LIMIT = 12000  # n máximo para usar matriz de adyacencia (n^2 bytes)

    def __init__(self, n: int, edges, name: str = "grafo"):
        self.n = n
        self.name = name
        self.adj = [set() for _ in range(n)]
        for u, v in edges:
            if u == v:
                continue
            self.adj[u].add(v)
            self.adj[v].add(u)
        self.adj_list = [sorted(s) for s in self.adj]
        self.m = sum(len(s) for s in self.adj) // 2
        self.deg = np.array([len(s) for s in self.adj], dtype=np.int64)
        self.A = None
        if n <= self.MATRIX_LIMIT:
            self.A = np.zeros((n, n), dtype=np.bool_)
            for u in range(n):
                for v in self.adj[u]:
                    self.A[u, v] = True

    # ------------------------------------------------------------------ consultas
    def has_edge(self, u: int, v: int) -> bool:
        if self.A is not None:
            return bool(self.A[u, v])
        return v in self.adj[u]

    def edges(self):
        for u in range(self.n):
            for v in self.adj[u]:
                if u < v:
                    yield (u, v)

    def stats(self) -> dict:
        return {
            "n": self.n,
            "m": self.m,
            "grado_min": int(self.deg.min()),
            "grado_max": int(self.deg.max()),
            "grado_prom": round(2 * self.m / self.n, 3),
        }


# ---------------------------------------------------------------------- evaluación
def cost(g: Graph, perm) -> int:
    """Aristas faltantes de la permutación (0 = ciclo hamiltoniano). O(n)."""
    p = np.asarray(perm)
    q = np.roll(p, -1)
    if g.A is not None:
        return int(g.n - g.A[p, q].sum())
    return sum(1 for a, b in zip(p, q) if b not in g.adj[a])


def fitness(g: Graph, perm) -> int:
    """Aristas existentes del recorrido (a maximizar, máximo n)."""
    return g.n - cost(g, perm)


def miss(g: Graph, u: int, v: int) -> int:
    """1 si {u, v} NO es arista del grafo, 0 si sí lo es."""
    return 0 if g.has_edge(u, v) else 1


def delta_inversion(g: Graph, p, i: int, j: int) -> int:
    """Cambio de costo al invertir el segmento p[i..j] (0 <= i < j < n), movimiento 2-opt.

    Se eliminan las aristas (p[i-1], p[i]) y (p[j], p[j+1]) y se agregan
    (p[i-1], p[j]) y (p[i], p[j+1]). Evaluación incremental O(1).
    """
    n = len(p)
    if i == 0 and j == n - 1:
        return 0  # invertir todo el ciclo no cambia nada
    a, b = p[i - 1], p[i]
    c, d = p[j], p[(j + 1) % n]
    return (miss(g, a, c) + miss(g, b, d)) - (miss(g, a, b) + miss(g, c, d))


def apply_inversion(p, i: int, j: int) -> None:
    p[i:j + 1] = p[i:j + 1][::-1]


def delta_swap(g: Graph, p, i: int, j: int) -> int:
    """Cambio de costo al intercambiar p[i] y p[j]. Evaluación incremental O(1)."""
    n = len(p)
    if i == j:
        return 0
    idx = {(i - 1) % n, i, (j - 1) % n, j}  # índice k representa el par (p[k], p[k+1])
    before = sum(miss(g, p[k], p[(k + 1) % n]) for k in idx)
    p[i], p[j] = p[j], p[i]
    after = sum(miss(g, p[k], p[(k + 1) % n]) for k in idx)
    p[i], p[j] = p[j], p[i]
    return after - before


def is_hamiltonian(g: Graph, perm) -> bool:
    """Validación de la salida: n vértices distintos y n aristas existentes."""
    return len(perm) == g.n and len(set(int(x) for x in perm)) == g.n and cost(g, perm) == 0


def random_keys_decode(keys) -> np.ndarray:
    """Decodificador de claves aleatorias: ordena los vértices por su clave."""
    return np.argsort(keys, kind="stable")


# --------------------------------------------------------------- inicialización
def greedy_walk(g: Graph, rng: random.Random) -> list:
    """Construcción voraz con la regla de Warnsdorff y desempates aleatorios.

    Desde un vértice al azar, avanza al vecino no visitado con menos vecinos no
    visitados. Si se bloquea, salta a un vértice no visitado al azar (eso genera
    una arista faltante que la metaheurística deberá reparar).
    """
    n = g.n
    visited = bytearray(n)
    free_deg = [len(s) for s in g.adj]
    unvisited = list(range(n))
    pos = list(range(n))  # posición de cada vértice en `unvisited` (borrado O(1))

    def mark(v):
        visited[v] = 1
        k = pos[v]
        last = unvisited[-1]
        unvisited[k] = last
        pos[last] = k
        unvisited.pop()
        for w in g.adj_list[v]:
            free_deg[w] -= 1

    cur = rng.randrange(n)
    tour = [cur]
    mark(cur)
    while unvisited:
        cand = [w for w in g.adj_list[cur] if not visited[w]]
        if cand:
            best = min(free_deg[w] for w in cand)
            cur = rng.choice([w for w in cand if free_deg[w] == best])
        else:
            cur = unvisited[rng.randrange(len(unvisited))]
        tour.append(cur)
        mark(cur)
    return tour


def random_perm(g: Graph, rng: random.Random) -> list:
    p = list(range(g.n))
    rng.shuffle(p)
    return p


def initial_solution(g: Graph, rng: random.Random, mode: str = "greedy") -> list:
    return greedy_walk(g, rng) if mode == "greedy" else random_perm(g, rng)


# ----------------------------------------------------------------- métricas IA
def edge_metrics(g: Graph, perm, reference=None) -> dict:
    """Métricas estadísticas adaptadas al HCP (ver reporte, sección de métricas).

    Se trata cada par consecutivo del recorrido como una 'predicción de arista del ciclo'.
    * precision = pares del recorrido que son aristas reales del grafo / n
    * recall y F1 (solo si hay un ciclo de referencia conocido): fracción de las n aristas
      del ciclo de referencia que el recorrido recupera.
    """
    n = g.n
    p = [int(x) for x in perm]
    pairs = {frozenset((p[k], p[(k + 1) % n])) for k in range(n)}
    valid = sum(1 for e in pairs if g.has_edge(*tuple(e)))
    out = {"precision": valid / n}
    if reference is not None:
        r = [int(x) for x in reference]
        ref = {frozenset((r[k], r[(k + 1) % n])) for k in range(n)}
        tp = len(pairs & ref)
        prec_ref = tp / n
        rec = tp / n
        out["recall_ref"] = rec
        out["precision_ref"] = prec_ref
        out["f1_ref"] = 0.0 if tp == 0 else 2 * prec_ref * rec / (prec_ref + rec)
    return out
