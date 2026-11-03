"""Resume resultados.csv: tablas por instancia y algoritmo, pruebas estadísticas y figuras.

Uso: python analyze.py --results results
Genera en results/: resumen_instancia_algoritmo.csv, resumen_algoritmos.csv,
estadistica.json y figuras/*.png
"""
from __future__ import annotations

import argparse
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


def heatmap(mat, rows, cols, title, fname, fmt, cmap="Blues", note=None, vmax=None):
    fig, ax = plt.subplots(figsize=(1.05 * len(cols) + 2.6, 0.48 * len(rows) + 1.6), dpi=200)
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
                txt = fmt(v)
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
            y = np.where(idx >= 0, cs[np.clip(idx, 0, None)], np.nan)
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
                                        tiempo_prom_s=("tiempo_total_s", "mean")).reindex(ORDER)
    alg["tasa_exito"] = alg.exitos / alg.corridas
    insts = inst_order(meta)
    alg["instancias_resueltas"] = [int((meta[(meta.algoritmo == x)].groupby("instancia").exito.max() > 0).sum()) for x in ORDER]
    # Ranking promedio (Friedman) sobre el costo medio por instancia; empates -> rango promedio
    piv = meta.groupby(["instancia", "algoritmo"]).mejor_costo.mean().unstack()[ORDER].loc[insts]
    tpiv = meta.groupby(["instancia", "algoritmo"]).tiempo_total_s.mean().unstack()[ORDER].loc[insts].round(1)  # empates < 0.1 s cuentan como empate
    # desempate por tiempo: rango sobre (costo, tiempo)
    ranks = []
    for inst in insts:
        key = sorted(ORDER, key=lambda x: (piv.loc[inst, x], tpiv.loc[inst, x]))
        r = {}
        for x in ORDER:
            same = [k for k in ORDER if piv.loc[inst, k] == piv.loc[inst, x] and abs(tpiv.loc[inst, k] - tpiv.loc[inst, x]) < 1e-9]
            pos = [key.index(k) + 1 for k in same]
            r[x] = float(np.mean(pos))
        ranks.append(r)
    rk = pd.DataFrame(ranks, index=insts)[ORDER]
    alg["rango_promedio"] = rk.mean().values
    alg.round(4).to_csv(os.path.join(a.results, "resumen_algoritmos.csv"))
    fr = stats.friedmanchisquare(*[rk[x].values for x in ORDER])
    # Wilcoxon pareado: mejor algoritmo vs cada uno (costo de todas las corridas, emparejado por instancia y semilla)
    best = alg["rango_promedio"].idxmin()
    wil = {}
    pv = meta.pivot_table(index=["instancia", "semilla"], columns="algoritmo", values="mejor_costo")
    for x in ORDER:
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
    st = {"friedman_chi2": float(fr.statistic), "friedman_p": float(fr.pvalue), "instancias": len(insts),
          "mejor_por_rango": best, "wilcoxon_vs_mejor": wil,
          "rangos_por_instancia": rk.round(2).to_dict()}
    with open(os.path.join(a.results, "estadistica.json"), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=2, ensure_ascii=False)

    # ------------------------------------------------ figuras
    rows = [f"{i} (n={int(meta[meta.instancia == i].n.iloc[0])})" for i in insts]
    succ = meta.groupby(["instancia", "algoritmo"]).exito.mean().unstack()[ORDER].loc[insts].values
    runs = int(meta.groupby(["instancia", "algoritmo"]).size().max())
    heatmap(succ, rows, ORDER, "Tasa de éxito: fracción de corridas que encontraron el ciclo",
            os.path.join(figdir, "tasa_exito.png"), lambda v: f"{v * runs:.0f}/{runs}", vmax=1.0,
            note=f"{runs} corridas por celda, {t_limit:.0f} s máx. por corrida")
    cmean = piv.values
    heatmap(cmean, rows, ORDER, "Aristas faltantes promedio c(π) al terminar (0 = ciclo encontrado)",
            os.path.join(figdir, "costo_promedio.png"), lambda v: f"{v:.1f}", cmap="Oranges")
    for inst in insts:
        if meta[meta.instancia == inst].n.iloc[0] >= 60:
            fname = os.path.join(figdir, f"convergencia_{inst}.png")
            convergence(hist, inst, t_limit, fname, f"Convergencia en {inst}: mediana de {runs} corridas")
    print(alg.round(3).to_string())
    print(json.dumps({k: st[k] for k in ("friedman_chi2", "friedman_p", "mejor_por_rango")}, indent=1))


if __name__ == "__main__":
    main()
