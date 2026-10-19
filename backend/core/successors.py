from dataclasses import dataclass, replace

from backend.models import Accion, Coordenada, Escenario, GameState, UnidadEstado
from backend.models.game_state import Bando, Posicion


_DIRECCIONES_POR_NOMBRE: dict[str, Posicion] = {
    "ARRIBA": (-1, 0),
    "DERECHA": (0, 1),
    "ABAJO": (1, 0),
    "IZQUIERDA": (0, -1),
}
_ORDEN_PREDETERMINADO = ("ARRIBA", "DERECHA", "ABAJO", "IZQUIERDA")


@dataclass(frozen=True, slots=True)
class Transition:
    """Agrupa un estado sucesor con la acción y el costo que lo producen."""

    state: GameState
    action: Accion
    cost: float
    steps: tuple["TransitionStep", ...] = ()


@dataclass(frozen=True, slots=True)
class TransitionStep:
    action: Accion
    state: GameState
    cost: float


def get_successors(
    state: GameState,
    scenario: Escenario,
) -> tuple[Transition, ...]:
    """Genera todos los movimientos legales del turno actual.

    Purpose:
        Expandir un estado sin atravesar obstáculos ni salir del mapa.
    Preconditions:
        `state` debe pertenecer al escenario y `scenario` debe estar validado.
    Postconditions:
        Devuelve solo estados válidos, sin mutar el estado original.
    Complexity:
        Cuesta O(u) para ocupación más O(4u) para revisar movimientos.
    AI usage:
        Es la función de expansión común para BFS, DFS, UCS, A* y Beam Search.
    AI intervention:
        El orden fijo arriba, derecha, abajo e izquierda hace reproducibles las búsquedas.
    Student validation:
        Se probarán límites, obstáculos, ocupación, turnos, recurso y costos dinámicos.
    """

    sucesores: list[Transition] = []

    for unidad in state.unidades:
        if unidad.bando != state.turno:
            continue
        sucesores.extend(
            _get_unit_successors(
                state,
                scenario,
                unidad,
                cambia_turno=True,
            )
        )

    return tuple(sucesores)


def get_navigation_successors(
    state: GameState,
    scenario: Escenario,
    unit_id: str,
) -> tuple[Transition, ...]:
    """Genera sucesores para navegar con una sola unidad.

    Purpose:
        Expandir una prueba de navegación sin simular decisiones del adversario.
    Preconditions:
        `state` y `scenario` deben ser compatibles y `unit_id` debe existir.
    Postconditions:
        Solo cambia la unidad indicada y conserva el turno durante la búsqueda.
    Complexity:
        Cuesta O(u) para localizar la unidad y O(4u) para revisar sus movimientos.
    AI usage:
        Es la expansión común de BFS y DFS en el modo de búsqueda.
    AI intervention:
        Se separó la navegación del modo partida para respetar el alcance de T-06.
    Student validation:
        Se probará que las unidades no seleccionadas permanezcan sin cambios.
    """

    unidad = next(
        (unidad for unidad in state.unidades if unidad.id == unit_id),
        None,
    )
    if unidad is None:
        raise ValueError(f"No existe la unidad de búsqueda: {unit_id}")

    return tuple(
        _get_unit_successors(
            state,
            scenario,
            unidad,
            cambia_turno=False,
        )
    )


def _get_unit_successors(
    state: GameState,
    scenario: Escenario,
    unidad: UnidadEstado,
    cambia_turno: bool,
    resolver_robo: bool = True,
) -> tuple[Transition, ...]:
    posiciones_ocupadas = {unidad.posicion for unidad in state.unidades}
    sucesores: list[Transition] = []

    orden = scenario.orden_sucesores or list(_ORDEN_PREDETERMINADO)
    for direccion in orden:
        desplazamiento_fila, desplazamiento_columna = _DIRECCIONES_POR_NOMBRE[direccion]
        destino = (
            unidad.posicion[0] + desplazamiento_fila,
            unidad.posicion[1] + desplazamiento_columna,
        )
        if not _es_movimiento_legal(
            destino,
            unidad,
            posiciones_ocupadas,
            scenario,
        ):
            continue

        terreno = scenario.terreno[destino[0]][destino[1]]
        costo = scenario.tipos_terreno[terreno].costo
        assert costo is not None

        unidad_actualizada = replace(unidad, posicion=destino)
        unidades_actualizadas = tuple(
            unidad_actualizada if actual.id == unidad.id else actual
            for actual in state.unidades
        )
        portador = state.portador_recurso
        posicion_recurso = state.posicion_recurso
        if (
            portador is None
            and posicion_recurso is not None
            and destino == posicion_recurso
        ):
            portador = unidad.id
            posicion_recurso = None

        state_after_move = GameState(
            unidades=unidades_actualizadas,
            portador_recurso=portador,
            posicion_recurso=posicion_recurso,
            turno=state.turno,
        )
        cost_total = costo
        steps = (
            TransitionStep(
                action=Accion(
                    tipo="mover",
                    unidad_id=unidad.id,
                    origen=_coordenada(unidad.posicion),
                    destino=_coordenada(destino),
                ),
                state=state_after_move,
                cost=costo,
            ),
        )
        if resolver_robo:
            state_after_move, extra_cost, extra_steps = _resolve_robbery(
                state_after_move,
                scenario,
                unidad_actualizada,
                steps[0].action,
                costo,
            )
            cost_total += extra_cost
            if extra_steps:
                steps = extra_steps

        successor = GameState(
            unidades=state_after_move.unidades,
            portador_recurso=state_after_move.portador_recurso,
            posicion_recurso=state_after_move.posicion_recurso,
            turno=(
                _siguiente_turno(state.turno)
                if cambia_turno
                else state.turno
            ),
        )
        action = steps[0].action
        sucesores.append(
            Transition(
                state=successor,
                action=action,
                cost=cost_total,
                steps=tuple(
                    TransitionStep(
                        action=step.action,
                        state=GameState(
                            unidades=step.state.unidades,
                            portador_recurso=step.state.portador_recurso,
                            posicion_recurso=step.state.posicion_recurso,
                            turno=successor.turno,
                        ),
                        cost=step.cost,
                    )
                    for step in steps
                ),
            )
        )

    return tuple(sucesores)


