from dataclasses import dataclass, replace

from backend.models import Accion, Coordenada, Escenario, GameState, UnidadEstado
from backend.models.game_state import Bando, Posicion


_DIRECCIONES: tuple[Posicion, ...] = (
    (-1, 0),
    (0, 1),
    (1, 0),
    (0, -1),
)


@dataclass(frozen=True, slots=True)
class Transition:
    """Agrupa un estado sucesor con la acción y el costo que lo producen."""

    state: GameState
    action: Accion
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

    posiciones_ocupadas = {
        unidad.posicion for unidad in state.unidades
    }
    sucesores: list[Transition] = []

    for unidad in state.unidades:
        if unidad.bando != state.turno:
            continue

        for desplazamiento_fila, desplazamiento_columna in _DIRECCIONES:
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

            successor = GameState(
                unidades=unidades_actualizadas,
                portador_recurso=portador,
                posicion_recurso=posicion_recurso,
                turno=_siguiente_turno(state.turno),
            )
            action = Accion(
                tipo="mover",
                unidad_id=unidad.id,
                origen=_coordenada(unidad.posicion),
                destino=_coordenada(destino),
            )
            sucesores.append(
                Transition(state=successor, action=action, cost=costo)
            )

    return tuple(sucesores)


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