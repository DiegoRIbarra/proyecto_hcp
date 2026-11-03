"""Lectura y escritura de archivos en formato HCP y TOUR (FHCP Challenge Set / TSPLIB)."""
from __future__ import annotations

import os
from .core import Graph


def read_hcp(path: str) -> Graph:
    """Lee un archivo .hcp (lista de aristas, vértices numerados desde 1)."""
    name = os.path.splitext(os.path.basename(path))[0]
    n = None
    edges = []
    in_edges = False
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            if not in_edges:
                key = line.split(":")[0].strip().upper()
                if key == "NAME":
                    name = line.split(":", 1)[1].strip() or name
                elif key == "DIMENSION":
                    n = int(line.split(":", 1)[1])
                elif key.startswith("EDGE_DATA_SECTION"):
                    in_edges = True
                continue
            if line in ("-1", "EOF"):
                if line == "EOF":
                    break
                in_edges = False
                continue
            parts = line.split()
            # Algunas variantes escriben "u v" y otras usan varias aristas por línea.
            nums = [int(x) for x in parts]
            for k in range(0, len(nums) - 1, 2):
                edges.append((nums[k] - 1, nums[k + 1] - 1))
    if n is None:
        raise ValueError(f"{path}: falta DIMENSION")
    return Graph(n, edges, name=name)


def write_hcp(path: str, g: Graph, comment: str = "") -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"NAME : {g.name}\n")
        if comment:
            fh.write(f"COMMENT : {comment}\n")
        fh.write("TYPE : HCP\n")
        fh.write(f"DIMENSION : {g.n}\n")
        fh.write("EDGE_DATA_FORMAT : EDGE_LIST\n")
        fh.write("EDGE_DATA_SECTION\n")
        for u, v in g.edges():
            fh.write(f"{u + 1} {v + 1}\n")
        fh.write("-1\nEOF\n")


def write_tour(path: str, name: str, perm, comment: str = "Tour found") -> None:
    """Escribe la solución en el formato TOUR del FHCP (vértices desde 1)."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"NAME : {name}\n")
        fh.write(f"COMMENT : {comment}\n")
        fh.write("TYPE : TOUR\n")
        fh.write(f"DIMENSION : {len(perm)}\n")
        fh.write("TOUR_SECTION\n")
        for v in perm:
            fh.write(f"{int(v) + 1}\n")
        fh.write("-1\nEOF\n")


def read_tour(path: str) -> list:
    tour = []
    reading = False
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if line.upper().startswith("TOUR_SECTION"):
                reading = True
                continue
            if reading:
                if line in ("-1", "EOF") or not line:
                    break
                tour.extend(int(x) - 1 for x in line.split())
    return tour
