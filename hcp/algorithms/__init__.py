"""Metaheurísticas implementadas. Todas exponen solve(g, time_limit, seed, max_evals, ...)."""
from . import ga, sa, aco, abc, de, pso, lkh_ref

ALGORITHMS = {
    "GA": ga.solve,
    "SA": sa.solve,
    "ACO": aco.solve,
    "ABC": abc.solve,
    "DE": de.solve,
    "PSO": pso.solve,
}
