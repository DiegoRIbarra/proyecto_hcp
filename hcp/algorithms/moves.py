"""Movimientos de vecindad sobre permutaciones con evaluación incremental.

Cada función propone un movimiento, devuelve (delta, aplicar) donde `aplicar()` ejecuta
el cambio sobre la permutación `p` y su arreglo de posiciones `pos` (pos[v] = índice de v).
"""
from __future__ import annotations

from ..core import delta_inversion, delta_swap


def _invert(p, pos, i, j):
    p[i:j + 1] = p[i:j + 1][::-1]
    for k in range(i, j + 1):
        pos[p[k]] = k


def random_swap(g, p, pos, rng):
    """Intercambio de dos índices al azar (movimiento pedido para SA)."""
    n = len(p)
    i, j = rng.randrange(n), rng.randrange(n)
    if i == j:
        return 0, lambda: None
    d = delta_swap(g, p, i, j)

    def apply():
        a, b = p[i], p[j]
        p[i], p[j] = b, a
        pos[a], pos[b] = j, i
    return d, apply


def random_inversion(g, p, pos, rng):
    """Inversión de un segmento al azar (2-opt)."""
    n = len(p)
    i, j = sorted((rng.randrange(n), rng.randrange(n)))
    if i == j or (i == 0 and j == n - 1):
        return 0, lambda: None
    d = delta_inversion(g, p, i, j)
    return d, (lambda: _invert(p, pos, i, j))


def guided_inversion(g, p, pos, rng):
    """2-opt guiado por el grafo: elige un vértice a y un vecino real b de a, e invierte
    el segmento necesario para que a y b queden consecutivos (crea la arista {a, b})."""
    n = len(p)
    i = rng.randrange(n)
    a = p[i]
    nb = g.adj_list[a]
    if not nb:
        return 0, lambda: None
    b = nb[rng.randrange(len(nb))]
    j = pos[b]
    if j == (i + 1) % n or i == (j + 1) % n:
        return 0, lambda: None
    if j > i:
        lo, hi = i + 1, j          # queda ... a, b, ...
    else:
        lo, hi = j, i - 1          # queda ... b(invertido) ... junto a a
    if lo >= hi or (lo == 0 and hi == n - 1):
        return 0, lambda: None
    d = delta_inversion(g, p, lo, hi)
    return d, (lambda: _invert(p, pos, lo, hi))


def make_pos(p):
    pos = [0] * len(p)
    for k, v in enumerate(p):
        pos[v] = k
    return pos
