"""Animacion unica con selector de experimentos (base, N0, P, s0, cinetico).

Corre una sola vez y puedes cambiar de experimento en vivo con los controles.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap
from matplotlib.widgets import Button, RadioButtons, Slider

from automata import MicrobialCA
from parametros import articulo_preset

# Ajustes globales del experimento interactivo (tamaños menores para agilidad)
GRID_SIZE = 80
FRAMES = 200
INTERVAL_MS = 100
PATCH_SIZE = 1  # 1 celula en division al centro para forzar arranque

MODOS = ["base", "n0", "prob", "sustrato", "cinetico"]
MODE_COLORS = {
    "base": "tab:blue",
    "n0": "tab:green",
    "prob": "tab:orange",
    "sustrato": "tab:red",
    "cinetico": "tab:purple",
}


def crear_ca(n0: int, prob: float, s0: float) -> MicrobialCA:
    """Crea un CA con un parche central y parametros (N0, P, s0) configurables."""
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
    """Modelo logistico simple usado como referencia poblacional."""
    return k / (1.0 + ((k - x0) / x0) * np.exp(-mu * t))


def main() -> None:
    # Estado mutable del experimento (controla reglas: modo, N0, P, s0).
    state = {
        "modo": "base",
        "n0": 3,
        "prob": 0.5,
        "s0": 60.0,
    }
    anim_running = True

    ca = crear_ca(state["n0"], state["prob"], state["s0"])
    historia: list[int] = []

    fig, (ax_grid, ax_curve) = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={"width_ratios": [1, 1.2]})
    plt.subplots_adjust(left=0.32, right=0.95, bottom=0.23, wspace=0.35)

    cmap_estados = ListedColormap(["black", "blue", "red"])
    im = ax_grid.imshow(ca.grid, cmap=cmap_estados, vmin=0, vmax=2, origin="lower")
    ax_grid.set_title("Automata celular microbiano")
    cbar = fig.colorbar(im, ax=ax_grid, fraction=0.046, pad=0.04)
    cbar.set_label("Estado\n0: vacio, 1: division, 2: crecimiento")

    linea_ca, = ax_curve.plot([], [], marker="o", markersize=4, label="CA", color=MODE_COLORS["base"])
    linea_kin, = ax_curve.plot([], [], label="Modelo cinetico", alpha=0.5, color="gray")
    ax_curve.set_xlim(0, FRAMES)
    ax_curve.set_ylim(0, GRID_SIZE * GRID_SIZE)
    ax_curve.set_xlabel("Paso de tiempo")
    ax_curve.set_ylabel("Celdas vivas (1 y 2)")
    ax_curve.set_title("Selecciona experimento en los controles")
    ax_curve.grid(True)
    ax_curve.legend()

    # Controles para cambiar N0, probabilidad de division y s0 (sustrato inicial).
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
    ax_pause = plt.axes([0.05, 0.10, 0.20, 0.05])
    btn_pause = Button(ax_pause, "Pausar / Reanudar")

    def reset_ca():
        # Reinicia la malla con los parametros actuales del estado (N0, P, s0).
        nonlocal ca, historia
        ca = crear_ca(state["n0"], state["prob"], state["s0"])
        historia = []
        linea_ca.set_data([], [])
        linea_kin.set_data([], [])
        linea_ca.set_color(MODE_COLORS.get(state["modo"], "tab:blue"))
        linea_ca.set_label(f"CA ({state['modo']})")
        ax_curve.set_ylim(0, GRID_SIZE * GRID_SIZE)
        if state["modo"] == "cinetico":
            t = np.arange(FRAMES, dtype=float)
            kin = modelo_cinetico(t, x0=1.0, k=GRID_SIZE * GRID_SIZE * 0.9, mu=0.05)
            linea_kin.set_data(t, kin)
        else:
            linea_kin.set_data([], [])
        ax_curve.set_xlim(0, FRAMES)
        titulo = f"Modo: {state['modo']} | N0={state['n0']} | P={state['prob']} | s0={state['s0']}"
        ax_curve.set_title(titulo)
        # Actualizar leyenda solo con las curvas visibles
        handles = [linea_ca]
        labels = [linea_ca.get_label()]
        if state["modo"] == "cinetico":
            handles.append(linea_kin)
            labels.append(linea_kin.get_label())
        ax_curve.legend(handles, labels)
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
    def on_pause(_event):
        nonlocal anim_running
        anim_running = not anim_running
    btn_pause.on_clicked(on_pause)

    def actualizar(_frame):
        if not anim_running:
            return im, linea_ca, linea_kin
        # Avanza el CA con la regla (N0, P) y actualiza curva de poblacion viva.
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
