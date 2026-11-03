"""Referencia externa: LKH (Helsgaun, 2000) vía el paquete `elkai`.

El FHCP usó LKH como uno de sus tres algoritmos de referencia. Aquí el HCP se reduce al
TSP con pesos 0/1 (0 si la arista existe, 1 si no) y se resuelve con LKH.
Solo para instancias pequeñas/medianas (construye una matriz n x n).
"""
from __future__ import annotations

import time
import numpy as np
from ..core import cost


def solve(g, time_limit=None, seed=0, max_evals=None, runs=10):
    try:
        import elkai
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Instala elkai: pip install elkai") from exc
    t0 = time.perf_counter()
    M = np.where(g.A, 0, 1).astype(int)
    np.fill_diagonal(M, 0)
    tour = elkai.DistanceMatrix(M.tolist()).solve_tsp(runs=runs)
    if len(tour) == g.n + 1:
        tour = tour[:-1]
    c = cost(g, tour)
    el = time.perf_counter() - t0
    return {
        "algoritmo": "LKH (ref.)", "mejor_costo": c, "exito": c == 0,
        "tiempo_total_s": round(el, 4), "tiempo_a_mejor_s": round(el, 4),
        "iteraciones": runs, "evaluaciones": None, "criterio_paro": "lkh",
        "parametros": {"runs": runs}, "historia": [(round(el, 4), c)], "perm": tour,
    }
