from typing import TypeAlias


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
