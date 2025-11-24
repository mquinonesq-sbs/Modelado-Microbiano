from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List
import json


def figuras_dir() -> Path:
    """Carpeta por defecto donde se guardan las figuras/exportes."""
    return Path("figuras")


@dataclass
class ParametrosCA:
    """
    Parametros que controlan el automata celular descrito en el articulo.

    - N0: umbral de vecinos activos (inhibicion espacial) para permitir division.
    - probabilidades: valores probados para la probabilidad base de division.
    - Terminos de sustrato siguen las condiciones iniciales y consumos reportados.
    """

    # Grid y horizonte temporal
    filas: int = 200
    columnas: int = 200
    iteraciones: int = 300
    snapshot_horas: List[int] = field(default_factory=lambda: [1, 5, 10, 30])

    # Estados: 0 vacio/muerto, 1 division, 2 crecimiento
    estados: int = 3

    # REGLA DEL CA: VECINDAD DE MOORE (8 VECINOS) CON INHIBICION ESPACIAL N0.
    # Barridos de probabilidad (P) y umbral espacial (N0)
    probabilidades: List[float] = field(default_factory=lambda: [0.5, 0.25, 0.125])
    n0_valores: List[int] = field(default_factory=lambda: [2, 3, 4])

    # Parametros de sustrato y consumo
    sustrato_inicial: float = 60.0  # g/L, s(0) del articulo
    sustrato_minimo: float = 1.0    # umbral minimo para permitir division
    consumo_division: float = 0.08  # consumo por celula en division
    consumo_crecimiento: float = 0.04  # consumo por celula en crecimiento
    difusion: float = 0.1  # coeficiente de difusion discreta

    # Relacion entre concentracion inicial x(0) y ocupacion de la malla
    concentracion_microbiana_inicial: float = 6.0  # g/L, x(0) del articulo
    referencia_concentracion: float = 10.0  # g/L usado para normalizar x0
    km_sustrato: float = 30.0  # g/L (punto medio para saturacion de probabilidad)

    # Semilla para reproducibilidad
    semilla: int = 42

    def carpeta_figuras(self) -> Path:
        return figuras_dir()

    def asegurar_directorios(self) -> None:
        self.carpeta_figuras().mkdir(parents=True, exist_ok=True)


def obtener_parametros() -> ParametrosCA:
    params = ParametrosCA()
    params.asegurar_directorios()
    return params


def articulo_preset() -> ParametrosCA:
    """
    Devuelve un `ParametrosCA` con los valores y convenciones usados
    en el documento "Articulo 8 microbiano(1).pdf".
    """
    p = ParametrosCA()
    p.filas = 200
    p.columnas = 200
    p.iteraciones = 300
    p.snapshot_horas = [1, 5, 10, 30]
    p.probabilidades = [0.5, 0.25, 0.125]
    p.n0_valores = [2, 3, 4]
    p.sustrato_inicial = 60.0
    p.concentracion_microbiana_inicial = 6.0
    p.asegurar_directorios()
    return p


def save_preset(path: Path, params: ParametrosCA) -> None:
    """Guardar un preset de parametros en formato JSON."""
    d = asdict(params)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


def load_preset(path: Path) -> ParametrosCA:
    """Cargar un preset desde JSON y devolver un ParametrosCA."""
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    p = ParametrosCA()
    for k, v in d.items():
        if hasattr(p, k):
            setattr(p, k, v)
    p.asegurar_directorios()
    return p


def validate_params(params: ParametrosCA) -> tuple[bool, str]:
    """Validacion minima de parametros. Retorna (ok, mensaje)."""
    if params.filas < 10 or params.columnas < 10:
        return False, "Filas/Columnas deben ser >= 10"
    if params.iteraciones < 1:
        return False, "Iteraciones debe ser >= 1"
    if not (0.0 <= params.sustrato_inicial):
        return False, "sustrato_inicial debe ser >= 0"
    return True, "OK"
