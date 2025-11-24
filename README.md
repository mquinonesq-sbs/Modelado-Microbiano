
# Simulacion microbiana basada en automatas celulares

Repositorio depurado para correr la simulacion interactiva y las rutinas batch. Se removieron documentos y pruebas temporales para dejar una base lista para demostraciones.

## Componentes

- parametros.py: dataclass ParametrosCA, presets y utilidades para guardar/cargar configuraciones.
- automata.py: implementacion del automata MicrobialCA con difusion de sustrato y reglas de inhibicion.
- simulacion.py: ejecutar_simulacion y ResultadoSimulacion para corridas batch.
- visualizacion.py: helpers de graficacion (plot_snapshots, plot_curvas_n0, etc.).
- viewer.py: nueva interfaz con controles agrupados, comparadores y exportacion de datos.
- main.py: script de ejemplo que genera figuras del preset del articulo.

## Instalacion rapida

    python -m venv .venv
    source .venv/bin/activate    # Windows: .venv\Scripts\activate
    pip install numpy matplotlib Pillow PyPDF2

## Uso

### Visor interactivo

    python viewer.py

- Pantalla principal con mapa espacial, curva de sustrato y poblacion viva.
- Sliders para N0 y probabilidad de division en vivo.
- Botones: Pause/Play, Step, Reset, Apply Grid, Init from x0, Load Article, Save/Load Preset, Export CSV, Open Compare (vista inline) y Compare Window (ventana externa con tres simulaciones).
- Exporta la serie temporal a figuras/historial_viewer.csv para documentar cada demo.

### Simulacion batch

    python main.py

Genera SVG con snapshots y curvas dentro de figuras/.

## Estructura

    Trabajo-Maye/
    - automata.py
    - main.py
    - parametros.py
    - simulacion.py
    - visualizacion.py
    - viewer.py
    - figuras/
    - README.md

## Experimentos sugeridos

1. Load Article + Compare Window para mostrar el efecto de N0.
2. Cambiar x0, Ref y Km y reinicializar con Init from x0.
3. Guardar los resultados de cada sesion con Export CSV.

## Notas

- Se eliminaron tools/, test_*.py, PDFs y PNGs historicos para mantener limpio el repositorio.
- Las figuras y presets personalizados se guardan en figuras/.
