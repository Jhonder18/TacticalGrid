"""Utilidades de verificación de rutas para búsquedas de navegación.

Este módulo no ejecuta algoritmos: comprueba que un camino ya producido sea
coherente con el escenario. Se usa en pruebas y puede reutilizarse para
diagnóstico sin acoplarse a BFS, DFS, UCS, A* ni Beam Search.
"""

from backend.models import Escenario, ResultadoBusqueda


def verificar_ruta_continua(resultado: ResultadoBusqueda) -> None:
    """Comprueba que cada paso consecutivo sea un movimiento ortogonal simple.

    Purpose:
        Detectar rutas que "salten" casillas o que no sean adyacentes.
    Preconditions:
        `resultado.camino` contiene coordenadas del escenario.
    Postconditions:
        Lanza AssertionError si algún salto no es de distancia Manhattan 1.
    Complexity:
        O(n), donde n es la cantidad de pasos de la ruta.
    AI usage:
        No.
    AI intervention:
        Se propuso comparar posiciones consecutivas por distancia Manhattan.
    Student validation:
        Se probará con rutas válidas y con una ruta alterada artificialmente.
    """

    for actual, siguiente in zip(resultado.camino, resultado.camino[1:]):
        salto = abs(actual.fila - siguiente.fila) + abs(
            actual.columna - siguiente.columna
        )
        assert salto == 1, (
            "La ruta no es continua: "
            f"({actual.fila},{actual.columna}) -> "
            f"({siguiente.fila},{siguiente.columna})"
        )


def verificar_ruta_transitable(
    scenario: Escenario,
    resultado: ResultadoBusqueda,
) -> None:
    """Comprueba que ninguna celda de la ruta sea un obstáculo.

    Purpose:
        Asegurar que la ruta no atraviesa terrenos no transitables.
    Preconditions:
        `scenario` debe estar validado y `resultado.camino` usar sus índices.
    Postconditions:
        Lanza AssertionError si alguna celda está fuera del mapa o es un muro.
    Complexity:
        O(n), donde n es la cantidad de pasos de la ruta.
    AI usage:
        No.
    AI intervention:
        Se propuso reutilizar `tipos_terreno` para consultar transitabilidad.
    Student validation:
        Se probará con una ruta que atraviese un muro y con rutas correctas.
    """

    filas, columnas = scenario.mapa.filas, scenario.mapa.columnas
    for paso in resultado.camino:
        assert 0 <= paso.fila < filas and 0 <= paso.columna < columnas, (
            f"La ruta sale del mapa en ({paso.fila},{paso.columna})"
        )
        terreno = scenario.terreno[paso.fila][paso.columna]
        assert scenario.tipos_terreno[terreno].transitable, (
            f"La ruta atraviesa un obstáculo en ({paso.fila},{paso.columna})"
        )


def recalcular_costo(
    scenario: Escenario,
    resultado: ResultadoBusqueda,
) -> float:
    """Recalcula el costo de la ruta sumando los costos del JSON.

    Purpose:
        Verificar de forma independiente el costo reportado por el algoritmo.
    Preconditions:
        `resultado.camino` debe partir de la posición inicial de la prueba.
    Postconditions:
        Devuelve la suma de costos de las celdas recorridas, sin la inicial.
    Complexity:
        O(n), donde n es la cantidad de pasos de la ruta.
    AI usage:
        No.
    AI intervention:
        Se propuso ignorar la primera celda porque el costo es de transición.
    Student validation:
        Se comparará contra el costo devuelto por UCS y A* en un escenario con
        terrenos de distinto costo.
    """

    total = 0.0
    for paso in resultado.camino[1:]:
        terreno = scenario.terreno[paso.fila][paso.columna]
        costo = scenario.tipos_terreno[terreno].costo
        assert costo is not None
        total += costo
    return total


def verificar_objetivo(
    scenario: Escenario,
    resultado: ResultadoBusqueda,
) -> None:
    """Comprueba que el estado final cumpla el objetivo de la prueba.

    Purpose:
        Asegurar que una búsqueda exitosa termina en `prueba.objetivo`.
    Preconditions:
        `scenario.prueba` debe indicar un objetivo.
    Postconditions:
        Lanza AssertionError si el último paso no coincide con el objetivo.
    Complexity:
        O(1).
    AI usage:
        No.
    AI intervention:
        Se propuso comparar solo el último elemento del camino.
    Student validation:
        Se probará con una ruta que no termine en el objetivo.
    """

    assert scenario.prueba is not None and scenario.prueba.objetivo is not None
    destino = scenario.prueba.objetivo
    ultimo = resultado.camino[-1]
    assert (ultimo.fila, ultimo.columna) == (destino.fila, destino.columna), (
        "La ruta no termina en el objetivo: "
        f"({ultimo.fila},{ultimo.columna}) != ({destino.fila},{destino.columna})"
    )


def verificar_resultado_busqueda(
    scenario: Escenario,
    resultado: ResultadoBusqueda,
) -> None:
    """Aplica todas las verificaciones de integridad sobre una ruta exitosa.

    Purpose:
        Reunir en una sola llamada la continuidad, transitabilidad, costo y
        objetivo para reutilizarla en pruebas de todos los algoritmos.
    Preconditions:
        `resultado.exito` debe ser verdadero y `scenario` estar validado.
    Postconditions:
        Lanza AssertionError en la primera inconsistencia detectada.
    Complexity:
        O(n), donde n es la cantidad de pasos de la ruta.
    AI usage:
        No.
    AI intervention:
        Se propuso una comprobación agregada para evitar duplicar líneas.
    Student validation:
        Se probará con cada algoritmo sobre los Casos 1 a 5.
    """

    assert resultado.exito, "Se esperaba una búsqueda exitosa"
    verificar_ruta_continua(resultado)
    verificar_ruta_transitable(scenario, resultado)
    verificar_objetivo(scenario, resultado)
    costo_recalculado = recalcular_costo(scenario, resultado)
    assert abs(costo_recalculado - resultado.costo) < 1e-9, (
        "El costo reportado no coincide con el recalculado: "
        f"{resultado.costo} != {costo_recalculado}"
    )
    assert resultado.longitud_camino == len(resultado.camino) - 1, (
        "La longitud del camino no coincide con la cantidad de pasos"
    )
