"""Optimización por Colonia de Hormigas (ACO), variante MAX-MIN Ant System (Stützle y Hoos, 2000).

Cada hormiga construye un recorrido caminando SOLO por aristas reales del grafo. En cada
paso elige un vecino no visitado w con probabilidad proporcional a
    tau(cur, w)^alpha * eta(w)^beta,   eta(w) = 1 / (1 + vecinos_libres(w))
(la heurística de Warnsdorff). Si se bloquea, salta a un vértice no visitado al azar,
lo que cuesta una arista faltante. La feromona se evapora y la mejor hormiga deposita
feromona en las aristas reales de su recorrido; se acota a [tau_min, tau_max].
"""
from __future__ import annotations

import random
from ..core import cost
from .base import Tracker


def solve(g, time_limit=10.0, seed=0, max_evals=None, ants=10, alpha=1.0, beta=2.0,
          rho=0.1, init=None):
    rng = random.Random(seed)
    tr = Tracker(g, time_limit, max_evals)
    params = dict(ants=ants, alpha=alpha, beta=beta, rho=rho)
    n = g.n
    eid = {}
    for u, v in g.edges():
        eid[(u, v)] = eid[(v, u)] = len(eid) // 2
    m = g.m
    tau_max = 1.0 / rho
    tau_min = tau_max / (2.0 * n)
    tau = [tau_max] * m
    best_global = None
    best_global_cost = None

    def construct():
        visited = bytearray(n)
        free = [len(s) for s in g.adj]
        unvisited = list(range(n))
        posu = list(range(n))

        def mark(v):
            visited[v] = 1
            k = posu[v]
            last = unvisited[-1]
            unvisited[k] = last
            posu[last] = k
            unvisited.pop()
            for w in g.adj_list[v]:
                free[w] -= 1

        cur = rng.randrange(n)
        tour = [cur]
        mark(cur)
        while unvisited:
            cand = [w for w in g.adj_list[cur] if not visited[w]]
            if cand:
                ws = [(tau[eid[(cur, w)]] ** alpha) * ((1.0 / (1 + free[w])) ** beta) for w in cand]
                cur = rng.choices(cand, weights=ws)[0]
            else:
                cur = unvisited[rng.randrange(len(unvisited))]
            tour.append(cur)
            mark(cur)
        return tour

    while not tr.done():
        it_best, it_cost = None, None
        for _ in range(ants):
            t = construct()
            c = cost(g, t)
            tr.evals += 1
            if it_cost is None or c < it_cost:
                it_best, it_cost = t, c
            if tr.offer(t, c):
                best_global, best_global_cost = t, c
            if c == 0 or tr.elapsed() >= tr.time_limit:
                break
        if tr.best_cost == 0:
            break
        # Evaporación
        for k in range(m):
            tau[k] *= (1.0 - rho)
        # Depósito: mejor de la iteración (y cada 10 iteraciones, el mejor global)
        dep, dep_cost = (best_global, best_global_cost) if tr.iterations % 10 == 9 else (it_best, it_cost)
        amount = 1.0 / (1.0 + dep_cost)
        for k in range(n):
            a, b = dep[k], dep[(k + 1) % n]
            e = eid.get((a, b))
            if e is not None:
                tau[e] += amount
        for k in range(m):
            if tau[k] > tau_max:
                tau[k] = tau_max
            elif tau[k] < tau_min:
                tau[k] = tau_min
        tr.iterations += 1
    return tr.result("ACO", params)
