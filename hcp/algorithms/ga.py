"""Algoritmo Genético (GA) — base de control.

Representación de camino (permutación). Selección por torneo, cruza OX (Davis, 1985)
o ERX (Whitley et al., 1989), mutación por inversión y elitismo.
"""
from __future__ import annotations

import random
from ..core import cost, initial_solution
from .base import Tracker


def ox(p1, p2, rng):
    """Order Crossover: copia un segmento de p1 y completa con el orden relativo de p2."""
    n = len(p1)
    i, j = sorted(rng.sample(range(n), 2))
    child = [None] * n
    child[i:j + 1] = p1[i:j + 1]
    used = set(p1[i:j + 1])
    fill = [v for v in p2[j + 1:] + p2[:j + 1] if v not in used]
    positions = list(range(j + 1, n)) + list(range(0, i))
    for k, v in zip(positions, fill):
        child[k] = v
    return child


def erx(p1, p2, rng):
    """Edge Recombination: el hijo hereda, en lo posible, las adyacencias de los padres."""
    n = len(p1)
    neigh = [set() for _ in range(n)]
    for p in (p1, p2):
        for k in range(n):
            a = p[k]
            neigh[a].add(p[k - 1])
            neigh[a].add(p[(k + 1) % n])
    remaining = list(range(n))
    pos = list(range(n))

    def remove(v):
        k = pos[v]
        last = remaining[-1]
        remaining[k] = last
        pos[last] = k
        remaining.pop()

    cur = p1[rng.randrange(n)]
    child = [cur]
    remove(cur)
    while remaining:
        for x in neigh[cur]:
            neigh[x].discard(cur)
        cand = list(neigh[cur])
        if cand:
            best = min(len(neigh[x]) for x in cand)
            cur = rng.choice([x for x in cand if len(neigh[x]) == best])
        else:
            cur = remaining[rng.randrange(len(remaining))]
        child.append(cur)
        remove(cur)
    return child


def solve(g, time_limit=10.0, seed=0, max_evals=None, pop_size=60, pc=0.9, pm=0.3,
          tournament=3, elite=2, crossover="ox", init="greedy"):
    rng = random.Random(seed)
    tr = Tracker(g, time_limit, max_evals)
    params = dict(pop_size=pop_size, pc=pc, pm=pm, tournament=tournament, elite=elite,
                  crossover=crossover, init=init)
    xover = erx if crossover == "erx" else ox
    n = g.n
    pop = [initial_solution(g, rng, init) for _ in range(pop_size)]
    costs = [cost(g, p) for p in pop]
    tr.evals += pop_size
    for p, c in zip(pop, costs):
        tr.offer(p, c)

    def pick():
        best = None
        for _ in range(tournament):
            k = rng.randrange(pop_size)
            if best is None or costs[k] < costs[best]:
                best = k
        return pop[best]

    while not tr.done():
        order = sorted(range(pop_size), key=lambda k: costs[k])
        new_pop = [pop[k][:] for k in order[:elite]]
        new_costs = [costs[k] for k in order[:elite]]
        while len(new_pop) < pop_size:
            a, b = pick(), pick()
            child = xover(a, b, rng) if rng.random() < pc else a[:]
            if rng.random() < pm and n > 3:
                i, j = sorted(rng.sample(range(n), 2))
                child[i:j + 1] = child[i:j + 1][::-1]
            c = cost(g, child)
            tr.evals += 1
            tr.offer(child, c)
            new_pop.append(child)
            new_costs.append(c)
            if tr.best_cost == 0:
                break
        pop, costs = new_pop, new_costs
        tr.iterations += 1
    return tr.result("GA", params)
