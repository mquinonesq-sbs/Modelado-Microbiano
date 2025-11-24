"""Animacion unica con selector de experimentos (base, N0, P, s0, cinetico).

Corre una sola vez y puedes cambiar de experimento en vivo con los controles.
"""

from __future__ import annotations

import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap
from matplotlib.widgets import Button, RadioButtons, Slider

from automata import MicrobialCA
from parametros import articulo_preset

# Ajustes globales
GRID_SIZE = 100
FRAMES = 200
INTERVAL_MS = 100
PATCH_SIZE = 1  # 1 celula en division al centro (garantiza expansion)

MODOS = ["base", "n0", "prob", "sustrato", "cinetico"]


def crear_ca(n0: int, prob: float, s0: float) -> MicrobialCA:
    params = articulo_preset()
    params.filas = GRID_SIZE
    params.columnas = GRID_SIZE
    params.iteraciones = FRAMES
    params.sustrato_inicial = s0
    ca = MicrobialCA(params)
    # parche central en division
    ca.grid[:] = 0
    c = GRID_SIZE // 2
    m = PATCH_SIZE // 2
    ca.grid[c - m : c + m + 1, c - m : c + m + 1] = 1
    return ca


def modelo_cinetico(t: np.ndarray, x0: float, k: float, mu: float) -> np.ndarray:
    return k / (1.0 + ((k - x0) / x0) * np.exp(-mu * t))


def main() -> None:
    # Estado mutable del experimento
    state = {
        "modo": "base",
        "n0": 3,
        "prob": 0.5,
        "s0": 60.0,
    }

    ca = crear_ca(state["n0"], state["prob"], state["s0"])
    historia: list[int] = []

    fig, (ax_grid, ax_curve) = plt.subplots(1, 2, figsize=(11, 6))
    plt.subplots_adjust(left=0.30, bottom=0.22)

    cmap_estados = ListedColormap(["black", "blue", "red"])
    im = ax_grid.imshow(ca.grid, cmap=cmap_estados, vmin=0, vmax=2, origin="lower")
    ax_grid.set_title("Automata celular microbiano")
    cbar = plt.colorbar(im, ax=ax_grid)
    cbar.set_label("Estado\n0: vacio, 1: division, 2: crecimiento")

    linea_ca, = ax_curve.plot([], [], marker="o", label="CA")
    linea_kin, = ax_curve.plot([], [], label="Modelo cinetico", alpha=0.5)
    ax_curve.set_xlim(0, FRAMES)
    ax_curve.set_ylim(0, GRID_SIZE * GRID_SIZE)
    ax_curve.set_xlabel("Paso de tiempo")
    ax_curve.set_ylabel("Celdas vivas (1 y 2)")
    ax_curve.set_title("Selecciona experimento en los controles")
    ax_curve.grid(True)
    ax_curve.legend()

    # Controles
    ax_radio = plt.axes([0.05, 0.55, 0.20, 0.35])
    radio = RadioButtons(ax_radio, MODOS, active=0)

    ax_n0 = plt.axes([0.05, 0.40, 0.20, 0.03])
    slider_n0 = Slider(ax_n0, "N0", 2, 4, valinit=state["n0"], valstep=1)

    ax_prob = plt.axes([0.05, 0.33, 0.20, 0.03])
    slider_prob = Slider(ax_prob, "P", 0.125, 0.5, valinit=state["prob"], valstep=0.125)

    ax_s0 = plt.axes([0.05, 0.26, 0.20, 0.03])
    slider_s0 = Slider(ax_s0, "s0", 50.0, 80.0, valinit=state["s0"], valstep=5.0)

    ax_reset = plt.axes([0.05, 0.18, 0.20, 0.05])
    btn_reset = Button(ax_reset, "Aplicar / Reiniciar")

    def reset_ca():
        nonlocal ca, historia
        ca = crear_ca(state["n0"], state["prob"], state["s0"])
        historia = []
        linea_ca.set_data([], [])
        linea_kin.set_data([], [])
        ax_curve.set_ylim(0, GRID_SIZE * GRID_SIZE)
        if state["modo"] == "cinetico":
            t = np.arange(FRAMES, dtype=float)
            kin = modelo_cinetico(t, x0=1.0, k=GRID_SIZE * GRID_SIZE * 0.9, mu=0.05)
            linea_kin.set_data(t, kin)
        fig.canvas.draw_idle()

    def on_radio(label):
        state["modo"] = label
        if label == "base":
            slider_n0.set_val(3)
            slider_prob.set_val(0.5)
            slider_s0.set_val(60.0)
        elif label == "n0":
            slider_n0.set_val(2)
            slider_prob.set_val(0.5)
            slider_s0.set_val(60.0)
        elif label == "prob":
            slider_n0.set_val(3)
            slider_prob.set_val(0.25)
            slider_s0.set_val(60.0)
        elif label == "sustrato":
            slider_n0.set_val(3)
            slider_prob.set_val(0.5)
            slider_s0.set_val(70.0)
        elif label == "cinetico":
            slider_n0.set_val(3)
            slider_prob.set_val(0.5)
            slider_s0.set_val(60.0)
        reset_ca()

    def on_slider(_val):
        state["n0"] = int(slider_n0.val)
        state["prob"] = float(slider_prob.val)
        state["s0"] = float(slider_s0.val)

    def on_reset(_event):
        on_slider(None)
        reset_ca()

    radio.on_clicked(on_radio)
    slider_n0.on_changed(on_slider)
    slider_prob.on_changed(on_slider)
    slider_s0.on_changed(on_slider)
    btn_reset.on_clicked(on_reset)

    def actualizar(_frame):
        counts = ca.step(n0=state["n0"], prob_div=state["prob"])
        vivos = counts["division"] + counts["crecimiento"]
        historia.append(vivos)

        im.set_data(ca.grid)
        x = np.arange(len(historia))
        linea_ca.set_data(x, historia)
        ax_curve.set_xlim(0, max(FRAMES, len(historia)))
        ax_curve.set_ylim(0, max(GRID_SIZE * GRID_SIZE * 0.1, max(historia) * 1.1))
        return im, linea_ca, linea_kin

    # mantener referencia para evitar GC
    anim = FuncAnimation(
        fig,
        actualizar,
        frames=FRAMES,
        interval=INTERVAL_MS,
        blit=True,
    )

    plt.show()


if __name__ == "__main__":
    main()
