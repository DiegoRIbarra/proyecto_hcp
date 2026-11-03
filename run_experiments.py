"""Ejecuta las metaheurísticas sobre un conjunto de instancias y guarda los resultados.

Ejemplos
--------
# 1) Generar el conjunto de prueba del borrador (familias del FHCP + grafos plantados):
python run_experiments.py --generate-suite instances

# 2) Correr todos los algoritmos, 5 semillas, 10 s por corrida:
python run_experiments.py --instances instances --runs 5 --time 10 --out results

# 3) Correr sobre el FHCP real (descomprimir FHCPCS.7z en fhcp/ y las soluciones en fhcp_sols/):
python run_experiments.py --instances fhcp --solutions fhcp_sols --max-n 1000 --runs 5 --time 30 --out results_fhcp
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hcp.io import read_hcp, write_hcp, write_tour, read_tour  # noqa: E402
from hcp.core import is_hamiltonian, edge_metrics  # noqa: E402
from hcp.generators import envelope, generalized_petersen, planted_hamiltonian  # noqa: E402
from hcp.algorithms import ALGORITHMS, lkh_ref  # noqa: E402

_CACHE = {}


def load(path):
    if path not in _CACHE:
        _CACHE[path] = read_hcp(path)
    return _CACHE[path]


def generate_suite(folder):
    """Conjunto del borrador: familias presentes en el FHCP y grafos con ciclo plantado."""
    os.makedirs(folder, exist_ok=True)
    os.makedirs(os.path.join(folder, "sols"), exist_ok=True)
    items = []
    g = envelope()
    items.append((g, [0, 1, 2, 5, 4, 3], "Ejemplo del sitio del FHCP"))
    for n in (9, 33, 75, 159):  # n = 3 (mod 6): exactamente 3 ciclos hamiltonianos
        items.append((generalized_petersen(n, 2, seed=n), None,
                      "Petersen generalizado GP(n,2), n = 3 mod 6 (familia incluida en el FHCP)"))
    for n in (100, 300, 1000):
        g, hc = planted_hamiltonian(n, extra_deg=1.0, seed=n)
        items.append((g, hc, "Aleatorio disperso (grado medio 3) con ciclo hamiltoniano plantado"))
    for g, hc, comment in items:
        fname = g.name.replace("(", "_").replace(")", "").replace(",", "_")
        g.name = fname
        write_hcp(os.path.join(folder, fname + ".hcp"), g, comment)
        if hc is not None:
            write_tour(os.path.join(folder, "sols", fname + ".tour"), fname, hc, "Ciclo de referencia")
    print(f"{len(items)} instancias escritas en {folder}/")


def job(args):
    path, algo, seed, tlimit, sols_dir, tours_dir = args
    g = load(path)
    if algo == "LKH":
        r = lkh_ref.solve(g, runs=10)
    else:
        r = ALGORITHMS[algo](g, time_limit=tlimit, seed=seed)
    perm = r.pop("perm")
    ref = None
    if sols_dir:
        ref_path = os.path.join(sols_dir, os.path.splitext(os.path.basename(path))[0] + ".tour")
        if os.path.exists(ref_path):
            ref = read_tour(ref_path)
    met = edge_metrics(g, perm, ref)
    valid = is_hamiltonian(g, perm)
    if r["exito"] and not valid:
        raise RuntimeError(f"{algo} reportó éxito con un ciclo inválido en {path}")
    if valid and tours_dir:
        write_tour(os.path.join(tours_dir, f"{g.name}__{algo}__s{seed}.tour"), g.name, perm)
    st = g.stats()
    row = {
        "instancia": g.name, "n": st["n"], "m": st["m"], "grado_prom": st["grado_prom"],
        "algoritmo": algo, "semilla": seed, "exito": int(valid),
        "mejor_costo": r["mejor_costo"], "aristas_validas": g.n - r["mejor_costo"],
        "precision": round(met["precision"], 4),
        "recall_ref": round(met["recall_ref"], 4) if "recall_ref" in met else "",
        "f1_ref": round(met["f1_ref"], 4) if "f1_ref" in met else "",
        "tiempo_total_s": r["tiempo_total_s"], "tiempo_a_mejor_s": r["tiempo_a_mejor_s"],
        "iteraciones": r["iteraciones"], "evaluaciones": r["evaluaciones"] if r["evaluaciones"] is not None else "",
        "criterio_paro": r["criterio_paro"], "parametros": json.dumps(r["parametros"]),
    }
    return row, {"instancia": g.name, "algoritmo": algo, "semilla": seed, "historia": r["historia"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate-suite", metavar="CARPETA")
    ap.add_argument("--instances", default="instances")
    ap.add_argument("--solutions", default=None, help="carpeta con <instancia>.tour de referencia")
    ap.add_argument("--algos", default="GA,SA,ACO,ABC,DE,PSO,LKH")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--time", type=float, default=10.0, help="segundos por corrida")
    ap.add_argument("--max-n", type=int, default=None, help="ignora instancias con más vértices")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    if a.generate_suite:
        generate_suite(a.generate_suite)
        return
    sols = a.solutions or (os.path.join(a.instances, "sols") if os.path.isdir(os.path.join(a.instances, "sols")) else None)
    paths = sorted(glob.glob(os.path.join(a.instances, "*.hcp")))
    if a.max_n:
        paths = [p for p in paths if load(p).n <= a.max_n]
    algos = [x.strip() for x in a.algos.split(",") if x.strip()]
    os.makedirs(a.out, exist_ok=True)
    tours = os.path.join(a.out, "tours")
    os.makedirs(tours, exist_ok=True)
    jobs = []
    for p in paths:
        for al in algos:
            seeds = [0] if al == "LKH" else range(a.runs)
            for s in seeds:
                jobs.append((p, al, s, a.time, sols, tours))
    print(f"{len(paths)} instancias x {len(algos)} algoritmos -> {len(jobs)} corridas")
    t0 = time.time()
    rows, hist = [], []
    with Pool(a.workers) as pool:
        for k, (row, h) in enumerate(pool.imap_unordered(job, jobs), 1):
            rows.append(row)
            hist.append(h)
            print(f"[{k}/{len(jobs)}] {row['instancia']:<22} {row['algoritmo']:<5} s={row['semilla']} "
                  f"costo={row['mejor_costo']} exito={row['exito']} t={row['tiempo_total_s']}s", flush=True)
    rows.sort(key=lambda r: (r["n"], r["instancia"], r["algoritmo"], r["semilla"]))
    with open(os.path.join(a.out, "resultados.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(a.out, "historias.json"), "w", encoding="utf-8") as fh:
        json.dump(hist, fh)
    print(f"Listo en {time.time() - t0:.1f} s -> {a.out}/resultados.csv")


if __name__ == "__main__":
    main()
