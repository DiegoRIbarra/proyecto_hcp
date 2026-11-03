"""Generadores de instancias de prueba.

* `envelope()`: grafo de ejemplo del sitio del FHCP (6 vértices, 9 aristas).
* `generalized_petersen(n, k)`: GP(n, k). El FHCP Challenge Set incluye GP(n, 2) con
  n = 3 (mod 6), que tienen exactamente tres ciclos hamiltonianos (Haythorpe, 2018).
* `planted_hamiltonian(n, extra_deg, seed)`: grafo disperso aleatorio con un ciclo
  hamiltoniano "plantado" (oculto por una relabelación aleatoria) más aristas extra.
"""
from __future__ import annotations

import random
from .core import Graph


def envelope() -> Graph:
    e = [(1, 2), (1, 4), (1, 5), (2, 3), (2, 6), (3, 4), (3, 6), (4, 5), (5, 6)]
    return Graph(6, [(u - 1, v - 1) for u, v in e], name="envelope")


def generalized_petersen(n: int, k: int, seed: int | None = 0) -> Graph:
    """GP(n, k): ciclo exterior u_i, estrella interior v_i -> v_{i+k}, radios u_i - v_i.

    Las etiquetas se permutan al azar (con `seed`) para que el orden de los vértices
    no revele la estructura, como ocurre en las instancias del FHCP.
    """
    edges = []
    for i in range(n):
        edges.append((i, (i + 1) % n))          # ciclo exterior
        edges.append((i, n + i))                # radio
        edges.append((n + i, n + (i + k) % n))  # estrella interior
    lab = list(range(2 * n))
    if seed is not None:
        random.Random(seed).shuffle(lab)
    edges = [(lab[u], lab[v]) for u, v in edges]
    return Graph(2 * n, edges, name=f"GP({n},{k})")


def planted_hamiltonian(n: int, extra_deg: float = 1.5, seed: int = 0):
    """Devuelve (grafo, ciclo_oculto). Grado promedio aproximado: 2 + extra_deg."""
    rng = random.Random(seed)
    order = list(range(n))
    rng.shuffle(order)
    edges = set()
    for i in range(n):
        a, b = order[i], order[(i + 1) % n]
        edges.add((min(a, b), max(a, b)))
    target = int(round(n * (2 + extra_deg) / 2))
    while len(edges) < target:
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            edges.add((min(a, b), max(a, b)))
    g = Graph(n, edges, name=f"planted_n{n}_d{2 + extra_deg:g}")
    return g, order
