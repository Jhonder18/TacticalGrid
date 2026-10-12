import json
from dataclasses import dataclass
from typing import Literal, TypeAlias

from .scenario import Escenario


Posicion: TypeAlias = tuple[int, int]
Bando: TypeAlias = Literal["A", "B"]


@dataclass(frozen=True, slots=True)
class UnidadEstado:
    """Representa la parte mutable de una unidad dentro de un estado.

    Purpose:
        Mantener la identidad, el bando y la posición de una unidad.
    Preconditions:
        La unidad debe tener un identificador único y una posición válida.
    Postconditions:
        La instancia es inmutable y puede formar parte de una clave de estado.
    Complexity:
        La creación y el acceso a sus campos son O(1).
    AI usage:
        Este objeto será usado por algoritmos para comparar y expandir estados.
    AI intervention:
        La representación fue diseñada para separar datos dinámicos de estáticos.
    Student validation:
        Se verificará mediante pruebas de igualdad, hashing y generación de sucesores.
    """

    id: str
    bando: Bando
    posicion: Posicion


@dataclass(frozen=True, slots=True, eq=False)
class GameState:
    """Representa de forma inmutable una configuración completa del juego.

    Purpose:
        Identificar matemáticamente una situación del juego para búsqueda.
    Preconditions:
        Las unidades deben estar ordenadas de forma determinista por identificador.
    Postconditions:
        Estados iguales tienen la misma clave, serialización y función hash.
    Complexity:
        Crear la clave y serializar el estado cuesta O(u), donde u es el número de unidades.
    AI usage:
        La clave permite detectar estados repetidos en BFS, DFS, UCS y A*.
    AI intervention:
        Se eligieron solo datos que cambian durante la partida; el mapa permanece en Escenario.
    Student validation:
        Se probarán diferencias de turno, posiciones, portador y posición del recurso.
    """

    unidades: tuple[UnidadEstado, ...]
    portador_recurso: str | None
    posicion_recurso: Posicion | None
    turno: Bando

    @classmethod
    def from_scenario(cls, scenario: Escenario) -> "GameState":
        """Construye el estado inicial a partir de un escenario validado.

        Purpose:
            Convertir el contrato JSON validado en el estado dinámico inicial.
        Preconditions:
            `scenario` debe ser una instancia válida de `Escenario`.
        Postconditions:
            Las unidades quedan ordenadas por identificador y el recurso queda sin posición
            cuando ya tiene portador.
        Complexity:
            Cuesta O(u log u) por la ordenación de las unidades.
        AI usage:
            Proporciona la raíz desde la que los algoritmos generan sucesores.
        AI intervention:
            La posición del recurso se vuelve `None` cuando una unidad lo transporta.
        Student validation:
            Se comprobará contra los escenarios JSON válidos del proyecto.
        """

        unidades = tuple(
            UnidadEstado(
                id=unidad.id,
                bando=unidad.bando,
                posicion=(unidad.fila, unidad.columna),
            )
            for unidad in sorted(scenario.unidades, key=lambda unidad: unidad.id)
        )
        portador = scenario.juego.portador_recurso
        posicion_recurso = (
            None
            if portador is not None
            else (scenario.recurso.fila, scenario.recurso.columna)
        )
        return cls(
            unidades=unidades,
            portador_recurso=portador,
            posicion_recurso=posicion_recurso,
            turno=scenario.turno,
        )

    def state_key(self) -> tuple[tuple[tuple[str, str, int, int], ...], str | None, Posicion | None, str]:
        """Devuelve la clave canónica usada para comparar estados.

        Purpose:
            Representar todos los datos relevantes del estado en un orden estable.
        Preconditions:
            Las unidades deben contener identificadores únicos.
        Postconditions:
            La misma configuración siempre produce la misma tupla.
        Complexity:
            Cuesta O(u log u) si el orden recibido no es canónico.
        AI usage:
            La clave se utiliza en conjuntos de visitados y tablas de costos.
        AI intervention:
            Se incluyen turno y recurso para evitar colisiones entre estados visualmente similares.
        Student validation:
            Se compararán claves de estados con una sola diferencia dinámica.
        """

        unidades = tuple(
            (unidad.id, unidad.bando, *unidad.posicion)
            for unidad in sorted(self.unidades, key=lambda unidad: unidad.id)
        )
        return (
            unidades,
            self.portador_recurso,
            self.posicion_recurso,
            self.turno,
        )

    def serialize(self) -> str:
        """Serializa el estado en JSON determinista y apto para depuración."""

        return json.dumps(
            self.state_key(),
            ensure_ascii=True,
            separators=(",", ":"),
        )

    def __hash__(self) -> int:
        return hash(self.state_key())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GameState):
            return NotImplemented
        return self.state_key() == other.state_key()