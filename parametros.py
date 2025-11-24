from dataclasses import dataclass, field
from pathlib import Path
from typing import List
import json
from dataclasses import asdict


def figuras_dir() -> Path:
    """Return path to output figures directory."""
    return Path('figuras')


@dataclass
class ParametrosCA:
    # Grid and simulation timing
    filas: int = 200
    columnas: int = 200
    iteraciones: int = 300
    snapshot_horas: List[int] = field(default_factory=lambda: [1, 5, 10, 30])
    
    # States: 0 vacío/muerto, 1 división, 2 crecimiento
    estados: int = 3

    # Probabilidades de división probadas
    probabilidades: List[float] = field(default_factory=lambda: [0.5, 0.25, 0.125])

    # Umbrales de inhibición espacial
    n0_valores: List[int] = field(default_factory=lambda: [2, 3, 4])

    # Parámetros de sustrato
    # sustrato_inicial: concentración inicial de sustrato en g/L (Artículo: 60 g/L)
    sustrato_inicial: float = 60.0  # g/L equivalente inicial (Artículo: s(0)=60 g/L)
    sustrato_minimo: float = 1.0    # umbral mínimo para permitir división
    consumo_division: float = 0.08  # consumo por célula en división
    consumo_crecimiento: float = 0.04  # consumo por célula en crecimiento
    difusion: float = 0.1  # coeficiente de difusión simple

    # Concentración microbiana inicial (artículo: x(0)=6 g/L)
    concentracion_microbiana_inicial: float = 6.0  # g/L (informativo)
    # Referencia para mapear concentración (g/L) -> fracción de ocupación de la malla
    referencia_concentracion: float = 10.0  # g/L (valor usado para normalizar x(0))
    # Constante similar a Michaelis-Menten para dependencia de probabilidad en sustrato
    km_sustrato: float = 30.0  # g/L (por defecto sustrato_inicial / 2)

    # Otros
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
    """Devuelve un objeto `ParametrosCA` con los valores y convenciones usados
    en el documento "Articulo 8 microbiano(1).pdf".

    Valores principales (tal como aparecen en el artículo):
    - Grid: 200 x 200
    - Iteraciones: 300
    - Snapshots: [1, 5, 10, 30] (horas)
    - sustrato_inicial: 60 g/L
    - concentracion_microbiana_inicial: 6 g/L
    - probabilidades: [0.5, 0.25, 0.125]
    - n0_valores: [2, 3, 4]

    Esta función facilita cargar el preset desde la GUI.
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
    """Guardar un preset de parámetros en formato JSON."""
    d = asdict(params)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2)


def load_preset(path: Path) -> ParametrosCA:
    """Cargar un preset desde JSON y devolver un ParametrosCA."""
    with open(path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    # crear ParametrosCA a partir del dict (ignorando claves adicionales)
    p = ParametrosCA()
    for k, v in d.items():
        if hasattr(p, k):
            setattr(p, k, v)
    p.asegurar_directorios()
    return p


def validate_params(params: ParametrosCA) -> tuple[bool, str]:
    """Validación mínima de parametros. Retorna (ok, mensaje)."""
    if params.filas < 10 or params.columnas < 10:
        return False, 'Filas/Columnas deben ser >= 10'
    if params.iteraciones < 1:
        return False, 'Iteraciones debe ser >= 1'
    if not (0.0 <= params.sustrato_inicial):
        return False, 'sustrato_inicial debe ser >= 0'
    return True, 'OK'
