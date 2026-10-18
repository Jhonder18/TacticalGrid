from dataclasses import dataclass
from time import perf_counter

from backend.core.successors import get_successors
from backend.core.utility import evaluate_utility
from backend.models import Accion, Escenario, GameState, ResultadoAdversarial
from backend.models.game_state import Bando


MAX_MINIMAX_DEPTH = 8


@dataclass
class MinimaxMetrics:
    nodos_generados: int = 1
    nodos_evaluados: int = 0
    profundidad_alcanzada: int = 0


def minimax(scenario: Escenario) -> ResultadoAdversarial:
    """Selecciona la acción con mayor utilidad minimax desde el turno inicial.

    MAX es el bando de ``scenario.turno`` y MIN es el bando contrario. La
    recursión se corta estrictamente en la profundidad configurada por el
    escenario o al alcanzar una victoria terminal.
    """

    depth_limit = scenario.juego.profundidad_maxima_minimax
    if depth_limit <= 0:
        raise ValueError("La profundidad máxima de Minimax debe ser positiva")
    if depth_limit > MAX_MINIMAX_DEPTH:
        raise ValueError(
            f"La profundidad máxima de Minimax no puede superar {MAX_MINIMAX_DEPTH}"
        )

    initial_state = GameState.from_scenario(scenario)
    max_player = initial_state.turno
    metrics = MinimaxMetrics()
    started_at = perf_counter()
    value, action = _minimax(
        state=initial_state,
        scenario=scenario,
        max_player=max_player,
        depth=0,
        depth_limit=depth_limit,
        metrics=metrics,
    )

    return ResultadoAdversarial(
        algoritmo="MINIMAX",
        nodos_generados=metrics.nodos_generados,
        nodos_evaluados=metrics.nodos_evaluados,
        nodos_podados=0,
        profundidad_alcanzada=metrics.profundidad_alcanzada,
        tiempo=perf_counter() - started_at,
        accion_seleccionada=action,
        valor_obtenido=value,
    )


def _minimax(
    state: GameState,
    scenario: Escenario,
    max_player: Bando,
    depth: int,
    depth_limit: int,
    metrics: MinimaxMetrics,
) -> tuple[float, Accion | None]:
    metrics.profundidad_alcanzada = max(metrics.profundidad_alcanzada, depth)
    transitions = get_successors(state, scenario)
    terminal = _is_terminal(state, scenario)

    if depth >= depth_limit or terminal or not transitions:
        metrics.nodos_evaluados += 1
        return evaluate_utility(state, max_player, scenario), None

    is_max_node = state.turno == max_player
    best_value = float("-inf") if is_max_node else float("inf")
    best_action: Accion | None = None

    for transition in transitions:
        metrics.nodos_generados += 1
        child_value, _ = _minimax(
            transition.state,
            scenario,
            max_player,
            depth + 1,
            depth_limit,
            metrics,
        )
        if (
            best_action is None
            or (is_max_node and child_value > best_value)
            or (not is_max_node and child_value < best_value)
        ):
            best_value = child_value
            best_action = transition.action

    return best_value, best_action


def _is_terminal(state: GameState, scenario: Escenario) -> bool:
    if state.portador_recurso is None:
        return False

    carrier = next(
        unidad
        for unidad in state.unidades
        if unidad.id == state.portador_recurso
    )
    base = scenario.bases.A if carrier.bando == "A" else scenario.bases.B
    return carrier.posicion == (base.fila, base.columna)
