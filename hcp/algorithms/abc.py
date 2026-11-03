"""Colonia Artificial de Abejas (Artificial Bee Colony, Karaboga, 2005), versión discreta.

* Fuentes de alimento = permutaciones. Aptitud = 1 / (1 + costo).
* Abejas empleadas: cada una explora un vecino de su fuente (swap, 2-opt o 2-opt guiado)
  y se queda con él si no empeora (selección voraz).
* Abejas observadoras: eligen fuentes por ruleta según la aptitud y las explotan igual.
* Abejas exploradoras: una fuente que no mejora en `limit` intentos se abandona y se
  reemplaza por una nueva construida con la regla de Warnsdorff.
"""
from __future__ import annotations

import random
from ..core import cost, initial_solution
from .base import Tracker
from .moves import random_swap, random_inversion, guided_inversion, make_pos


def solve(g, time_limit=10.0, seed=0, max_evals=None, sources=20, limit=None,
          p_guided=0.5, init="greedy"):
    rng = random.Random(seed)
    tr = Tracker(g, time_limit, max_evals)
    n = g.n
    limit = limit if limit is not None else max(100, 5 * n)
    params = dict(sources=sources, limit=limit, p_guided=p_guided, init=init)
    foods = [initial_solution(g, rng, init) for _ in range(sources)]
    poss = [make_pos(f) for f in foods]
    costs = [cost(g, f) for f in foods]
    trials = [0] * sources
    tr.evals += sources
    for f, c in zip(foods, costs):
        tr.offer(f, c)

    def explore(k):
        p, pos = foods[k], poss[k]
        r = rng.random()
        if r < p_guided:
            d, apply = guided_inversion(g, p, pos, rng)
        elif r < p_guided + (1 - p_guided) / 2:
            d, apply = random_inversion(g, p, pos, rng)
        else:
            d, apply = random_swap(g, p, pos, rng)
        tr.evals += 1
        if d <= 0:
            apply()
            costs[k] += d
            trials[k] = 0 if d < 0 else trials[k] + 1
            if d < 0:
                tr.offer(p, costs[k])
        else:
            trials[k] += 1

    while not tr.done():
        for _ in range(50):  # 50 ciclos de abejas entre revisiones del reloj
            for k in range(sources):           # fase de empleadas
                explore(k)
            fit = [1.0 / (1 + c) for c in costs]
            for _ in range(sources):           # fase de observadoras
                k = rng.choices(range(sources), weights=fit)[0]
                explore(k)
            if tr.best_cost == 0:
                break
            worst = max(range(sources), key=lambda k: trials[k])   # fase de exploradoras
            if trials[worst] > limit and costs[worst] > tr.best_cost:
                foods[worst] = initial_solution(g, rng, init)
                poss[worst] = make_pos(foods[worst])
                costs[worst] = cost(g, foods[worst])
                trials[worst] = 0
                tr.evals += 1
                tr.offer(foods[worst], costs[worst])
            tr.iterations += 1
    return tr.result("ABC", params)
