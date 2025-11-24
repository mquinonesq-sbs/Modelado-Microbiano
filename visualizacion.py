from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np

from parametros import ParametrosCA
from simulacion import ResultadoSimulacion


# Colores asociados a los estados del CA: 0-vacio (blanco), 1-division (azul),
# 2-crecimiento (rojo). Esto facilita interpretar las figuras respecto al articulo.
COLORMAP = {
    0: (1.0, 1.0, 1.0),
    1: (0.2, 0.4, 0.85),
    2: (0.85, 0.2, 0.2),
}


def _state_to_rgb(grid: np.ndarray) -> np.ndarray:
    """Convierte la grilla de estados en una imagen RGB segun COLORMAP."""
    h, w = grid.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)
    for state, color in COLORMAP.items():
        rgb[grid == state] = color
    return rgb


def plot_snapshots(result: ResultadoSimulacion, params: ParametrosCA, n0: int, prob: float, destino: Path) -> None:
    """Grafica el estado espacial en las horas solicitadas (snapshot_horas)."""
    tiempos = sorted(result.snapshots.keys())
    num = len(tiempos)
    fig, axes = plt.subplots(1, num, figsize=(4 * num, 4), constrained_layout=True)
    if num == 1:
        axes = [axes]
    for ax, t in zip(axes, tiempos):
        rgb = _state_to_rgb(result.snapshots[t])
        ax.imshow(rgb, origin="lower")
        ax.set_title(f"t = {t} h")
        ax.axis("off")
    fig.suptitle(f"Distribucion espacial (N0={n0}, P={prob})")
    fig.savefig(str(destino), dpi=200)
    plt.close(fig)


def plot_curvas_n0(resultados: Dict[int, ResultadoSimulacion], params: ParametrosCA, destino: Path) -> None:
    """Curvas de concentracion total para distintos N0 (inhibicion espacial)."""
    fig, ax = plt.subplots(figsize=(7, 4))
    for n0, res in resultados.items():
        ax.plot(res.tiempo, res.concentracion_total(), label=f"N0={n0}")
    ax.set_xlabel("Tiempo (h)")
    ax.set_ylabel("Concentracion microbiana (celdas vivas)")
    ax.set_title("Efecto de la inhibicion espacial (N0)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(str(destino), dpi=200)
    plt.close(fig)


def plot_curvas_prob(resultados: Dict[float, ResultadoSimulacion], params: ParametrosCA, destino: Path, n0: int) -> None:
    """Curvas de concentracion total para distintas probabilidades de division."""
    fig, ax = plt.subplots(figsize=(7, 4))
    for prob, res in resultados.items():
        ax.plot(res.tiempo, res.concentracion_total(), label=f"P={prob}")
    ax.set_xlabel("Tiempo (h)")
    ax.set_ylabel("Concentracion microbiana (celdas vivas)")
    ax.set_title(f"Efecto de la probabilidad de division (N0={n0})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(str(destino), dpi=200)
    plt.close(fig)


def plot_sustrato(res: ResultadoSimulacion, params: ParametrosCA, destino: Path, n0: int, prob: float) -> None:
    """Evolucion temporal del sustrato medio para un N0 y prob_div dados."""
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(res.tiempo, res.sustrato_prom)
    ax.set_xlabel("Tiempo (h)")
    ax.set_ylabel("Concentracion media de sustrato")
    ax.set_title(f"Evolucion del sustrato (N0={n0}, P={prob})")
    fig.tight_layout()
    fig.savefig(str(destino), dpi=200)
    plt.close(fig)
