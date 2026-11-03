"""Evolución Diferencial (DE, Storn y Price, 1997) adaptada a permutaciones con claves aleatorias.

Cada individuo es un vector real de n claves. El decodificador ordena los vértices por su
clave (Bean, 1994), así que toda solución es una permutación válida. Esquema DE/rand/1/bin:
    v = x_r1 + F (x_r2 - x_r3);  u = cruza binomial(x_i, v, CR);  se queda u si no empeora.
"""
from __future__ import annotations

import random
import numpy as np
from ..core import cost, initial_solution, random_keys_decode
from .base import Tracker


def encode(perm, rng_np, noise=0.02):
    """Convierte una permutación en claves aleatorias (para iniciar desde Warnsdorff)."""
    n = len(perm)
    keys = np.empty(n)
    keys[np.asarray(perm)] = np.arange(n) / n
    return keys + rng_np.uniform(-noise / n, noise / n, n)


def solve(g, time_limit=10.0, seed=0, max_evals=None, np_size=30, F=0.5, CR=0.9, init="greedy"):
    rng = random.Random(seed)
    rnp = np.random.default_rng(seed)
    tr = Tracker(g, time_limit, max_evals)
    params = dict(np_size=np_size, F=F, CR=CR, esquema="DE/rand/1/bin", init=init)
    n = g.n
    if init == "greedy":
        X = np.array([encode(initial_solution(g, rng, "greedy"), rnp) for _ in range(np_size)])
    else:
        X = rnp.random((np_size, n))
    C = np.array([cost(g, random_keys_decode(x)) for x in X])
    tr.evals += np_size
    for x, c in zip(X, C):
        tr.offer(random_keys_decode(x), c)
    while not tr.done():
        for i in range(np_size):
            r1, r2, r3 = rnp.choice([k for k in range(np_size) if k != i], 3, replace=False)
            v = X[r1] + F * (X[r2] - X[r3])
            mask = rnp.random(n) < CR
            mask[rnp.integers(n)] = True
            u = np.where(mask, v, X[i])
            perm = random_keys_decode(u)
            cu = cost(g, perm)
            tr.evals += 1
            if cu <= C[i]:
                X[i], C[i] = u, cu
                tr.offer(perm, cu)
            if tr.best_cost == 0:
                break
        tr.iterations += 1
    return tr.result("DE", params)
