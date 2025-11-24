import numpy as np
from typing import Dict, Tuple
from parametros import ParametrosCA


class MicrobialCA:
    """Autómata celular bidimensional para crecimiento microbiano."""

    def __init__(self, params: ParametrosCA):
        self.params = params
        self.rng = np.random.default_rng(self.params.semilla)
        # Distribución inicial basada en la concentración microbiana inicial
        # Mapear x(0) (g/L) -> fracción de ocupación de la malla
        ref = max(1e-6, getattr(self.params, 'referencia_concentracion', 10.0))
        frac = float(self.params.concentracion_microbiana_inicial) / float(ref)
        frac = max(0.0, min(1.0, frac))
        # dividir la fracción ocupada en división/crecimiento (50/50 por defecto)
        p_div = 0.5 * frac
        p_cre = 0.5 * frac
        p_empty = 1.0 - frac
        self.grid = self.rng.choice(
            [0, 1, 2],
            size=(self.params.filas, self.params.columnas),
            p=[p_empty, p_div, p_cre],
        ).astype(np.int8)
        self.sustrato = np.full((self.params.filas, self.params.columnas), self.params.sustrato_inicial, dtype=np.float32)

    def _vecinos_estado(self, estado: int) -> np.ndarray:
        """Cuenta vecinos de Moore en un estado dado usando desplazamientos circulares."""
        g = (self.grid == estado).astype(np.int8)
        total = np.zeros_like(g, dtype=np.int16)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                total += np.roll(np.roll(g, di, axis=0), dj, axis=1)
        return total

    def _difundir_sustrato(self) -> None:
        s = self.sustrato
        kernel_mean = sum(
            np.roll(np.roll(s, di, axis=0), dj, axis=1)
            for di in (-1, 0, 1)
            for dj in (-1, 0, 1)
            if not (di == 0 and dj == 0)
        ) / 8.0
        self.sustrato = s + self.params.difusion * (kernel_mean - s)

    def _consumir_sustrato(self) -> None:
        self.sustrato -= (self.grid == 1) * self.params.consumo_division
        self.sustrato -= (self.grid == 2) * self.params.consumo_crecimiento
        np.clip(self.sustrato, 0, None, out=self.sustrato)

    def step(self, n0: int, prob_div: float) -> Dict[str, int]:
        """Ejecuta un paso temporal y devuelve conteos por estado."""
        # 1) difundir y consumir sustrato
        self._difundir_sustrato()
        self._consumir_sustrato()

        # 2) vecindarios
        vecinos_div = self._vecinos_estado(1)
        vecinos_cre = self._vecinos_estado(2)
        vecinos_total = vecinos_div + vecinos_cre

        grid_old = self.grid.copy()
        nuevo_grid = self.grid.copy()

        # Regla de inhibición espacial: células en división rodeadas pasan a crecimiento
        crowded = vecinos_total > n0
        nuevo_grid[(grid_old == 1) & crowded] = 2

        # División celular cuando no hay hacinamiento y hay sustrato disponible
        can_divide = (grid_old == 1) & (~crowded) & (self.sustrato > self.params.sustrato_minimo)
        positions = np.argwhere(can_divide)
        for i, j in positions:
            # Buscar vecinos vacíos
            vacios = []
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    ni = (i + di) % self.params.filas
                    nj = (j + dj) % self.params.columnas
                    if grid_old[ni, nj] == 0:
                        vacios.append((ni, nj))
            if not vacios:
                continue
            # Escalar probabilidad por sustrato local (Michaelis-Menten like)
            km = getattr(self.params, 'km_sustrato', max(1e-6, self.params.sustrato_inicial / 2.0))
            s_local = float(self.sustrato[i, j])
            prob_eff = float(prob_div) * (s_local / (s_local + km))
            if self.rng.random() < prob_eff:
                ni, nj = vacios[self.rng.integers(len(vacios))]
                nuevo_grid[ni, nj] = 1  # nueva célula en división
                nuevo_grid[i, j] = 2    # célula madre pasa a crecimiento

        # Células en crecimiento pueden volver a división si no hay hacinamiento
        # y hay suficiente sustrato.
        growth_to_div = (
            (grid_old == 2)
            & (vecinos_total <= n0)
            & (self.sustrato > self.params.sustrato_minimo)
        )
        rand_mask = self.rng.random(grid_old.shape)
        # Probabilidad efectiva para crecimiento->division también depende del sustrato local
        km = getattr(self.params, 'km_sustrato', max(1e-6, self.params.sustrato_inicial / 2.0))
        s = self.sustrato
        prob_eff_grid = float(prob_div) * (s / (s + km))
        nuevo_grid[growth_to_div & (rand_mask < prob_eff_grid)] = 1

        # Muerte por inanición ligera (evita crecimiento ilimitado con sustrato 0)
        starvation = (self.sustrato < 0.1) & (nuevo_grid > 0)
        death_mask = self.rng.random(grid_old.shape) < (0.05)
        nuevo_grid[starvation & death_mask] = 0

        self.grid = nuevo_grid

        return {
            'vacios': int((self.grid == 0).sum()),
            'division': int((self.grid == 1).sum()),
            'crecimiento': int((self.grid == 2).sum()),
        }

    def estado_actual(self) -> Tuple[np.ndarray, np.ndarray]:
        return self.grid.copy(), self.sustrato.copy()
