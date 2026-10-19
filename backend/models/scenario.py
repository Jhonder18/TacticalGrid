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
    profundidad_maxima_minimax: int = Field(strict=True, gt=0, le=8)


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
    orden_sucesores: list[Literal["ARRIBA", "DERECHA", "ABAJO", "IZQUIERDA"]] | None = None

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

        if (
            self.bases.A.fila == self.bases.B.fila
            and self.bases.A.columna == self.bases.B.columna
        ):
            raise ValueError("Las bases A y B deben estar en posiciones diferentes")

        ids = [unidad.id for unidad in self.unidades]
        if len(ids) != len(set(ids)):
            raise ValueError("Los identificadores de las unidades deben ser únicos")

        ocupadas: set[tuple[int, int]] = set()
        for unidad in self.unidades:
            self._validar_posicion(unidad, filas, columnas, f"unidad {unidad.id}")
            terreno = self.tipos_terreno[self.terreno[unidad.fila][unidad.columna]]
            if not terreno.transitable:
                raise ValueError(
                    f"La unidad {unidad.id} está sobre un terreno no transitable"
                )
            posicion = (unidad.fila, unidad.columna)
            if posicion in ocupadas:
                raise ValueError(
                    "Las posiciones iniciales de las unidades no pueden repetirse"
                )
            ocupadas.add(posicion)

        if self.orden_sucesores is not None:
            if len(self.orden_sucesores) != len(set(self.orden_sucesores)):
                raise ValueError(
                    "orden_sucesores no puede contener direcciones repetidas"
                )

        if self.prueba is not None and self.prueba.modo == "busqueda":
            self._validar_prueba_busqueda(filas, columnas)

        portador = self.juego.portador_recurso
        if portador is not None and portador not in set(ids):
            raise ValueError(
                "portador_recurso debe identificar una unidad existente"
            )
        if portador is not None:
            unidad_portadora = next(
                unidad for unidad in self.unidades if unidad.id == portador
            )
            if unidad_portadora.fila != self.recurso.fila or unidad_portadora.columna != self.recurso.columna:
                raise ValueError(
                    "La unidad portadora debe ocupar la misma posición que el recurso"
                )

        return self

    def _validar_prueba_busqueda(
        self,
        filas: int,
        columnas: int,
    ) -> None:
        prueba = self.prueba
        assert prueba is not None

        if prueba.unidad_inicio is None:
            raise ValueError(
                "La prueba en modo busqueda debe indicar unidad_inicio"
            )
        if prueba.unidad_inicio not in {unidad.id for unidad in self.unidades}:
            raise ValueError(
                "unidad_inicio debe identificar una unidad existente"
            )

        if prueba.objetivo is None:
            raise ValueError(
                "La prueba en modo busqueda debe indicar objetivo"
            )
        self._validar_posicion(prueba.objetivo, filas, columnas, "objetivo")
        terreno = self.tipos_terreno[
            self.terreno[prueba.objetivo.fila][prueba.objetivo.columna]
        ]
        if not terreno.transitable:
            raise ValueError("El objetivo está sobre un terreno no transitable")

    @staticmethod
    def _validar_posicion(
        posicion: Coordenada,
        filas: int,
        columnas: int,
        nombre: str,
    ) -> None:
        if not (0 <= posicion.fila < filas and 0 <= posicion.columna < columnas):
            raise ValueError(f"La posición de {nombre} está fuera del mapa")
