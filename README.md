# Simulacion microbiana basada en automatas celulares
# Autor: Mayerly Julissa Quiñones Quiñones (Trabajo-Maye)
# Universidad Nacional de Colombia - Sede Manizales, Facultad de Ciencias Exactas y Naturales

Repositorio depurado para correr la simulacion interactiva y las rutinas batch. Se removieron documentos y pruebas temporales para dejar una base lista para demostraciones.

## Componentes

- parametros.py: dataclass ParametrosCA, presets y utilidades para guardar/cargar configuraciones.
- automata.py: implementacion del automata MicrobialCA con difusion de sustrato y reglas de inhibicion.
- simulacion.py: ejecutar_simulacion y ResultadoSimulacion para corridas batch.
- visualizacion.py: helpers de graficacion (plot_snapshots, plot_curvas_n0, etc.).
- viewer.py: nueva interfaz con controles agrupados, comparadores y exportacion de datos.
- experiments.py: genera todas las figuras estaticas usadas en el articulo.
- main.py: atajo que ejecuta experiments.py.
- animacion.py: animacion unica con selector de experimentos (base, N0, P, s0, cinetico) sin reiniciar el script.

## Reglas del automata (resumen)

- Estados: 0=vacío, 1=division, 2=crecimiento.
- Vecindad: Moore (8 vecinos) con bordes periodicos (toroidal).
- Inhibicion espacial: si vecinos activos > N0, se bloquea la division.
- Probabilidad de transicion: tabla `PROB_POR_VECINOS` escalada por `prob_div` (valores usados en el articulo: 0.5, 0.25, 0.125) y modulada por sustrato local (`s_min`).
- Reglas: 0 -> 2 (coloniza) si 0 < vecinos <= N0 y random < p_efectiva; 2 -> 1 (activa division) si vecinos <= N0 y random < p_efectiva; 1 -> 2 (fin de division) siempre; sin muerte explicita.
- Sustrato: difusion discreta en vecindad Moore; consumo mayor en estado 1 que en estado 2; inicializado con s0=60 g/L (preset del articulo).
- Inicializacion: x0=6 g/L se mapea a fraccion de ocupacion inicial; semilla fija para reproducibilidad.

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

### Simulacion batch (figuras para el articulo)

    python main.py

### Animacion rapida estilo documento

    python animacion.py

Selector interactivo para ver los diferentes experimentos sin reiniciar (base, N0, P, s0, cinetico).

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