def _resolve_robbery(
    state: GameState,
    scenario: Escenario,
    moving_unit: UnidadEstado,
    move_action: Accion,
    move_cost: float,
) -> tuple[GameState, float, tuple[TransitionStep, ...]]:
    carrier = next(
        (unit for unit in state.unidades if unit.id == state.portador_recurso),
        None,
    )
    if carrier is None or carrier.bando == moving_unit.bando:
        return state, 0.0, ()
    if abs(carrier.posicion[0] - moving_unit.posicion[0]) + abs(
        carrier.posicion[1] - moving_unit.posicion[1]
    ) != 1:
        return state, 0.0, ()

    current = GameState(
        unidades=state.unidades,
        portador_recurso=moving_unit.id,
        posicion_recurso=None,
        turno=state.turno,
    )
    extra_cost = 0.0
    extra_steps: list[TransitionStep] = [
        TransitionStep(
            action=move_action,
            state=current,
            cost=move_cost,
        )
    ]
    for _ in range(2):
        robber = next(
            unit for unit in current.unidades if unit.id == moving_unit.id
        )
        escapes = _get_unit_successors(
            current,
            scenario,
            robber,
            cambia_turno=False,
            resolver_robo=False,
        )
        if not escapes:
            break
        escape = max(
            escapes,
            key=lambda transition: (
                -_distance_to_own_base(
                    transition.state,
                    scenario,
                    moving_unit.id,
                ),
                _distance_to_enemy_carrier(transition.state, carrier),
                -transition.cost,
            ),
        )
        extra_steps.append(
            TransitionStep(
                action=escape.action,
                state=escape.state,
                cost=escape.cost,
            )
        )
        current = escape.state
        extra_cost += escape.cost
    return current, extra_cost, tuple(extra_steps)


def _distance_to_enemy_carrier(
    state: GameState,
    carrier: UnidadEstado,
) -> int:
    robber = next(
        unit for unit in state.unidades if unit.id == state.portador_recurso
    )
    return abs(robber.posicion[0] - carrier.posicion[0]) + abs(
        robber.posicion[1] - carrier.posicion[1]
    )


def _distance_to_own_base(
    state: GameState,
    scenario: Escenario,
    unit_id: str,
) -> int:
    robber = next(unit for unit in state.unidades if unit.id == unit_id)
    base = scenario.bases.A if robber.bando == "A" else scenario.bases.B
    return abs(robber.posicion[0] - base.fila) + abs(
        robber.posicion[1] - base.columna
    )


def _es_movimiento_legal(
    destino: Posicion,
    unidad: UnidadEstado,
    posiciones_ocupadas: set[Posicion],
    scenario: Escenario,
) -> bool:
    filas, columnas = scenario.mapa.filas, scenario.mapa.columnas
    if not (0 <= destino[0] < filas and 0 <= destino[1] < columnas):
        return False
    if destino in posiciones_ocupadas and destino != unidad.posicion:
        return False

    nombre_terreno = scenario.terreno[destino[0]][destino[1]]
    return scenario.tipos_terreno[nombre_terreno].transitable


def _siguiente_turno(turno: Bando) -> Bando:
    return "B" if turno == "A" else "A"


def _coordenada(posicion: Posicion) -> Coordenada:
    return Coordenada(fila=posicion[0], columna=posicion[1])