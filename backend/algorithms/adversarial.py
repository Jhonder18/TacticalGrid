from dataclasses import dataclass
from time import perf_counter

from backend.core.successors import get_successors
from backend.core.utility import evaluate_utility
from backend.models import (
    Accion,
    Escenario,
    GameState,
    NodoArbolAdversarial,
    ResultadoAdversarial,
)
from backend.models.game_state import Bando


MAX_MINIMAX_DEPTH = 8


@dataclass
class AdversarialMetrics:
    nodos_generados: int = 1
    nodos_evaluados: int = 0
    nodos_podados: int = 0
    profundidad_alcanzada: int = 0
    arbol: NodoArbolAdversarial | None = None


def minimax(scenario: Escenario) -> ResultadoAdversarial:
    return _run_adversarial(scenario, "MINIMAX")


def alpha_beta(scenario: Escenario) -> ResultadoAdversarial:
    return _run_adversarial(scenario, "ALFA_BETA")


def _run_adversarial(
    scenario: Escenario,
    algorithm: str,
) -> ResultadoAdversarial:
    depth_limit = scenario.juego.profundidad_maxima_minimax
    _validate_depth(depth_limit, algorithm)
    initial_state = GameState.from_scenario(scenario)
    max_player = initial_state.turno
    metrics = AdversarialMetrics()
    metrics.arbol = _make_tree_node(initial_state, max_player, 0, "root")
    started_at = perf_counter()

    if algorithm == "MINIMAX":
        value, action = _minimax(
            initial_state, scenario, max_player, 0, depth_limit, metrics, metrics.arbol
        )
    else:
        value, action = _alpha_beta(
            initial_state,
            scenario,
            max_player,
            0,
            depth_limit,
            float("-inf"),
            float("inf"),
            metrics,
            metrics.arbol,
        )

    return ResultadoAdversarial(
        algoritmo=algorithm,
        nodos_generados=metrics.nodos_generados,
        nodos_evaluados=metrics.nodos_evaluados,
        nodos_podados=metrics.nodos_podados,
        profundidad_alcanzada=metrics.profundidad_alcanzada,
        tiempo=perf_counter() - started_at,
        accion_seleccionada=action,
        valor_obtenido=value,
        arbol=metrics.arbol,
    )


def _minimax(
    state: GameState,
    scenario: Escenario,
    max_player: Bando,
    depth: int,
    depth_limit: int,
    metrics: AdversarialMetrics,
    tree_node: NodoArbolAdversarial,
) -> tuple[float, Accion | None]:
    metrics.profundidad_alcanzada = max(metrics.profundidad_alcanzada, depth)
    transitions = get_successors(state, scenario)
    terminal = _is_terminal(state, scenario)
    if depth >= depth_limit or terminal or not transitions:
        return _evaluate_leaf(state, scenario, max_player, metrics, tree_node, terminal)

    is_max = state.turno == max_player
    best_value = float("-inf") if is_max else float("inf")
    best_action: Accion | None = None
    for index, transition in enumerate(transitions, start=1):
        metrics.nodos_generados += 1
        child = _make_tree_node(
            transition.state,
            max_player,
            depth + 1,
            f"{tree_node.id}.{index}",
            transition.action,
        )
        tree_node.hijos.append(child)
        child_value, _ = _minimax(
            transition.state,
            scenario,
            max_player,
            depth + 1,
            depth_limit,
            metrics,
            child,
        )
        if best_action is None or (is_max and child_value > best_value) or (
            not is_max and child_value < best_value
        ):
            best_value = child_value
            best_action = transition.action
    tree_node.valor = best_value
    return best_value, best_action


def _alpha_beta(
    state: GameState,
    scenario: Escenario,
    max_player: Bando,
    depth: int,
    depth_limit: int,
    alpha: float,
    beta: float,
    metrics: AdversarialMetrics,
    tree_node: NodoArbolAdversarial,
) -> tuple[float, Accion | None]:
    metrics.profundidad_alcanzada = max(metrics.profundidad_alcanzada, depth)
    transitions = get_successors(state, scenario)
    terminal = _is_terminal(state, scenario)
    if depth >= depth_limit or terminal or not transitions:
        return _evaluate_leaf(state, scenario, max_player, metrics, tree_node, terminal)

    is_max = state.turno == max_player
    best_value = float("-inf") if is_max else float("inf")
    best_action: Accion | None = None
    for index, transition in enumerate(transitions):
        metrics.nodos_generados += 1
        child = _make_tree_node(
            transition.state,
            max_player,
            depth + 1,
            f"{tree_node.id}.{index + 1}",
            transition.action,
        )
        tree_node.hijos.append(child)
        child_value, _ = _alpha_beta(
            transition.state,
            scenario,
            max_player,
            depth + 1,
            depth_limit,
            alpha,
            beta,
            metrics,
            child,
        )
        if best_action is None or (is_max and child_value > best_value) or (
            not is_max and child_value < best_value
        ):
            best_value = child_value
            best_action = transition.action
        if is_max:
            alpha = max(alpha, best_value)
        else:
            beta = min(beta, best_value)
        if beta <= alpha:
            remaining = transitions[index + 1:]
            metrics.nodos_podados += len(remaining)
            for offset, pruned in enumerate(remaining, start=index + 2):
                tree_node.hijos.append(
                    _make_tree_node(
                        pruned.state,
                        max_player,
                        depth + 1,
                        f"{tree_node.id}.{offset}",
                        pruned.action,
                        "podado",
                    )
                )
            break
    tree_node.valor = best_value
    return best_value, best_action


def _evaluate_leaf(
    state: GameState,
    scenario: Escenario,
    max_player: Bando,
    metrics: AdversarialMetrics,
    tree_node: NodoArbolAdversarial,
    terminal: bool,
) -> tuple[float, None]:
    metrics.nodos_evaluados += 1
    value = evaluate_utility(state, max_player, scenario)
    tree_node.valor = value
    tree_node.estado = "terminal" if terminal else "evaluado"
    return value, None


def _make_tree_node(
    state: GameState,
    max_player: Bando,
    depth: int,
    node_id: str,
    action: Accion | None = None,
    status: str = "explorado",
) -> NodoArbolAdversarial:
    return NodoArbolAdversarial(
        id=node_id,
        profundidad=depth,
        jugador="MAX" if state.turno == max_player else "MIN",
        accion=action,
        estado=status,
    )


def _validate_depth(depth: int, algorithm: str) -> None:
    if depth <= 0:
        raise ValueError(f"La profundidad máxima de {algorithm} debe ser positiva")
    if depth > MAX_MINIMAX_DEPTH:
        raise ValueError(
            f"La profundidad máxima de {algorithm} no puede superar {MAX_MINIMAX_DEPTH}"
        )


def _is_terminal(state: GameState, scenario: Escenario) -> bool:
    if state.portador_recurso is None:
        return False
    carrier = next(
        unit for unit in state.unidades if unit.id == state.portador_recurso
    )
    base = scenario.bases.A if carrier.bando == "A" else scenario.bases.B
    return carrier.posicion == (base.fila, base.columna)
