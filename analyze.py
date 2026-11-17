"""Resume resultados.csv: tablas por instancia y algoritmo, pruebas estadísticas y figuras.

Uso: python analyze.py --results results
Genera en results/: resumen_instancia_algoritmo.csv, resumen_algoritmos.csv,
estadistica.json y figuras/*.png
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy import stats  # noqa: E402

ORDER = ["GA", "SA", "ACO", "ABC", "DE", "PSO"]
COLORS = {  # paleta categórica validada (orden fijo, nunca reciclado)
    "GA": "#2a78d6", "SA": "#eb6834", "ACO": "#1baf7a",
    "ABC": "#eda100", "DE": "#e87ba4", "PSO": "#008300", "LKH": "#6b6b6b",
}
INK, MUTED, GRID = "#1f1f1e", "#5f5e58", "#e6e5e0"


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#b9b8b0")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.label.set_color(INK)
    ax.xaxis.label.set_color(INK)


def inst_order(df):
    return (df.groupby("instancia")["n"].first().sort_values().index.tolist())


def heatmap(mat, rows, cols, title, fname, fmt, cmap="Blues", note=None, vmax=None, labels=None):
    fig, ax = plt.subplots(figsize=(1.05 * len(cols) + 2.6, 0.42 * len(rows) + 1.6), dpi=200)
    im = ax.imshow(mat, cmap=cmap, aspect="auto", vmin=0, vmax=vmax if vmax is not None else np.nanmax(mat))
    ax.set_xticks(range(len(cols)), cols)
    ax.set_yticks(range(len(rows)), rows)
    ax.xaxis.tick_top()
    for i in range(len(rows)):
        for j in range(len(cols)):
            v = mat[i, j]
            if np.isnan(v):
                txt, col = "—", MUTED
            else:
                txt = labels[i][j] if labels is not None else fmt(v)
                col = "white" if v > 0.6 * (vmax if vmax is not None else np.nanmax(mat)) else INK
            ax.text(j, i, txt, ha="center", va="center", fontsize=9, color=col)
    ax.set_title(title, fontsize=11, color=INK, pad=28, loc="left")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, labelsize=9, colors=INK)
    if note:
        fig.text(0.01, 0.01, note, fontsize=8, color=MUTED)
    fig.tight_layout()
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def heatmap_pages(mat, rows, cols, title, fname, fmt, cmap="Blues", note=None,
                  vmax=None, labels=None, rows_per_page=45):
    """Guarda un heatmap paginado para que cada fila siga siendo legible."""
    stem, ext = os.path.splitext(fname)
    for old in glob.glob(f"{stem}_*.png"):
        os.remove(old)
    page_count = max(1, (len(rows) + rows_per_page - 1) // rows_per_page)
    for page in range(page_count):
        start = page * rows_per_page
        end = min(start + rows_per_page, len(rows))
        page_title = f"{title} (página {page + 1}/{page_count})"
        page_fname = fname if page == 0 else f"{stem}_{page + 1:03d}{ext}"
        page_note = note if page_count == 1 else f"{note} | instancias {start + 1}-{end} de {len(rows)}"
        page_labels = None if labels is None else labels[start:end]
        heatmap(mat[start:end], rows[start:end], cols, page_title, page_fname, fmt,
                cmap=cmap, note=page_note, vmax=vmax, labels=page_labels)


def convergence(hist, inst, t_limit, fname, title):
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=200)
    grid = np.linspace(0, t_limit, 200)
    last_y = {}
    for alg in ORDER:
        curves = []
        for h in hist:
            if h["instancia"] != inst or h["algoritmo"] != alg or not h["historia"]:
                continue
            ts = np.array([p[0] for p in h["historia"]])
            cs = np.array([p[1] for p in h["historia"]], dtype=float)
            idx = np.searchsorted(ts, grid, side="right") - 1
            y = cs[np.clip(idx, 0, None)]
            curves.append(y)
        if not curves:
            continue
        med = np.nanmedian(np.vstack(curves), axis=0)
        ax.step(grid, med, where="post", color=COLORS[alg], lw=2, label=alg)
        last_y[alg] = med[-1]
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Mediana del mejor c(π)")
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    style(ax)
    ax.legend(frameon=False, fontsize=8, ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    ax.set_title(title, fontsize=10.5, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    a = ap.parse_args()
    df = pd.read_csv(os.path.join(a.results, "resultados.csv"))
    with open(os.path.join(a.results, "historias.json"), encoding="utf-8") as fh:
        hist = json.load(fh)
    figdir = os.path.join(a.results, "figuras")
    os.makedirs(figdir, exist_ok=True)
    meta = df[df.algoritmo != "LKH"]
    algorithms = [algorithm for algorithm in ORDER if algorithm in set(meta.algoritmo)]
    if not algorithms:
        raise ValueError("resultados.csv no contiene algoritmos comparables (GA, SA, ACO, ABC, DE o PSO)")
    t_limit = float(meta.tiempo_total_s.max())

    # ------------------------------------------------ tabla instancia x algoritmo
    g = df.groupby(["instancia", "algoritmo"])
    summ = g.agg(n=("n", "first"), m=("m", "first"), corridas=("exito", "size"), exitos=("exito", "sum"),
                 costo_min=("mejor_costo", "min"), costo_prom=("mejor_costo", "mean"),
                 costo_de=("mejor_costo", "std"), precision_prom=("precision", "mean"),
                 tiempo_prom_s=("tiempo_total_s", "mean"), evaluaciones_prom=("evaluaciones", "mean"),
                 iteraciones_prom=("iteraciones", "mean")).reset_index()
    succ_t = df[df.exito == 1].groupby(["instancia", "algoritmo"])["tiempo_a_mejor_s"].mean()
    summ["tiempo_a_solucion_s"] = summ.set_index(["instancia", "algoritmo"]).index.map(succ_t)
    f1 = df[df.f1_ref.notna()].groupby(["instancia", "algoritmo"])["f1_ref"].mean()
    summ["f1_ref_prom"] = summ.set_index(["instancia", "algoritmo"]).index.map(f1)
    summ["tasa_exito"] = summ.exitos / summ.corridas
    summ = summ.sort_values(["n", "instancia", "algoritmo"])
    summ.round(4).to_csv(os.path.join(a.results, "resumen_instancia_algoritmo.csv"), index=False)

    # ------------------------------------------------ resumen por algoritmo
    meta = meta.assign(costo_norm=meta.mejor_costo / meta.n)
    alg = meta.groupby("algoritmo").agg(corridas=("exito", "size"), exitos=("exito", "sum"),
                                        costo_norm_prom=("costo_norm", "mean"),
                                        precision_prom=("precision", "mean"),
                                        tiempo_prom_s=("tiempo_total_s", "mean")).reindex(algorithms)
    alg["tasa_exito"] = alg.exitos / alg.corridas
    insts = inst_order(meta)
    alg["instancias_resueltas"] = [
        int((meta[(meta.algoritmo == x)].groupby("instancia").exito.max() > 0).sum())
        for x in algorithms
    ]
    # Ranking promedio (Friedman) sobre el costo medio por instancia; empates -> rango promedio
    piv = meta.groupby(["instancia", "algoritmo"]).mejor_costo.mean().unstack()[algorithms].loc[insts]
    tpiv = meta.groupby(["instancia", "algoritmo"]).tiempo_total_s.mean().unstack()[algorithms].loc[insts].round(1)  # empates < 0.1 s cuentan como empate
    # desempate por tiempo: rango sobre (costo, tiempo)
    ranks = []
    for inst in insts:
        key = sorted(algorithms, key=lambda x: (piv.loc[inst, x], tpiv.loc[inst, x]))
        r = {}
        for x in algorithms:
            same = [k for k in algorithms if piv.loc[inst, k] == piv.loc[inst, x] and abs(tpiv.loc[inst, k] - tpiv.loc[inst, x]) < 1e-9]
            pos = [key.index(k) + 1 for k in same]
            r[x] = float(np.mean(pos))
        ranks.append(r)
    rk = pd.DataFrame(ranks, index=insts)[algorithms]
    alg["rango_promedio"] = rk.mean().values
    alg.round(4).to_csv(os.path.join(a.results, "resumen_algoritmos.csv"))
    fr = stats.friedmanchisquare(*[rk[x].values for x in algorithms]) if len(algorithms) > 1 else None
    # Wilcoxon pareado: mejor algoritmo vs cada uno (costo de todas las corridas, emparejado por instancia y semilla)
    best = alg["rango_promedio"].idxmin()
    wil = {}
    pv = meta.pivot_table(index=["instancia", "semilla"], columns="algoritmo", values="mejor_costo")
    for x in algorithms:
        if x == best:
            continue
        d = pv[best] - pv[x]
        if (d != 0).sum() == 0:
            wil[x] = {"p": 1.0, "nota": "sin diferencias"}
        else:
            w = stats.wilcoxon(pv[best], pv[x], zero_method="wilcox", alternative="less")
            wil[x] = {"estadistico": float(w.statistic), "p": float(w.pvalue)}
    holm = sorted(wil.items(), key=lambda kv: kv[1]["p"])
    k = len(holm)
    for i, (x, d) in enumerate(holm):
        d["p_holm"] = min(1.0, d["p"] * (k - i))
    st = {"friedman_chi2": None if fr is None else float(fr.statistic),
          "friedman_p": None if fr is None else float(fr.pvalue), "instancias": len(insts),
          "mejor_por_rango": best, "wilcoxon_vs_mejor": wil,
          "rangos_por_instancia": rk.round(2).to_dict()}
    with open(os.path.join(a.results, "estadistica.json"), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=2, ensure_ascii=False)

    # ------------------------------------------------ figuras
    rows = [f"{i} (n={int(df[df.instancia == i].n.iloc[0])})" for i in insts]
    plot_algorithms = algorithms + (["LKH"] if "LKH" in set(df.algoritmo) else [])
    plot_data = df[df.algoritmo.isin(plot_algorithms)]
    plot_groups = plot_data.groupby(["instancia", "algoritmo"])
    success_counts = plot_groups.exito.sum().unstack().reindex(index=insts, columns=plot_algorithms)
    run_counts = plot_groups.exito.size().unstack().reindex(index=insts, columns=plot_algorithms)
    success_fraction = (success_counts / run_counts).values
    success_labels = np.full(success_counts.shape, "—", dtype=object)
    available = run_counts.notna().values
    success_labels[available] = np.vectorize(lambda success, runs: f"{int(success)}/{int(runs)}")(
        success_counts.values[available], run_counts.values[available]
    )
    heatmap_pages(success_fraction, rows, plot_algorithms,
                  "Tasa de éxito: corridas que encontraron el ciclo",
                  os.path.join(figdir, "tasa_exito.png"), lambda v: "", vmax=1.0,
                  labels=success_labels,
                  note=f"Cada celda muestra éxitos/corridas; {t_limit:.0f} s máx. por corrida")
    cost_mean = plot_groups.mejor_costo.mean().unstack().reindex(index=insts, columns=plot_algorithms).values
    heatmap_pages(cost_mean, rows, plot_algorithms,
                  "Aristas faltantes promedio c(π) al terminar (0 = ciclo encontrado)",
                  os.path.join(figdir, "costo_promedio.png"), lambda v: f"{v:.1f}", cmap="Oranges",
                  note="— = algoritmo sin resultados para esa instancia")
    runs = int(meta.groupby(["instancia", "algoritmo"]).size().max())
    for inst in insts:
        if meta[meta.instancia == inst].n.iloc[0] >= 60:
            fname = os.path.join(figdir, f"convergencia_{inst}.png")
            convergence(hist, inst, t_limit, fname, f"Convergencia en {inst}: mediana de {runs} corridas")
    print(alg.round(3).to_string())
    print(json.dumps({k: st[k] for k in ("friedman_chi2", "friedman_p", "mejor_por_rango")}, indent=1))


if __name__ == "__main__":
    main()
