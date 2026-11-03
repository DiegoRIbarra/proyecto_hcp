"""Optimización por Enjambre de Partículas (PSO, Kennedy y Eberhart, 1995) con claves aleatorias.

Cada partícula es un vector real de n claves decodificado por ordenamiento. Actualización
con coeficiente de inercia (Shi y Eberhart, 1998) y los valores de Clerc y Kennedy (2002):
    v <- w v + c1 r1 (pbest - x) + c2 r2 (gbest - x);   x <- x + v
"""
from __future__ import annotations

import random
import numpy as np
from ..core import cost, initial_solution, random_keys_decode
from .base import Tracker
from .de import encode


def solve(g, time_limit=10.0, seed=0, max_evals=None, swarm=30, w=0.729, c1=1.49445,
          c2=1.49445, vmax=0.1, init="greedy"):
    rng = random.Random(seed)
    rnp = np.random.default_rng(seed)
    tr = Tracker(g, time_limit, max_evals)
    params = dict(swarm=swarm, w=w, c1=c1, c2=c2, vmax=vmax, init=init)
    n = g.n
    if init == "greedy":
        X = np.array([encode(initial_solution(g, rng, "greedy"), rnp) for _ in range(swarm)])
    else:
        X = rnp.random((swarm, n))
    V = rnp.uniform(-vmax, vmax, (swarm, n))
    C = np.array([cost(g, random_keys_decode(x)) for x in X])
    tr.evals += swarm
    P, PC = X.copy(), C.copy()
    gi = int(np.argmin(PC))
    for x, c in zip(X, C):
        tr.offer(random_keys_decode(x), c)
    while not tr.done():
        r1 = rnp.random((swarm, n))
        r2 = rnp.random((swarm, n))
        V = w * V + c1 * r1 * (P - X) + c2 * r2 * (P[gi] - X)
        np.clip(V, -vmax, vmax, out=V)
        X = X + V
        for k in range(swarm):
            perm = random_keys_decode(X[k])
            c = cost(g, perm)
            tr.evals += 1
            if c <= PC[k]:
                P[k], PC[k] = X[k], c
                if c <= PC[gi]:
                    gi = k
                tr.offer(perm, c)
        tr.iterations += 1
    return tr.result("PSO", params)
