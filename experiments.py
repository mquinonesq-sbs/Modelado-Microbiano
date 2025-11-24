"""Genera todas las figuras estaticas usadas en el articulo."""

from __future__ import annotations

from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt
import numpy as np

from parametros import articulo_preset
from simulacion import ejecutar_simulacion
from visualizacion import plot_curvas_n0, plot_curvas_prob, plot_snapshots, plot_sustrato


def _plot_concentracion(res, titulo: str, destino: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(res.tiempo, res.concentracion_total(), label="CA")
    ax.set_xlabel("Tiempo (h)")
    ax.set_ylabel("Celdas vivas (1 y 2)")
    ax.set_title(titulo)
    ax.legend()
    fig.tight_layout()
    fig.savefig(destino, dpi=200)
    plt.close(fig)


def run_experimentos() -> None:
    params = articulo_preset()
    # Configuracion rapida para generar figuras sin demoras largas
    params.filas = 80
    params.columnas = 80
    params.iteraciones = 150

    # Base: snapshots, sustrato, curva de concentracion
    n0_base = 3
    prob_base = params.probabilidades[0]
    res_base = ejecutar_simulacion(params, n0=n0_base, prob_div=prob_base)

    plot_snapshots(
        res_base,
        params=params,
        n0=n0_base,
        prob=prob_base,
        destino=params.carpeta_figuras() / "exp_base_snapshots.png",
    )
    plot_sustrato(
        res_base,
        params=params,
        n0=n0_base,
        prob=prob_base,
        destino=params.carpeta_figuras() / "exp_base_sustrato.png",
    )
    _plot_concentracion(
        res_base,
        titulo="Evolucion base (N0=3, P=0.5)",
        destino=params.carpeta_figuras() / "exp_base_concentracion.png",
    )

    # Barrido de N0
    resultados_n0: Dict[int, object] = {}
    for n0 in params.n0_valores:
        resultados_n0[n0] = ejecutar_simulacion(params, n0=n0, prob_div=prob_base)
    plot_curvas_n0(
        resultados=resultados_n0,
        params=params,
        destino=params.carpeta_figuras() / "exp_n0_curvas.png",
    )

    # Barrido de probabilidad con N0 fijo
    resultados_prob: Dict[float, object] = {}
    for prob in params.probabilidades:
        resultados_prob[prob] = ejecutar_simulacion(params, n0=n0_base, prob_div=prob)
    plot_curvas_prob(
        resultados=resultados_prob,
        params=params,
        destino=params.carpeta_figuras() / "exp_prob_curvas.png",
        n0=n0_base,
    )

    # Efecto de sustrato inicial
    s0_vals = [60.0, 70.0]
    curvas_s: Dict[float, tuple[list[int], list[int]]] = {}
    for s0 in s0_vals:
        params.sustrato_inicial = s0
        res_s = ejecutar_simulacion(params, n0=n0_base, prob_div=prob_base)
        curvas_s[s0] = (res_s.tiempo, res_s.concentracion_total())
    fig, ax = plt.subplots(figsize=(7, 4))
    for s0, (t, conc) in curvas_s.items():
        ax.plot(t, conc, label=f"s0={s0}")
    ax.set_xlabel("Tiempo (h)")
    ax.set_ylabel("Celdas vivas (1 y 2)")
    ax.set_title("Efecto del sustrato inicial")
    ax.legend()
    fig.tight_layout()
    fig.savefig(params.carpeta_figuras() / "exp_sustrato_curvas.png", dpi=200)
    plt.close(fig)

    # Comparacion con modelo cinetico simple (logistica)
    t = np.array(res_base.tiempo, dtype=float)
    ca_curve = np.array(res_base.concentracion_total(), dtype=float)
    x0 = max(1.0, ca_curve[0])
    k = float(max(ca_curve))
    mu = 0.05
    kin_curve = k / (1.0 + ((k - x0) / x0) * np.exp(-mu * t))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(t, ca_curve, label="CA")
    ax.plot(t, kin_curve, label="Modelo cinetico")
    ax.set_xlabel("Tiempo (h)")
    ax.set_ylabel("Celdas vivas (1 y 2)")
    ax.set_title("CA vs modelo cinetico (aprox.)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(params.carpeta_figuras() / "exp_cinetico.png", dpi=200)
    plt.close(fig)

    print("Experimentos listos en", params.carpeta_figuras())


if __name__ == "__main__":
    run_experimentos()
