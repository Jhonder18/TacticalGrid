from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Literal

from backend.algorithms.heuristics import (
    euclidean_distance,
    manhattan_distance,
    minimum_traversable_cost,
)
from backend.core.successors import Transition, get_navigation_successors, get_successors
from backend.models import Escenario, GameState
from backend.models.game_state import UnidadEstado


GameAlgorithm = Literal[
    "BFS",
    "DFS",
    "UCS",
    "A_ESTRELLA",
    "BEAM_SEARCH",
]
Heuristic = Literal["MANHATTAN", "EUCLIDEA"]


@dataclass(frozen=True, slots=True)
class PlannedAction:
    transition: Transition
    steps: int
    cost: float
    priority: float


@dataclass(frozen=True, slots=True)
class _Node:
    state: GameState
    transition: Transition | None
    parent: "_Node | None"
    cost: float
    depth: int


def choose_turn_transition(
    state: GameState,
    scenario: Escenario,
    algorithm: GameAlgorithm,
    heuristic: Heuristic = "MANHATTAN",
    beam_width: int = 4,
) -> Transition:
    """Choose the next action for the active side without client input."""

    if algorithm not in {"BFS", "DFS", "UCS", "A_ESTRELLA", "BEAM_SEARCH"}:
        raise ValueError(f"Algoritmo de partida no soportado: {algorithm}")
    if heuristic not in {"MANHATTAN", "EUCLIDEA"}:
        raise ValueError(f"Heurística no soportada: {heuristic}")
    if beam_width <= 0:
        raise ValueError("El ancho de Beam Search debe ser positivo")

    transitions = get_successors(state, scenario)
    if not transitions:
        raise ValueError("No hay acciones legales para el turno actual")

    plans: list[PlannedAction] = []
    carrier = next(
        (unit for unit in state.unidades if unit.id == state.portador_recurso),
        None,
    )
    forced_unit_id = (
        carrier.id
        if carrier is not None and carrier.bando == state.turno
        else None
    )
    for unit in state.unidades:
        if unit.bando != state.turno:
            continue
        if forced_unit_id is not None and unit.id != forced_unit_id:
            continue
        target = _target_for_unit(state, scenario, unit)
        plan = _plan_for_unit(
            state,
            scenario,
            unit.id,
            target,
                state.portador_recurso is not None
                and carrier is not None
                and carrier.bando != unit.bando,
                algorithm,
                heuristic,
                beam_width,
        )
        if plan is not None:
            plans.append(plan)

    if plans:
        progressing_plans = [
            plan for plan in plans
            if _is_progressing_transition(plan.transition, state, scenario)
        ]
        if progressing_plans:
            return min(
                progressing_plans,
                key=lambda plan: (plan.priority, plan.steps, plan.cost),
            ).transition

    fallback_transitions = (
        tuple(
            transition for transition in transitions
            if transition.action.unidad_id == forced_unit_id
        )
        if forced_unit_id is not None
        else transitions
    )
    return min(
        fallback_transitions or transitions,
        key=lambda transition: _distance_to_target(
            transition.state,
            scenario,
            transition.action.unidad_id,
        ),
    )


def _target_for_unit(
    state: GameState,
    scenario: Escenario,
    unit: UnidadEstado,
) -> tuple[int, int]:
    unit_id = unit.id
    if state.portador_recurso == unit_id:
        base = scenario.bases.A if unit.bando == "A" else scenario.bases.B
        return base.fila, base.columna
    if state.portador_recurso is not None:
        carrier = next(
            current
            for current in state.unidades
            if current.id == state.portador_recurso
        )
        if carrier.bando != unit.bando:
            return carrier.posicion
        base = scenario.bases.A if unit.bando == "A" else scenario.bases.B
        return base.fila, base.columna
    if state.posicion_recurso is None:
        raise ValueError("El estado no tiene objetivo para el turno")
    return state.posicion_recurso


def _plan_for_unit(
    state: GameState,
    scenario: Escenario,
    unit_id: str,
    target: tuple[int, int],
    intercepting: bool,
    algorithm: GameAlgorithm,
    heuristic: Heuristic,
    beam_width: int,
) -> PlannedAction | None:
    initial = _Node(state, None, None, 0.0, 0)
    if _target_reached(state, unit_id, target, intercepting):
        return None

    if algorithm in {"BFS", "DFS"}:
        return _uninformed_plan(
            initial,
            scenario,
            unit_id,
            target,
            intercepting,
            algorithm,
        )
    if algorithm == "UCS":
        return _ucs_plan(initial, scenario, unit_id, target, intercepting)
    if algorithm == "A_ESTRELLA":
        return _a_star_plan(
            initial, scenario, unit_id, target, intercepting, heuristic
        )
    return _beam_plan(
        initial,
        scenario,
        unit_id,
        target,
        intercepting,
        beam_width,
    )


def _uninformed_plan(
    initial: _Node,
    scenario: Escenario,
    unit_id: str,
    target: tuple[int, int],
    intercepting: bool,
    algorithm: Literal["BFS", "DFS"],
) -> PlannedAction | None:
    frontier: deque[_Node] | list[_Node] = deque([initial]) if algorithm == "BFS" else [initial]
    visited = {initial.state}
    while frontier:
        node = frontier.popleft() if algorithm == "BFS" else frontier.pop()
        if _target_reached(node.state, unit_id, target, intercepting):
            return _to_plan(node)
        successors = get_navigation_successors(node.state, scenario, unit_id)
        ordered = reversed(successors) if algorithm == "DFS" else successors
        for transition in ordered:
            if transition.state in visited:
                continue
            visited.add(transition.state)
            child = _Node(
                transition.state,
                transition,
                node,
                node.cost + transition.cost,
                node.depth + 1,
            )
            frontier.append(child)
    return None


