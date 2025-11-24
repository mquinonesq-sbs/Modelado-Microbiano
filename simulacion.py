from typing import Dict, List, Tuple
import numpy as np
from automata import MicrobialCA
from parametros import ParametrosCA


class ResultadoSimulacion:
    def __init__(self, tiempo: List[int], division: List[int], crecimiento: List[int], vacios: List[int], sustrato_prom: List[float], snapshots: Dict[int, np.ndarray]):
        self.tiempo = tiempo
        self.division = division
        self.crecimiento = crecimiento
        self.vacios = vacios
        self.sustrato_prom = sustrato_prom
        self.snapshots = snapshots

    def concentracion_total(self) -> List[int]:
        return [d + c for d, c in zip(self.division, self.crecimiento)]


def ejecutar_simulacion(params: ParametrosCA, n0: int, prob_div: float) -> ResultadoSimulacion:
    ca = MicrobialCA(params)
    snapshots: Dict[int, np.ndarray] = {}
    tiempo = []
    division = []
    crecimiento = []
    vacios = []
    sustrato_prom = []

    for t in range(1, params.iteraciones + 1):
        counts = ca.step(n0=n0, prob_div=prob_div)
        g, s = ca.estado_actual()
        if t in params.snapshot_horas:
            snapshots[t] = g
        tiempo.append(t)
        division.append(counts['division'])
        crecimiento.append(counts['crecimiento'])
        vacios.append(counts['vacios'])
        sustrato_prom.append(float(s.mean()))

    return ResultadoSimulacion(
        tiempo=tiempo,
        division=division,
        crecimiento=crecimiento,
        vacios=vacios,
        sustrato_prom=sustrato_prom,
        snapshots=snapshots,
    )
