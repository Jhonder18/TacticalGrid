from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Coordenada(BaseModel):
    fila: int = Field(strict=True)
    columna: int = Field(strict=True)


class Mapa(BaseModel):
    filas: int = Field(strict=True, gt=0)
    columnas: int = Field(strict=True, gt=0)


class Terreno(BaseModel):
    costo: float | None = Field(default=None, gt=0)
    transitable: bool

    @model_validator(mode="after")
    def validar_costo_transitable(self) -> "Terreno":
        if self.transitable and self.costo is None:
            raise ValueError("Los terrenos transitables deben tener un costo positivo")
        return self


class Bases(BaseModel):
    A: Coordenada
    B: Coordenada


class Unidad(Coordenada):
    id: str = Field(min_length=1)
    bando: Literal["A", "B"]
    tipo: str = Field(min_length=1)


class Juego(BaseModel):
    portador_recurso: str | None = None
    profundidad_maxima_minimax: int = Field(strict=True, gt=0)


class Prueba(BaseModel):
    modo: Literal["busqueda", "partida", "adversarial"]
    unidad_inicio: str | None = None
    objetivo: Coordenada | None = None


class Escenario(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: str = Field(min_length=1)
    mapa: Mapa
    tipos_terreno: dict[str, Terreno]
    terreno: list[list[str]]
    bases: Bases
    recurso: Coordenada
    unidades: list[Unidad]
    turno: Literal["A", "B"]
    juego: Juego
    prueba: Prueba | None = None

    @model_validator(mode="after")
    def validar_consistencia(self) -> "Escenario":
        filas, columnas = self.mapa.filas, self.mapa.columnas

        if len(self.terreno) != filas or any(
            len(fila) != columnas for fila in self.terreno
        ):
            raise ValueError(
                "La matriz terreno debe coincidir con las dimensiones del mapa"
            )

        nombres_terreno = set(self.tipos_terreno)
        terrenos_usados = {
            nombre for fila in self.terreno for nombre in fila
        }
        desconocidos = terrenos_usados - nombres_terreno
        if desconocidos:
            raise ValueError(
                f"El mapa utiliza terrenos no definidos: {sorted(desconocidos)}"
            )

        posiciones = {
            "Base A": self.bases.A,
            "Base B": self.bases.B,
            "Recurso": self.recurso,
        }
        for nombre, posicion in posiciones.items():
            self._validar_posicion(posicion, filas, columnas, nombre)
            terreno = self.tipos_terreno[self.terreno[posicion.fila][posicion.columna]]
            if not terreno.transitable:
                raise ValueError(
                    f"{nombre} está sobre un terreno no transitable"
                )

        ids = [unidad.id for unidad in self.unidades]
        if len(ids) != len(set(ids)):
            raise ValueError("Los identificadores de las unidades deben ser únicos")

        for unidad in self.unidades:
            self._validar_posicion(unidad, filas, columnas, f"unidad {unidad.id}")
            terreno = self.tipos_terreno[self.terreno[unidad.fila][unidad.columna]]
            if not terreno.transitable:
                raise ValueError(
                    f"La unidad {unidad.id} está sobre un terreno no transitable"
                )

        portador = self.juego.portador_recurso
        if portador is not None and portador not in set(ids):
            raise ValueError(
                "portador_recurso debe identificar una unidad existente"
            )

        return self

    @staticmethod
    def _validar_posicion(
        posicion: Coordenada,
        filas: int,
        columnas: int,
        nombre: str,
    ) -> None:
        if not (0 <= posicion.fila < filas and 0 <= posicion.columna < columnas):
            raise ValueError(f"La posición de {nombre} está fuera del mapa")
