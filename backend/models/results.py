from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .scenario import Coordenada


class Accion(BaseModel):
    tipo: str
    unidad_id: str
    origen: Coordenada | None = None
    destino: Coordenada | None = None


class ResultadoBusqueda(BaseModel):
    algoritmo: Literal["BFS", "DFS", "UCS", "A_ESTRELLA", "BEAM_SEARCH"]
    exito: bool
    camino: list[Coordenada]
    costo: float = Field(ge=0)
    longitud_camino: int = Field(ge=0)
    estados_generados: int = Field(ge=0)
    estados_expandidos: int = Field(ge=0)
    maximo_frontera: int = Field(ge=0)
    tiempo: float = Field(ge=0)
    k: int | None = Field(default=None, ge=0)


class NodoArbolAdversarial(BaseModel):
    id: str
    profundidad: int = Field(ge=0)
    jugador: Literal["MAX", "MIN"]
    accion: Accion | None = None
    valor: float | None = None
    estado: Literal["explorado", "evaluado", "podado", "terminal"]
    hijos: list["NodoArbolAdversarial"] = Field(default_factory=list)


class ResultadoAdversarial(BaseModel):
    algoritmo: Literal["MINIMAX", "ALFA_BETA"]
    nodos_generados: int = Field(ge=0)
    nodos_evaluados: int = Field(ge=0)
    nodos_podados: int = Field(ge=0)
    profundidad_alcanzada: int = Field(ge=0)
    tiempo: float = Field(ge=0)
    accion_seleccionada: Accion | None
    valor_obtenido: float
    arbol: NodoArbolAdversarial


class UnidadEstadoResponse(BaseModel):
    id: str
    bando: Literal["A", "B"]
    posicion: Coordenada


class EstadoPartidaResponse(BaseModel):
    unidades: list[UnidadEstadoResponse]
    portador_recurso: str | None
    posicion_recurso: Coordenada | None
    turno: Literal["A", "B"]


class PasoTurno(BaseModel):
    accion: Accion
    estado: EstadoPartidaResponse
    costo: float = Field(ge=0)


class ResultadoTurno(BaseModel):
    algoritmo: Literal["BFS", "DFS", "UCS", "A_ESTRELLA", "BEAM_SEARCH"]
    heuristica: Literal["MANHATTAN", "EUCLIDEA"]
    estado: EstadoPartidaResponse
    accion: Accion
    costo: float = Field(ge=0)
    estado_partida: Literal["en curso", "victoria_A", "victoria_B", "bloqueado"]
    turno_siguiente: Literal["A", "B"] | None
    pasos: list[PasoTurno]


class ResultadoSimulacion(BaseModel):
    algoritmo: Literal["BFS", "DFS", "UCS", "A_ESTRELLA", "BEAM_SEARCH"]
    heuristica: Literal["MANHATTAN", "EUCLIDEA"]
    limite_turnos: int = Field(gt=0)
    turnos_ejecutados: int = Field(ge=0)
    estado_final: Literal["en curso", "victoria_A", "victoria_B", "bloqueado", "empate"]
    motivo_final: str | None = None
    historial: list[ResultadoTurno]


ResultadoAlgoritmo = Annotated[
    ResultadoBusqueda | ResultadoAdversarial,
    Field(discriminator="algoritmo"),
]
