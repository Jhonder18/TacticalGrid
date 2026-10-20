"""Simulación automática de partidas y utilidades de turno.

Reúne la lógica compartida por el endpoint ``/api/game/simulate`` y los
generadores de informes: convertir resultados internos a respuestas Pydantic y
ejecutar una partida completa hasta un estado terminal.
"""

from backend.core.game import apply_action, get_game_status
from backend.core.game_policy import choose_turn_transition
from backend.models import (
    EstadoPartidaResponse,
    GameState,
    PasoTurno,
    ResultadoSimulacion,
    ResultadoTurno,
    Escenario,
    UnidadEstadoResponse,
)


def turn_limit(scenario: Escenario) -> int:
    """Calcula el máximo de turnos permitidos para una partida.

    Purpose:
        Evitar simulaciones sin fin acotando la duración de la partida.
    Preconditions:
        `scenario` debe estar validado.
    Postconditions:
        Devuelve un entero entre 50 y 500 proporcional al tamaño del mapa.
    Complexity:
        O(1).
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se probará con mapas pequeños y grandes.
    """

    return min(500, max(50, 4 * scenario.mapa.filas * scenario.mapa.columnas))


def state_response(state: GameState) -> EstadoPartidaResponse:
    """Convierte un estado interno en una respuesta serializable.

    Purpose:
        Compartir el formato de estado entre turnos y simulaciones.
    Preconditions:
        `state` debe ser un `GameState` válido.
    Postconditions:
        Devuelve un `EstadoPartidaResponse` con posiciones como coordenadas.
    Complexity:
        O(u), con u el número de unidades.
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se revisará contra los escenarios de partida.
    """

    return EstadoPartidaResponse(
        unidades=[
            UnidadEstadoResponse(
                id=unit.id,
                bando=unit.bando,
                posicion={"fila": unit.posicion[0], "columna": unit.posicion[1]},
            )
            for unit in state.unidades
        ],
        portador_recurso=state.portador_recurso,
        posicion_recurso=(
            None
            if state.posicion_recurso is None
            else {
                "fila": state.posicion_recurso[0],
                "columna": state.posicion_recurso[1],
            }
        ),
        turno=state.turno,
    )


def turn_result(result, algoritmo: str, heuristica: str) -> ResultadoTurno:
    """Convierte el resultado interno de un turno en una respuesta Pydantic.

    Purpose:
        Estandarizar la salida de un turno aplicado.
    Preconditions:
        `result` proviene de `apply_action`.
    Postconditions:
        Devuelve un `ResultadoTurno` con estado, acción, costo y pasos.
    Complexity:
        O(u + p), con u unidades y p pasos del turno.
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se comparará con las métricas del tablero.
    """

    return ResultadoTurno(
        algoritmo=algoritmo,
        heuristica=heuristica,
        estado=state_response(result.estado),
        accion=result.accion,
        costo=result.costo,
        estado_partida=result.estado_partida,
        turno_siguiente=result.turno_siguiente,
        pasos=[
            PasoTurno(
                accion=step.action,
                estado=state_response(step.state),
                costo=step.cost,
            )
            for step in result.pasos
        ],
    )


def simular_partida(
    scenario: Escenario,
    algoritmo: str = "BFS",
    heuristica: str = "MANHATTAN",
    k: int = 4,
) -> ResultadoSimulacion:
    """Simula una partida completa hasta un estado terminal.

    Purpose:
        Producir el historial y el estado final de una partida automática.
    Preconditions:
        `scenario` debe estar validado y en modo partida.
    Postconditions:
        Devuelve la simulación con historial, estado final y motivo. El resultado
        es reproducible para el mismo escenario y parámetros.
    Complexity:
        O(T · (u + b^d)), donde T es el número de turnos y b^d el costo de cada
        decisión.
    AI usage:
        No.
    AI intervention:
        Se extrajo de `main.py` para reutilizarla en los informes de resultados.
    Student validation:
        Se probará con los escenarios de robo de bandera y bandera bloqueada.
    """

    state = GameState.from_scenario(scenario)
    limit = turn_limit(scenario)
    history = []
    status = get_game_status(state, scenario)
    visited_states = {state}
    final_reason = None

    for _ in range(limit):
        if status != "en curso":
            break
        transition = choose_turn_transition(state, scenario, algoritmo, heuristica, k)
        result = apply_action(state, scenario, transition.action)
        history.append(turn_result(result, algoritmo, heuristica))
        state = result.estado
        status = result.estado_partida
        if status == "en curso" and state in visited_states:
            status = "empate"
            final_reason = (
                "Se detectó un bucle: el estado completo de la partida "
                "se repitió, por lo que la partida queda en empate."
            )
            break
        visited_states.add(state)

    if status == "en curso" and len(history) >= limit:
        status = "empate"
        final_reason = (
            "La partida alcanzó el límite máximo de turnos sin un ganador, "
            "por lo que queda en empate."
        )

    return ResultadoSimulacion(
        algoritmo=algoritmo,
        heuristica=heuristica,
        limite_turnos=limit,
        turnos_ejecutados=len(history),
        estado_final=status,
        motivo_final=final_reason,
        historial=history,
    )
