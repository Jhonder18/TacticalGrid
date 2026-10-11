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


class ResultadoAdversarial(BaseModel):
    algoritmo: Literal["MINIMAX", "ALFA_BETA"]
    nodos_generados: int = Field(ge=0)
    nodos_evaluados: int = Field(ge=0)
    nodos_podados: int = Field(ge=0)
    profundidad_alcanzada: int = Field(ge=0)
    tiempo: float = Field(ge=0)
    accion_seleccionada: Accion | None
    valor_obtenido: float


ResultadoAlgoritmo = Annotated[
    ResultadoBusqueda | ResultadoAdversarial,
    Field(discriminator="algoritmo"),
]
