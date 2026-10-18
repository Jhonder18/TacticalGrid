from dataclasses import dataclass
from typing import Literal

from backend.core.successors import Transition, get_successors
from backend.models import Accion, Escenario, GameState


EstadoPartida = Literal["en curso", "victoria_A", "victoria_B", "bloqueado"]


@dataclass(frozen=True, slots=True)
class ResultadoTurno:
    """Resultado inmutable de aplicar una acción al estado de una partida."""

    estado: GameState
    accion: Accion
    costo: float
    estado_partida: EstadoPartida
    turno_siguiente: str | None


def apply_action(
    state: GameState,
    scenario: Escenario,
    action: Accion,
) -> ResultadoTurno:
    """Aplica una acción legal y devuelve el estado siguiente.

    Las acciones válidas se obtienen de ``get_successors`` para mantener una
    única fuente de verdad para límites, obstáculos, ocupación, recurso y
    cambio de turno.
    """

    current_status = get_game_status(state, scenario)
    if current_status != "en curso":
        raise ValueError(
            f"No se puede aplicar una acción: la partida está {current_status}"
        )

    transition = _find_matching_transition(state, scenario, action)
    next_state = transition.state
    status = get_game_status(next_state, scenario)

    return ResultadoTurno(
        estado=next_state,
        accion=transition.action,
        costo=transition.cost,
        estado_partida=status,
        turno_siguiente=None if status != "en curso" else next_state.turno,
    )


def get_game_status(state: GameState, scenario: Escenario) -> EstadoPartida:
    """Determina si la partida continúa, terminó o quedó bloqueada."""

    winner = _winner(state, scenario)
    if winner is not None:
        return "victoria_A" if winner == "A" else "victoria_B"

    if not get_successors(state, scenario):
        return "bloqueado"

    return "en curso"


def _find_matching_transition(
    state: GameState,
    scenario: Escenario,
    action: Accion,
) -> Transition:
    transitions = get_successors(state, scenario)
    for transition in transitions:
        if transition.action == action:
            return transition

    if not any(
        transition.action.unidad_id == action.unidad_id
        for transition in transitions
    ):
        raise ValueError(
            f"La unidad {action.unidad_id} no puede actuar en el turno {state.turno}"
        )
    raise ValueError("La acción no es válida para el estado actual")


def _winner(state: GameState, scenario: Escenario) -> str | None:
    if state.portador_recurso is None:
        return None

    carrier = next(
        unit for unit in state.unidades if unit.id == state.portador_recurso
    )
    base = scenario.bases.A if carrier.bando == "A" else scenario.bases.B
    if carrier.posicion == (base.fila, base.columna):
        return carrier.bando
    return None
