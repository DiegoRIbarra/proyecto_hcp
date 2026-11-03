"""Utilidades comunes a todas las metaheurísticas: control de presupuesto y registro."""
from __future__ import annotations

import time


class Tracker:
    """Lleva el mejor resultado, cuenta evaluaciones/iteraciones y decide cuándo parar.

    Criterios de paro: (1) se encontró un ciclo hamiltoniano (costo 0);
    (2) se agotó el tiempo límite; (3) se agotó el número máximo de evaluaciones.
    """

    def __init__(self, g, time_limit: float, max_evals: int | None = None):
        self.g = g
        self.t0 = time.perf_counter()
        self.time_limit = time_limit
        self.max_evals = max_evals
        self.evals = 0
        self.iterations = 0
        self.best_cost = None
        self.best_perm = None
        self.time_to_best = 0.0
        self.history = []  # (segundos, mejor_costo) en cada mejora
        self.stop_reason = None

    def elapsed(self) -> float:
        return time.perf_counter() - self.t0

    def offer(self, perm, c: int) -> bool:
        """Registra una solución candidata; devuelve True si mejora la mejor global."""
        if self.best_cost is None or c < self.best_cost:
            self.best_cost = int(c)
            self.best_perm = [int(x) for x in perm]
            self.time_to_best = self.elapsed()
            self.history.append((round(self.time_to_best, 4), self.best_cost))
            return True
        return False

    def done(self) -> bool:
        if self.best_cost == 0:
            self.stop_reason = "solucion"
            return True
        if self.elapsed() >= self.time_limit:
            self.stop_reason = "tiempo"
            return True
        if self.max_evals is not None and self.evals >= self.max_evals:
            self.stop_reason = "evaluaciones"
            return True
        return False

    def result(self, algorithm: str, params: dict) -> dict:
        if self.stop_reason is None:
            self.done()
        return {
            "algoritmo": algorithm,
            "mejor_costo": self.best_cost,
            "exito": self.best_cost == 0,
            "tiempo_total_s": round(self.elapsed(), 4),
            "tiempo_a_mejor_s": round(self.time_to_best, 4),
            "iteraciones": self.iterations,
            "evaluaciones": self.evals,
            "criterio_paro": self.stop_reason,
            "parametros": params,
            "historia": self.history,
            "perm": self.best_perm,
        }
