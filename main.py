from pathlib import Path
from parametros import obtener_parametros
from simulacion import ejecutar_simulacion
from visualizacion import plot_snapshots, plot_curvas_n0, plot_curvas_prob, plot_sustrato


def main() -> None:
    params = obtener_parametros()

    # Simulación base para snapshots y sustrato
    n0_base = 3
    prob_base = params.probabilidades[0]
    resultado_base = ejecutar_simulacion(params, n0=n0_base, prob_div=prob_base)

    # Guardar como SVG como solución temporal a errores de escritura PNG en este entorno
    plot_snapshots(
        resultado_base,
        params=params,
        n0=n0_base,
        prob=prob_base,
        destino=params.carpeta_figuras() / 'espacial_t1_5_10_30.svg',
    )
    plot_sustrato(
        resultado_base,
        params=params,
        n0=n0_base,
        prob=prob_base,
        destino=params.carpeta_figuras() / 'sustrato_base.svg',
    )

    # Curvas para distintos N0 usando prob_base
    resultados_n0 = {}
    for n0 in params.n0_valores:
        resultados_n0[n0] = ejecutar_simulacion(params, n0=n0, prob_div=prob_base)
    plot_curvas_n0(
        resultados=resultados_n0,
        params=params,
        destino=params.carpeta_figuras() / 'curva_concentracion_n0.svg',
    )

    # Curvas para distintas probabilidades con N0 fijo
    resultados_prob = {}
    for prob in params.probabilidades:
        resultados_prob[prob] = ejecutar_simulacion(params, n0=n0_base, prob_div=prob)
    plot_curvas_prob(
        resultados=resultados_prob,
        params=params,
        destino=params.carpeta_figuras() / 'curva_probabilidades.svg',
        n0=n0_base,
    )

    print('Simulaciones completadas. Figuras guardadas en', params.carpeta_figuras())


if __name__ == '__main__':
    main()
