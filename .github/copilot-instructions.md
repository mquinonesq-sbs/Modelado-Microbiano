# Instrucciones para agentes AI (Copilot)

Resumen breve
- **Arquitectura**: conjunto de scripts Python de propósito único. `main.py` orquesta simulaciones y visualizaciones; `simulacion.py` ejecuta la lógica temporal y devuelve un `ResultadoSimulacion`; `automata.py` contiene la implementación del autómata celular (`MicrobialCA`); `parametros.py` centraliza configuraciones y crea `figuras/`; `visualizacion.py` genera imágenes con `matplotlib`.

Qué debes saber antes de cambiar código
- **Estados**: el autómata usa codificación entera: `0` vacío/muerto, `1` división, `2` crecimiento. Evita cambiar esos valores sin propagar cambios en `visualizacion.py` y en conteos de `simulacion.py`.
- **Vecindario**: se usa vecindario de Moore con bordes periódicos (implementado con `np.roll`) en `automata._vecinos_estado`.
- **Sustrato**: difusión y consumo están implementados en `automata._difundir_sustrato` y `_consumir_sustrato`. La variable `sustrato` es un array `float32` con mismo shape que `grid`.
- **Reproducibilidad**: `MicrobialCA` usa `np.random.default_rng(params.semilla)`. Cambiar `semilla` o la forma en que se generan números aleatorios cambia resultados reproducibles.
- **Parámetros centrales**: `ParametrosCA` en `parametros.py` define dimensiones (`filas`, `columnas`), `iteraciones`, `snapshot_horas`, `probabilidades`, `n0_valores`, y consumo/difusión del sustrato. `obtener_parametros()` llama a `asegurar_directorios()`.

Flujo de datos y responsabilidades
- `main.py`: crea `params = obtener_parametros()`, lanza varias ejecuciones de `ejecutar_simulacion(params, n0, prob_div)` y llama a funciones de `visualizacion.py` para guardar figuras en `figuras/`.
- `simulacion.ejecutar_simulacion`: crea `MicrobialCA(params)`, itera `params.iteraciones` pasos llamando `ca.step(...)`, captura snapshots en `params.snapshot_horas` y retorna `ResultadoSimulacion`.
- `visualizacion`: espera `ResultadoSimulacion` con atributos `tiempo`, `division`, `crecimiento`, `vacios`, `sustrato_prom`, `snapshots`. Todas las funciones de plotting reciben `destino: Path` y guardan archivos PNG.

Dependencias y cómo ejecutar
- Requisitos detectables: `numpy`, `matplotlib` (CPython 3.12 es el intérprete usado para los archivos compilados en `__pycache__`).
- Comando típico (desde la raíz del proyecto):

```sh
python main.py
```

Salida esperada: imágenes PNG guardadas en la carpeta `figuras/` (creada por `ParametrosCA.asegurar_directorios`).

Patrones y convenciones específicas del proyecto
- **Objetos de retorno**: las funciones de simulación devuelven el objeto `ResultadoSimulacion` (clase en `simulacion.py`) en lugar de pasar datos sueltos; respeta su API (`concentracion_total()` disponible).
- **Plotting**: las funciones de `visualizacion.py` generan y cierran figuras (`plt.close(fig)`); cuando añadas nuevos plots, sigue este patrón para evitar fugas de memoria en ejecuciones largas.
- **Estructura de archivos**: las figuras se nombran en `main.py` mediante `params.carpeta_figuras() / 'nombre.png'`. Usa `Path` para manipular rutas.

Ejemplos concretos (copiar/pegar)
- Ejecutar una simulación individual:

```py
from parametros import obtener_parametros
from simulacion import ejecutar_simulacion

params = obtener_parametros()
res = ejecutar_simulacion(params, n0=3, prob_div=0.5)
g, s = res.snapshots.get(10), res.sustrato_prom
print(len(res.tiempo), sum(res.concentracion_total()))
```

- Inspeccionar el autómata en caliente (debug):

```py
from parametros import obtener_parametros
from automata import MicrobialCA

params = obtener_parametros()
ca = MicrobialCA(params)
ca.step(n0=3, prob_div=0.5)
grid, sustrato = ca.estado_actual()
print(grid.shape, sustrato.mean())
```

Notas de rendimiento y debugging rápido
- Valores por defecto (`filas=200`, `columnas=200`, `iteraciones=300`) pueden consumir tiempo/memoria; para depurar, reduzca a `filas=50` y `iteraciones=50` en `ParametrosCA` o creando una instancia con valores temporales.
- Para reproducibilidad en pruebas unitarias, fija `semilla` en `ParametrosCA`.

Qué revisar antes de un PR
- Asegurar que no se cambia la codificación de estados sin actualizar `visualizacion.py` y cualquier conteo en `simulacion.py`.
- Mantener la API de `ResultadoSimulacion` (nombres y formatos de campos). Si hace falta cambiar, documenta en el PR y actualiza los plots.

Contacto
- Si algo no está claro, responde a este PR con ejemplos de entrada/salida y pasos para reproducir el comportamiento esperado.

---
Archivo generado automáticamente por un agente para orientar trabajo en este repositorio.
