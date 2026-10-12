from collections import deque
from dataclasses import dataclass
from time import perf_counter
from typing import Literal

from backend.core.successors import get_navigation_successors
from backend.models import Coordenada, Escenario, GameState, ResultadoBusqueda


@dataclass(frozen=True, slots=True)
class SearchNode:
    """Guarda un estado y la información necesaria para reconstruir el camino."""

    state: GameState
    parent: "SearchNode | None"
    action: Coordenada | None
    cost: float


def bfs(scenario: Escenario) -> ResultadoBusqueda:
    """Busca un camino con Breadth-First Search usando una cola.

    Purpose:
        Encontrar un camino con el menor número de movimientos en navegación.
    Preconditions:
        `scenario.prueba` debe indicar una unidad de inicio y un objetivo.
    Postconditions:
        Devuelve el camino encontrado y las métricas de exploración, o un resultado sin éxito.
    Complexity:
        Tiempo y memoria O(b^d), donde b es la ramificación y d la profundidad de la solución.
    AI usage:
        No.
    AI intervention:
        Se propuso la estructura de cola, el control de visitados y la reconstrucción del camino.
    Student validation:
        Se validará con escenarios con obstáculos, solución y ausencia de solución.
    """

    return _search(scenario, "BFS")


def dfs(scenario: Escenario) -> ResultadoBusqueda:
    """Busca un camino con Depth-First Search usando una pila.

    Purpose:
        Encontrar una solución explorando primero una rama profunda del espacio.
    Preconditions:
        `scenario.prueba` debe indicar una unidad de inicio y un objetivo.
    Postconditions:
        Devuelve el primer camino encontrado y las métricas de exploración.
    Complexity:
        Tiempo O(b^m) y memoria O(bm), donde m es la profundidad máxima explorada.
    AI usage:
        No.
    AI intervention:
        Se propuso la estructura de pila, el control de visitados y la reconstrucción del camino.
    Student validation:
        Se comparará con BFS en escenarios donde ambas estrategias exploren distinto.
    """

    return _search(scenario, "DFS")


def _search(
    scenario: Escenario,
    algorithm: Literal["BFS", "DFS"],
) -> ResultadoBusqueda:
    unit_id, target = _get_search_configuration(scenario)
    initial_state = GameState.from_scenario(scenario)
    initial_unit = next(
        unidad for unidad in initial_state.unidades if unidad.id == unit_id
    )
    initial_node = SearchNode(
        state=initial_state,
        parent=None,
        action=None,
        cost=0.0,
    )
    frontier: deque[SearchNode] | list[SearchNode]
    if algorithm == "BFS":
        frontier = deque([initial_node])
    else:
        frontier = [initial_node]

    visited = {initial_state}
    generated = 1
    expanded = 0
    max_frontier = 1
    started_at = perf_counter()

    while frontier:
        node = (
            frontier.popleft()
            if algorithm == "BFS"
            else frontier.pop()
        )
        current_position = _unit_position(node.state, unit_id)
        if current_position == target:
            return _build_result(
                algorithm,
                node,
                generated,
                expanded,
                max_frontier,
                perf_counter() - started_at,
                initial_unit.posicion,
            )

        expanded += 1
        successors = get_navigation_successors(
            node.state,
            scenario,
            unit_id,
        )
        ordered_successors = (
            reversed(successors) if algorithm == "DFS" else successors
        )
        for transition in ordered_successors:
            if transition.state in visited:
                continue
            visited.add(transition.state)
            successor = SearchNode(
                state=transition.state,
                parent=node,
                action=transition.action.destino,
                cost=node.cost + transition.cost,
            )
            frontier.append(successor)
            generated += 1

        max_frontier = max(max_frontier, len(frontier))

    return _build_result(
        algorithm,
        None,
        generated,
        expanded,
        max_frontier,
        perf_counter() - started_at,
        initial_unit.posicion,
    )


def _get_search_configuration(
    scenario: Escenario,
) -> tuple[str, tuple[int, int]]:
    if scenario.prueba is None:
        raise ValueError("El escenario no tiene configuración de prueba")
    if scenario.prueba.unidad_inicio is None:
        raise ValueError("La prueba no tiene unidad_inicio")
    if scenario.prueba.objetivo is None:
        raise ValueError("La prueba no tiene objetivo")
    return (
        scenario.prueba.unidad_inicio,
        (scenario.prueba.objetivo.fila, scenario.prueba.objetivo.columna),
    )


def _unit_position(state: GameState, unit_id: str) -> tuple[int, int]:
    for unidad in state.unidades:
        if unidad.id == unit_id:
            return unidad.posicion
    raise ValueError(f"No existe la unidad de búsqueda: {unit_id}")


def _build_result(
    algorithm: Literal["BFS", "DFS"],
    node: SearchNode | None,
    generated: int,
    expanded: int,
    max_frontier: int,
    elapsed: float,
    initial_position: tuple[int, int],
) -> ResultadoBusqueda:
    path = _reconstruct_path(node, initial_position)
    return ResultadoBusqueda(
        algoritmo=algorithm,
        exito=node is not None,
        camino=[Coordenada(fila=fila, columna=columna) for fila, columna in path],
        costo=node.cost if node is not None else 0.0,
        longitud_camino=max(0, len(path) - 1),
        estados_generados=generated,
        estados_expandidos=expanded,
        maximo_frontera=max_frontier,
        tiempo=elapsed,
    )


def _reconstruct_path(
    node: SearchNode | None,
    initial_position: tuple[int, int],
) -> list[tuple[int, int]]:
    if node is None:
        return []

    path: list[tuple[int, int]] = []
    current: SearchNode | None = node
    while current is not None:
        if current.action is not None:
            path.append((current.action.fila, current.action.columna))
        current = current.parent
    path.append(initial_position)
    path.reverse()
    return path