def _ucs_plan(
    initial: _Node,
    scenario: Escenario,
    unit_id: str,
    target: tuple[int, int],
    intercepting: bool,
) -> PlannedAction | None:
    frontier: list[tuple[float, int, _Node]] = [(0.0, 0, initial)]
    best_costs = {initial.state: 0.0}
    sequence = 0
    while frontier:
        cost, _, node = heappop(frontier)
        if cost != best_costs.get(node.state):
            continue
        if _target_reached(node.state, unit_id, target, intercepting):
            return _to_plan(node)
        for transition in get_navigation_successors(node.state, scenario, unit_id):
            next_cost = node.cost + transition.cost
            if next_cost >= best_costs.get(transition.state, float("inf")):
                continue
            best_costs[transition.state] = next_cost
            sequence += 1
            heappush(
                frontier,
                (
                    next_cost,
                    sequence,
                    _Node(
                        transition.state,
                        transition,
                        node,
                        next_cost,
                        node.depth + 1,
                    ),
                ),
            )
    return None


def _a_star_plan(
    initial: _Node,
    scenario: Escenario,
    unit_id: str,
    target: tuple[int, int],
    intercepting: bool,
    heuristic: Heuristic,
) -> PlannedAction | None:
    minimum_cost = minimum_traversable_cost(scenario)
    frontier: list[tuple[float, int, _Node]] = [
        (_estimate(_unit_position(initial.state, unit_id), target, heuristic, minimum_cost), 0, initial)
    ]
    best_costs = {initial.state: 0.0}
    sequence = 0
    while frontier:
        _, _, node = heappop(frontier)
        if node.cost != best_costs.get(node.state):
            continue
        if _target_reached(node.state, unit_id, target, intercepting):
            return _to_plan(node)
        for transition in get_navigation_successors(node.state, scenario, unit_id):
            next_cost = node.cost + transition.cost
            if next_cost >= best_costs.get(transition.state, float("inf")):
                continue
            best_costs[transition.state] = next_cost
            sequence += 1
            position = _unit_position(transition.state, unit_id)
            heappush(
                frontier,
                (
                    next_cost + _estimate(position, target, heuristic, minimum_cost),
                    sequence,
                    _Node(
                        transition.state,
                        transition,
                        node,
                        next_cost,
                        node.depth + 1,
                    ),
                ),
            )
    return None


def _beam_plan(
    initial: _Node,
    scenario: Escenario,
    unit_id: str,
    target: tuple[int, int],
    intercepting: bool,
    beam_width: int,
) -> PlannedAction | None:
    frontier = [initial]
    visited = {initial.state}
    while frontier:
        candidates: list[_Node] = []
        for node in frontier:
            if _target_reached(node.state, unit_id, target, intercepting):
                return _to_plan(node)
            for transition in get_navigation_successors(node.state, scenario, unit_id):
                if transition.state in visited:
                    continue
                visited.add(transition.state)
                candidates.append(
                    _Node(
                        transition.state,
                        transition,
                        node,
                        node.cost + transition.cost,
                        node.depth + 1,
                    )
                )
        candidates.sort(
            key=lambda node: (
                manhattan_distance(_unit_position(node.state, unit_id), target),
                node.cost,
            )
        )
        frontier = candidates[:beam_width]
    return None


def _to_plan(node: _Node) -> PlannedAction:
    first = node
    while first.parent is not None and first.parent.parent is not None:
        first = first.parent
    if first.transition is None:
        raise ValueError("El plan no contiene una acción")
    return PlannedAction(
        transition=first.transition,
        steps=node.depth,
        cost=node.cost,
        priority=float(node.depth),
    )


def _unit_position(state: GameState, unit_id: str) -> tuple[int, int]:
    return next(unit.posicion for unit in state.unidades if unit.id == unit_id)


def _distance_to_target(
    state: GameState,
    scenario: Escenario,
    unit_id: str,
) -> float:
    unit = next(unit for unit in state.unidades if unit.id == unit_id)
    target = _target_for_unit(state, scenario, unit)
    distance = manhattan_distance(unit.posicion, target)
    if state.portador_recurso is not None:
        carrier = next(
            current
            for current in state.unidades
            if current.id == state.portador_recurso
        )
        if carrier.bando != unit.bando:
            return max(0, distance - 1)
    return distance


def _target_reached(
    state: GameState,
    unit_id: str,
    target: tuple[int, int],
    intercepting: bool,
) -> bool:
    if intercepting and state.portador_recurso == unit_id:
        return True
    unit = next(current for current in state.unidades if current.id == unit_id)
    if (
        state.portador_recurso is not None
        and state.portador_recurso != unit_id
    ):
        carrier = next(
            current
            for current in state.unidades
            if current.id == state.portador_recurso
        )
        if carrier.bando != unit.bando:
            return (
                abs(unit.posicion[0] - target[0])
                + abs(unit.posicion[1] - target[1])
                <= 1
            )
    return unit.posicion == target


def _is_progressing_transition(
    transition: Transition,
    state: GameState,
    scenario: Escenario,
) -> bool:
    unit_id = transition.action.unidad_id
    if (
        transition.state.portador_recurso == unit_id
        and state.portador_recurso != unit_id
    ):
        return True
    return _distance_to_target(
        transition.state,
        scenario,
        unit_id,
    ) < _distance_to_target(state, scenario, unit_id)


def _estimate(
    position: tuple[int, int],
    target: tuple[int, int],
    heuristic: Heuristic,
    minimum_cost: float,
) -> float:
    if heuristic == "EUCLIDEA":
        return euclidean_distance(position, target) * minimum_cost
    return manhattan_distance(position, target) * minimum_cost
