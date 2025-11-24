from __future__ import annotations

"""Visor interactivo reorganizado para los experimentos microbiologicos."""

from dataclasses import dataclass
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider, TextBox
import numpy as np
import tkinter as tk
from tkinter import filedialog

from automata import MicrobialCA
from parametros import (
    ParametrosCA,
    articulo_preset,
    load_preset,
    obtener_parametros,
    save_preset,
)
from visualizacion import _state_to_rgb


@dataclass
class History:
    """Series temporales que se grafican en la vista principal."""

    substrate: List[float]
    population: List[int]

    def reset(self) -> None:
        self.substrate.clear()
        self.population.clear()


def compare_n0_window(params: ParametrosCA, prob: float) -> None:
    """Abre una ventana secundaria con tres simulaciones paralelas para N0."""

    n0_values = params.n0_valores[:3] or [2, 3, 4]
    base = MicrobialCA(params)
    clones = []
    for _ in n0_values:
        ca = MicrobialCA(params)
        ca.grid = base.grid.copy()
        ca.sustrato = base.sustrato.copy()
        ca.rng = np.random.default_rng(params.semilla)
        clones.append(ca)

    fig, axes = plt.subplots(len(clones), 2, figsize=(10, 3.2 * len(clones)))
    axes = np.atleast_2d(axes)
    histories = [[] for _ in clones]
    images = []
    lines = []

    for row, (n0, ca) in enumerate(zip(n0_values, clones)):
        ax_grid = axes[row, 0]
        ax_curve = axes[row, 1]
        ax_grid.imshow(_state_to_rgb(ca.grid), origin="lower")
        ax_grid.set_title(f"N0 = {n0}")
        ax_grid.axis("off")
        line, = ax_curve.plot([], [], "-o", markersize=3)
        ax_curve.set_xlabel("Tiempo (h)")
        ax_curve.set_ylabel("Sustrato")
        ax_curve.set_ylim(0, params.sustrato_inicial * 1.2)
        images.append(ax_grid.images[0])
        lines.append(line)

    fig.suptitle("Comparacion simultanea de N0")

    def _update(_frame: int):
        for idx, (n0, ca) in enumerate(zip(n0_values, clones)):
            ca.step(n0=n0, prob_div=prob)
            grid, s = ca.estado_actual()
            histories[idx].append(float(s.mean()))
            images[idx].set_data(_state_to_rgb(grid))
            lines[idx].set_data(range(1, len(histories[idx]) + 1), histories[idx])
            axes[idx, 1].set_xlim(0, max(10, len(histories[idx])))
            axes[idx, 1].set_ylim(0, max(params.sustrato_inicial, max(histories[idx])) * 1.1)
        return images + lines

    FuncAnimation(fig, _update, frames=range(params.iteraciones), interval=250, blit=False, repeat=False)
    plt.show(block=False)


