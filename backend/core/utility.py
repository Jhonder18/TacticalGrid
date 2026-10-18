from typing import Literal, TypeAlias

from backend.algorithms.heuristics import manhattan_distance
from backend.models import Escenario, GameState
from backend.models.game_state import Posicion


Bando: TypeAlias = Literal["A", "B"]

WEIGHT_RESOURCE = 0.30
WEIGHT_PROGRESS = 0.40
WEIGHT_THREAT = 0.30
TERMINAL_WIN_UTILITY = 100_000.0


def evaluate_utility(state: GameState, player: Bando, scenario: Escenario) -> float:
    """Evalúa un estado desde la perspectiva del bando indicado.

    La utilidad positiva favorece a ``player`` (el MAX de la búsqueda) y la
    negativa favorece al rival. En estados no terminales se combinan tres
    señales normalizadas:

    * cercanía relativa de cada bando al recurso;
    * avance del portador hacia su propia base;
    * presión de cada bando sobre el objetivo estratégico rival.

    La utilidad terminal domina cualquier heurística: ganar vale +100000 y
    perder -100000 desde la perspectiva de ``player``.
    """

    if player not in ("A", "B"):
        raise ValueError("El jugador debe ser 'A' o 'B'")

    opponent = "B" if player == "A" else "A"
    winner = _winner(state, scenario)
    if winner is not None:
        return TERMINAL_WIN_UTILITY if winner == player else -TERMINAL_WIN_UTILITY

    resource_score = _relative_resource_proximity(state, scenario, player, opponent)
    progress_score = _relative_base_progress(state, scenario, player, opponent)
    threat_score = _relative_threat(state, scenario, player, opponent)

    return (
        WEIGHT_RESOURCE * resource_score
        + WEIGHT_PROGRESS * progress_score
        + WEIGHT_THREAT * threat_score
    )


def _winner(state: GameState, scenario: Escenario) -> str | None:
    if state.portador_recurso is None:
        return None

    carrier = _unit_position(state, state.portador_recurso)
    for bando in ("A", "B"):
        base = _base_position(scenario, bando)
        if carrier == base:
            return bando
    return None


def _relative_resource_proximity(
    state: GameState,
    scenario: Escenario,
    player: Bando,
    opponent: Bando,
) -> float:
    if state.posicion_recurso is None:
        return 0.0

    player_distance = _nearest_distance(state, player, state.posicion_recurso)
    opponent_distance = _nearest_distance(state, opponent, state.posicion_recurso)
    return _inverse_distance(player_distance) - _inverse_distance(opponent_distance)


def _relative_base_progress(
    state: GameState,
    scenario: Escenario,
    player: Bando,
    opponent: Bando,
) -> float:
    player_position = _carrier_position(state, player)
    opponent_position = _carrier_position(state, opponent)
    player_progress = (
        _inverse_distance(
            manhattan_distance(player_position, _base_position(scenario, player))
        )
        if player_position is not None
        else 0.0
    )
    opponent_progress = (
        _inverse_distance(
            manhattan_distance(opponent_position, _base_position(scenario, opponent))
        )
        if opponent_position is not None
        else 0.0
    )
    return player_progress - opponent_progress


def _relative_threat(
    state: GameState,
    scenario: Escenario,
    player: Bando,
    opponent: Bando,
) -> float:
    player_target = _strategic_target(state, player)
    opponent_target = _strategic_target(state, opponent)
    if player_target is None or opponent_target is None:
        return 0.0

    pressure_on_player = _nearest_distance(state, opponent, player_target)
    pressure_on_opponent = _nearest_distance(state, player, opponent_target)
    return _inverse_distance(pressure_on_opponent) - _inverse_distance(pressure_on_player)


def _strategic_target(state: GameState, bando: Bando) -> Posicion | None:
    if state.portador_recurso is not None:
        carrier = next(
            (
                unidad
                for unidad in state.unidades
                if unidad.id == state.portador_recurso
            ),
            None,
        )
        if carrier is not None:
            return carrier.posicion
    return state.posicion_recurso


def _carrier_position(state: GameState, bando: Bando) -> Posicion | None:
    if state.portador_recurso is None:
        return None
    carrier = next(
        (
            unidad
            for unidad in state.unidades
            if unidad.id == state.portador_recurso and unidad.bando == bando
        ),
        None,
    )
    return carrier.posicion if carrier is not None else None


def _nearest_distance(
    state: GameState,
    bando: Bando,
    target: Posicion,
) -> int:
    distances = [
        manhattan_distance(unidad.posicion, target)
        for unidad in state.unidades
        if unidad.bando == bando
    ]
    if not distances:
        return 10**6
    return min(distances)


def _unit_position(state: GameState, unit_id: str) -> Posicion:
    for unidad in state.unidades:
        if unidad.id == unit_id:
            return unidad.posicion
    raise ValueError(f"No existe la unidad portadora: {unit_id}")


def _base_position(scenario: Escenario, bando: Bando) -> Posicion:
    base = scenario.bases.A if bando == "A" else scenario.bases.B
    return base.fila, base.columna


def _inverse_distance(distance: int) -> float:
    return 1.0 / (1.0 + distance)
