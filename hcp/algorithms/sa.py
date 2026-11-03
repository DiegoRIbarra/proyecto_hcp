"""Recocido Simulado (Simulated Annealing, Kirkpatrick et al., 1983).

Movimientos: intercambio aleatorio de índices (swap), inversión aleatoria (2-opt) e
inversión guiada por el grafo. Criterio de Metropolis: se acepta un empeoramiento d > 0
con probabilidad exp(-d / T).

Enfriamiento: geométrico por movimiento, T <- alpha * T, con alpha muy cercano a 1
(enfriamiento lento). Cada ciclo baja T de T0 a T_fin en L = cycle_factor * n movimientos;
al terminar un ciclo sin encontrar la solución se recalienta (T = T0) partiendo de la
mejor solución conocida. Así el algoritmo converge rápido en grafos pequeños y sigue
explorando en grafos grandes dentro del presupuesto de tiempo.

Versión anterior del borrador (v1): un solo enfriamiento a lo largo de todo el presupuesto
de tiempo; se descartó porque solo se "congelaba" al final del tiempo límite.
"""
from __future__ import annotations

import math
import random
from ..core import cost, initial_solution
from .base import Tracker
from .moves import random_swap, random_inversion, guided_inversion, make_pos


def solve(g, time_limit=10.0, seed=0, max_evals=None, t0=1.0, t_end=0.02,
          cycle_factor=2000, min_cycle=20000, p_swap=0.34, p_inv=0.33, init="greedy"):
    rng = random.Random(seed)
    tr = Tracker(g, time_limit, max_evals)
    n = g.n
    L = max(min_cycle, cycle_factor * n)          # movimientos por ciclo de enfriamiento
    alpha = (t_end / t0) ** (1.0 / L)             # factor geométrico por movimiento
    params = dict(t0=t0, t_end=t_end, movimientos_por_ciclo=L, alpha=round(alpha, 8),
                  p_swap=p_swap, p_inv=p_inv, p_guided=round(1 - p_swap - p_inv, 2), init=init)
    p = initial_solution(g, rng, init)
    pos = make_pos(p)
    c = cost(g, p)
    tr.evals += 1
    tr.offer(p, c)
    T = t0
    k = 0
    while True:
        if tr.iterations % 2000 == 0 and tr.done():
            break
        r = rng.random()
        if r < p_swap:
            d, apply = random_swap(g, p, pos, rng)
        elif r < p_swap + p_inv:
            d, apply = random_inversion(g, p, pos, rng)
        else:
            d, apply = guided_inversion(g, p, pos, rng)
        tr.evals += 1
        tr.iterations += 1
        if d <= 0 or rng.random() < math.exp(-d / T):
            apply()
            c += d
            if c < tr.best_cost:
                tr.offer(p, c)
                if c == 0:
                    break
        T *= alpha
        k += 1
        if k >= L:                                # fin de ciclo: recalentar desde la mejor
            p = list(tr.best_perm)
            pos = make_pos(p)
            c = tr.best_cost
            T = t0
            k = 0
    tr.done()
    return tr.result("SA", params)