class ViewerApp:
    """Controla la interfaz y los flujos de simulacion."""

    def __init__(self, params: ParametrosCA, n0: int, prob: float):
        self.params = params
        self.ca = MicrobialCA(self.params)
        self.current_n0 = n0
        self.current_prob = prob
        self.history = History([], [])
        self.fig = plt.figure(figsize=(13, 8))
        gs = self.fig.add_gridspec(
            2,
            2,
            left=0.05,
            right=0.70,
            top=0.90,
            bottom=0.32,
            hspace=0.28,
            wspace=0.18,
        )
        self.ax_grid = self.fig.add_subplot(gs[:, 0])
        self.ax_substrate = self.fig.add_subplot(gs[0, 1])
        self.ax_population = self.fig.add_subplot(gs[1, 1])
        self.grid_im = None
        self.substrate_line = None
        self.population_line = None
        self.animation: FuncAnimation | None = None
        self.running = True
        self._compare_enabled = False
        self._compare_timer = None
        self._build_main_axes()
        self._build_widgets()
        self._start_animation()

    def _build_main_axes(self) -> None:
        grid, _ = self.ca.estado_actual()
        self.grid_im = self.ax_grid.imshow(_state_to_rgb(grid), origin="lower")
        self.ax_grid.set_title("Estado espacial")
        self.ax_grid.axis("off")

        self.substrate_line, = self.ax_substrate.plot([], [], "-o", markersize=3)
        self.ax_substrate.set_xlabel("Tiempo (h)")
        self.ax_substrate.set_ylabel("Sustrato medio (g/L)")
        self.ax_substrate.set_ylim(0, self.params.sustrato_inicial * 1.2)

        self.population_line, = self.ax_population.plot([], [], "-o", color="#ff7f0e")
        self.ax_population.set_xlabel("Tiempo (h)")
        self.ax_population.set_ylabel("Celdas vivas (1+2)")

    def _build_widgets(self) -> None:
        self.widgets: dict[str, object] = {}

        def btn(x: float, y: float, label: str, w: float = 0.12, h: float = 0.05) -> Button:
            return Button(self.fig.add_axes([x, y, w, h]), label)

        # Fila 1: controles principales
        self.widgets["btn_play"] = btn(0.05, 0.26, "Pause")
        self.widgets["btn_step"] = btn(0.19, 0.26, "Step")
        self.widgets["btn_reset"] = btn(0.33, 0.26, "Reset")
        self.widgets["btn_apply"] = btn(0.47, 0.26, "Apply Grid", w=0.14)
        self.widgets["btn_init"] = btn(0.63, 0.26, "Init from x0", w=0.14)
        self.widgets["btn_compare"] = btn(0.79, 0.26, "Open Compare", w=0.16)

        # Fila 2: presets y exportacion
        self.widgets["btn_load_article"] = btn(0.05, 0.19, "Load Article", w=0.14)
        self.widgets["btn_save_preset"] = btn(0.21, 0.19, "Save Preset", w=0.14)
        self.widgets["btn_load_preset"] = btn(0.37, 0.19, "Load Preset", w=0.14)
        self.widgets["btn_export"] = btn(0.53, 0.19, "Export CSV", w=0.14)
        self.widgets["btn_compare_win"] = btn(0.69, 0.19, "Compare Window", w=0.18)

        # Sliders
        self.widgets["slider_n0"] = Slider(self.fig.add_axes([0.05, 0.12, 0.38, 0.035]), "N0", 0, 10, valinit=self.current_n0, valstep=1)
        self.widgets["slider_prob"] = Slider(self.fig.add_axes([0.50, 0.12, 0.38, 0.035]), "Prob", 0.0, 1.0, valinit=self.current_prob, valstep=0.01)

        # TextBoxes filas/columnas/iter y x0/ref/km
        self.widgets["tb_filas"] = TextBox(self.fig.add_axes([0.05, 0.06, 0.10, 0.04]), "Filas", initial=str(self.params.filas))
        self.widgets["tb_cols"] = TextBox(self.fig.add_axes([0.17, 0.06, 0.10, 0.04]), "Columnas", initial=str(self.params.columnas))
        self.widgets["tb_iter"] = TextBox(self.fig.add_axes([0.29, 0.06, 0.10, 0.04]), "Iter", initial=str(self.params.iteraciones))
        self.widgets["tb_x0"] = TextBox(self.fig.add_axes([0.41, 0.06, 0.10, 0.04]), "x0 (g/L)", initial=str(self.params.concentracion_microbiana_inicial))
        self.widgets["tb_ref"] = TextBox(self.fig.add_axes([0.53, 0.06, 0.10, 0.04]), "Ref (g/L)", initial=str(self.params.referencia_concentracion))
        self.widgets["tb_km"] = TextBox(self.fig.add_axes([0.65, 0.06, 0.10, 0.04]), "Km", initial=str(self.params.km_sustrato))

        self.widgets["btn_play"].on_clicked(self._toggle_play)
        self.widgets["btn_step"].on_clicked(self._step_once)
        self.widgets["btn_reset"].on_clicked(self._reset)
        self.widgets["btn_apply"].on_clicked(self._apply_grid)
        self.widgets["btn_init"].on_clicked(self._init_from_x0)
        self.widgets["btn_compare"].on_clicked(self._toggle_inline_compare)
        self.widgets["btn_load_article"].on_clicked(self._load_article)
        self.widgets["btn_save_preset"].on_clicked(lambda _evt: self._save_preset())
        self.widgets["btn_load_preset"].on_clicked(lambda _evt: self._load_preset())
        self.widgets["btn_export"].on_clicked(lambda _evt: self._export_csv())
        self.widgets["btn_compare_win"].on_clicked(lambda _evt: compare_n0_window(self.params, self.current_prob))
        self.widgets["slider_n0"].on_changed(self._set_n0)
        self.widgets["slider_prob"].on_changed(self._set_prob)

    def _start_animation(self) -> None:
        if self.animation is not None:
            self.animation.event_source.stop()
        self.animation = FuncAnimation(self.fig, self._update_frame, frames=range(self.params.iteraciones), interval=200, blit=False, repeat=False)

    def _update_frame(self, _frame: int):
        if not self.running:
            return self.grid_im, self.substrate_line, self.population_line
        self._perform_step()
        return self.grid_im, self.substrate_line, self.population_line

    def _perform_step(self) -> None:
        counts = self.ca.step(self.current_n0, self.current_prob)
        grid, sustrato = self.ca.estado_actual()
        self.history.substrate.append(float(sustrato.mean()))
        self.history.population.append(int(counts["division"] + counts["crecimiento"]))
        step_idx = len(self.history.substrate)
        self.grid_im.set_data(_state_to_rgb(grid))
        self.substrate_line.set_data(range(1, step_idx + 1), self.history.substrate)
        self.population_line.set_data(range(1, step_idx + 1), self.history.population)
        self.ax_substrate.set_xlim(0, max(10, step_idx))
        self.ax_population.set_xlim(0, max(10, step_idx))
        self.ax_substrate.set_ylim(0, max(self.params.sustrato_inicial, max(self.history.substrate)) * 1.1)
        self.ax_population.set_ylim(0, max(10, max(self.history.population, default=0)) * 1.1)
        self.fig.suptitle(
            f"t={step_idx} | N0={self.current_n0} | Prob={self.current_prob:.2f} | vacios={counts['vacios']} | div={counts['division']} | cre={counts['crecimiento']}"
        )
        self.fig.canvas.draw_idle()

    def _toggle_play(self, _evt) -> None:
        self.running = not self.running
        label = "Pause" if self.running else "Play"
        self.widgets["btn_play"].label.set_text(label)

    def _step_once(self, _evt) -> None:
        was_running = self.running
        self.running = False
        self.widgets["btn_play"].label.set_text("Play")
        self._perform_step()
        self.running = was_running

    def _reset(self, _evt) -> None:
        self.ca = MicrobialCA(self.params)
        self.history.reset()
        grid, _ = self.ca.estado_actual()
        self.grid_im.set_data(_state_to_rgb(grid))
        self.substrate_line.set_data([], [])
        self.population_line.set_data([], [])
        self.fig.suptitle("Simulacion reiniciada")
        self.fig.canvas.draw_idle()

    def _apply_grid(self, _evt) -> None:
        try:
            filas = int(self.widgets["tb_filas"].text)
            columnas = int(self.widgets["tb_cols"].text)
            iteraciones = int(self.widgets["tb_iter"].text)
        except ValueError:
            self.fig.suptitle("Grid invalido: use enteros")
            return
        if filas < 10 or columnas < 10 or iteraciones < 1:
            self.fig.suptitle("Grid debe ser >=10x10 e iter>=1")
            return
        self.params = ParametrosCA(
            filas=filas,
            columnas=columnas,
            iteraciones=iteraciones,
            snapshot_horas=self.params.snapshot_horas,
            probabilidades=self.params.probabilidades,
            n0_valores=self.params.n0_valores,
            sustrato_inicial=self.params.sustrato_inicial,
            sustrato_minimo=self.params.sustrato_minimo,
            consumo_division=self.params.consumo_division,
            consumo_crecimiento=self.params.consumo_crecimiento,
            difusion=self.params.difusion,
            concentracion_microbiana_inicial=self.params.concentracion_microbiana_inicial,
            referencia_concentracion=self.params.referencia_concentracion,
            km_sustrato=self.params.km_sustrato,
            semilla=self.params.semilla,
        )
        self.params.asegurar_directorios()
        self._reset(None)
        self._start_animation()
        self.fig.suptitle(f"Nueva malla: {filas}x{columnas}, iter={iteraciones}")

    def _init_from_x0(self, _evt) -> None:
        try:
            x0 = float(self.widgets["tb_x0"].text)
            ref = float(self.widgets["tb_ref"].text)
            km = float(self.widgets["tb_km"].text)
        except ValueError:
            self.fig.suptitle("x0/ref/km invalidos")
            return
        self.params.concentracion_microbiana_inicial = x0
        self.params.referencia_concentracion = ref
        self.params.km_sustrato = km
        self._reset(None)
        self.fig.suptitle(f"x0 inicializado en {x0} g/L (ref={ref}, Km={km})")

    def _toggle_inline_compare(self, _evt) -> None:
        self._compare_enabled = not self._compare_enabled
        label = "Close Compare" if self._compare_enabled else "Open Compare"
        self.widgets["btn_compare"].label.set_text(label)
        if self._compare_enabled:
            self._ensure_inline_compare()
        else:
            self._hide_inline_compare()

    def _ensure_inline_compare(self) -> None:
        self._compare_axes = []
        top = 0.88
        height = 0.16
        for idx, n0 in enumerate(self.params.n0_valores[:3]):
            ax = self.fig.add_axes([0.74, top - idx * (height + 0.02), 0.22, height])
            ax.axis("off")
            ax.set_title(f"N0={n0}")
            self._compare_axes.append((ax, MicrobialCA(self.params)))
        self._compare_timer = self.fig.canvas.new_timer(interval=400, callbacks=[(self._step_inline_compare, [], {})])
        self._compare_timer.start()

    def _hide_inline_compare(self) -> None:
        if getattr(self, "_compare_axes", None):
            for ax, _ in self._compare_axes:
                ax.remove()
        self._compare_axes = []
        if self._compare_timer is not None:
            self._compare_timer.stop()
            self._compare_timer = None
        self.fig.canvas.draw_idle()

    def _step_inline_compare(self) -> None:
        if not self._compare_axes:
            return
        for (ax, ca), n0 in zip(self._compare_axes, self.params.n0_valores[: len(self._compare_axes)]):
            ca.step(n0=n0, prob_div=self.current_prob)
            grid, _ = ca.estado_actual()
            ax.imshow(_state_to_rgb(grid), origin="lower")
            ax.figure.canvas.draw_idle()

    def _set_n0(self, value: float) -> None:
        self.current_n0 = int(round(value))

    def _set_prob(self, value: float) -> None:
        self.current_prob = float(value)

    def _load_article(self, _evt) -> None:
        art = articulo_preset()
        self.widgets["tb_filas"].set_val(str(art.filas))
        self.widgets["tb_cols"].set_val(str(art.columnas))
        self.widgets["tb_iter"].set_val(str(art.iteraciones))
        self.widgets["tb_x0"].set_val(str(art.concentracion_microbiana_inicial))
        self.widgets["tb_ref"].set_val(str(art.referencia_concentracion))
        self.widgets["tb_km"].set_val(str(art.km_sustrato))
        self.widgets["slider_prob"].set_val(art.probabilidades[0])
        self.widgets["slider_n0"].set_val(art.n0_valores[1] if len(art.n0_valores) > 1 else art.n0_valores[0])
        self._apply_grid(None)

    def _save_preset(self) -> None:
        root = tk.Tk()
        root.withdraw()
        fname = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if fname:
            save_preset(Path(fname), self.params)
            self.fig.suptitle(f"Preset guardado en {fname}")
        root.destroy()

    def _load_preset(self) -> None:
        root = tk.Tk()
        root.withdraw()
        fname = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if fname:
            new_params = load_preset(Path(fname))
            self.params = new_params
            self.widgets["tb_filas"].set_val(str(new_params.filas))
            self.widgets["tb_cols"].set_val(str(new_params.columnas))
            self.widgets["tb_iter"].set_val(str(new_params.iteraciones))
            self.widgets["tb_x0"].set_val(str(new_params.concentracion_microbiana_inicial))
            self.widgets["tb_ref"].set_val(str(new_params.referencia_concentracion))
            self.widgets["tb_km"].set_val(str(new_params.km_sustrato))
            self.widgets["slider_prob"].set_val(new_params.probabilidades[0])
            self.widgets["slider_n0"].set_val(new_params.n0_valores[0])
            self._reset(None)
            self.fig.suptitle(f"Preset cargado: {fname}")
        root.destroy()

    def _export_csv(self) -> None:
        destino = self.params.carpeta_figuras() / "historial_viewer.csv"
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", encoding="utf-8") as fh:
            fh.write("paso,sustrato,poblacion\n")
            for idx, (s, p) in enumerate(zip(self.history.substrate, self.history.population), start=1):
                fh.write(f"{idx},{s},{p}\n")
        self.fig.suptitle(f"Historial exportado a {destino}")


def main(n0: int = 3, prob: float | None = None) -> None:
    params = obtener_parametros()
    if prob is None:
        prob = params.probabilidades[0]
    ViewerApp(params, n0=n0, prob=prob)
    plt.show()


if __name__ == "__main__":
    main()
