from typing import TypeAlias

from backend.models import Escenario


Posicion: TypeAlias = tuple[int, int]


def manhattan_distance(origin: Posicion, target: Posicion) -> int:
    """Calcula la distancia Manhattan entre dos casillas.

    Purpose:
        Estimar los movimientos mínimos entre una posición y un objetivo sin diagonales.
    Preconditions:
        Ambas posiciones deben expresarse como tuplas `(fila, columna)`.
    Postconditions:
        Devuelve un entero no negativo y no modifica ninguna entrada.
    Complexity:
        Tiempo O(1) y espacio O(1).
    AI usage:
        No.
    AI intervention:
        Se propuso la fórmula de distancia para orientar A*.
    Student validation:
        Se probarán posiciones iguales, horizontales, verticales y diagonales.
    """

    return abs(origin[0] - target[0]) + abs(origin[1] - target[1])


def euclidean_distance(origin: Posicion, target: Posicion) -> float:
    """Calcula la distancia Euclidiana entre dos casillas.

    Purpose:
        Estimar la separación geométrica directa entre una posición y un objetivo.
    Preconditions:
        Ambas posiciones deben expresarse como tuplas `(fila, columna)`.
    Postconditions:
        Devuelve un valor real no negativo y no modifica ninguna entrada.
    Complexity:
        Tiempo O(1) y espacio O(1).
    AI usage:
        No.
    AI intervention:
        Se propuso como segunda estrategia heurística para comparar con Manhattan.
    Student validation:
        Se comprobarán posiciones iguales, horizontales, verticales y diagonales.
    """

    row_difference = origin[0] - target[0]
    column_difference = origin[1] - target[1]
    return (row_difference**2 + column_difference**2) ** 0.5


def minimum_traversable_cost(scenario: Escenario) -> float:
    """Obtiene el menor costo de una casilla transitable del escenario.

    Purpose:
        Convertir una distancia geométrica en una cota inferior de costo.
    Preconditions:
        El escenario debe tener al menos un terreno transitable con costo positivo.
    Postconditions:
        Devuelve el menor costo definido en el JSON para terrenos transitables.
    Complexity:
        Tiempo O(t) y espacio O(1), donde t es el número de tipos de terreno.
    AI usage:
        No.
    AI intervention:
        Se añadió para conservar admisibilidad cuando los costos no están normalizados a 1.
    Student validation:
        Se probará con catálogos que contienen costos diferentes.
    """

    costs = [
        terrain.costo
        for terrain in scenario.tipos_terreno.values()
        if terrain.transitable and terrain.costo is not None
    ]
    if not costs:
        raise ValueError("El escenario no tiene terrenos transitables con costo")
    return min(costs)
