import unittest
import asyncio
import json
from io import BytesIO

from fastapi import UploadFile

from backend.core.game import apply_action, get_game_status
from backend.core.successors import get_successors
from backend.main import run_game_turn
from backend.models import Accion, Coordenada, Escenario, GameState


def build_scenario() -> Escenario:
    return Escenario.model_validate(
        {
            "version": "1.0",
            "mapa": {"filas": 4, "columnas": 4},
            "tipos_terreno": {
                "camino": {"costo": 1, "transitable": True},
                "muro": {"transitable": False},
            },
            "terreno": [
                ["camino", "camino", "camino", "camino"],
                ["camino", "muro", "camino", "camino"],
                ["camino", "camino", "camino", "camino"],
                ["camino", "camino", "camino", "camino"],
            ],
            "bases": {
                "A": {"fila": 0, "columna": 0},
                "B": {"fila": 3, "columna": 3},
            },
            "recurso": {"fila": 2, "columna": 2},
            "unidades": [
                {
                    "id": "A1",
                    "bando": "A",
                    "tipo": "explorador",
                    "fila": 0,
                    "columna": 1,
                },
                {
                    "id": "B1",
                    "bando": "B",
                    "tipo": "defensor",
                    "fila": 3,
                    "columna": 2,
                },
            ],
            "turno": "A",
            "juego": {
                "portador_recurso": None,
                "profundidad_maxima_minimax": 2,
            },
            "prueba": {"modo": "partida"},
        }
    )


class GameTurnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = build_scenario()
        self.state = GameState.from_scenario(self.scenario)

    def test_applies_valid_action_without_mutating_original_state(self) -> None:
        action = Accion(
            tipo="mover",
            unidad_id="A1",
            origen=Coordenada(fila=0, columna=1),
            destino=Coordenada(fila=0, columna=2),
        )

        result = apply_action(self.state, self.scenario, action)

        self.assertEqual(result.estado_partida, "en curso")
        self.assertEqual(result.turno_siguiente, "B")
        self.assertEqual(result.estado.turno, "B")
        self.assertEqual(
            next(unit for unit in result.estado.unidades if unit.id == "A1").posicion,
            (0, 2),
        )
        self.assertEqual(
            next(unit for unit in self.state.unidades if unit.id == "A1").posicion,
            (0, 1),
        )

    def test_rejects_action_for_unit_from_other_bando(self) -> None:
        action = Accion(
            tipo="mover",
            unidad_id="B1",
            origen=Coordenada(fila=3, columna=2),
            destino=Coordenada(fila=3, columna=1),
        )

        with self.assertRaisesRegex(ValueError, "no puede actuar"):
            apply_action(self.state, self.scenario, action)

    def test_rejects_obstacle_and_non_orthogonal_moves(self) -> None:
        obstacle_action = Accion(
            tipo="mover",
            unidad_id="A1",
            origen=Coordenada(fila=0, columna=1),
            destino=Coordenada(fila=1, columna=1),
        )
        diagonal_action = Accion(
            tipo="mover",
            unidad_id="A1",
            origen=Coordenada(fila=0, columna=1),
            destino=Coordenada(fila=1, columna=2),
        )

        with self.assertRaises(ValueError):
            apply_action(self.state, self.scenario, obstacle_action)
        with self.assertRaises(ValueError):
            apply_action(self.state, self.scenario, diagonal_action)

    def test_picking_resource_updates_carrier_and_position(self) -> None:
        state = GameState(
            unidades=(
                self.state.unidades[0].__class__("A1", "A", (1, 2)),
                self.state.unidades[1],
            ),
            portador_recurso=None,
            posicion_recurso=(2, 2),
            turno="A",
        )
        action = Accion(
            tipo="mover",
            unidad_id="A1",
            origen=Coordenada(fila=1, columna=2),
            destino=Coordenada(fila=2, columna=2),
        )

        result = apply_action(state, self.scenario, action)

        self.assertEqual(result.estado.portador_recurso, "A1")
        self.assertIsNone(result.estado.posicion_recurso)

    def test_reports_terminal_victory_and_rejects_follow_up_action(self) -> None:
        scenario = self.scenario.model_copy(
            update={
                "juego": self.scenario.juego.model_copy(
                    update={"portador_recurso": "A1"}
                ),
                "recurso": Coordenada(fila=0, columna=0),
                "unidades": [
                    self.scenario.unidades[0].model_copy(
                        update={"fila": 0, "columna": 0}
                    ),
                    self.scenario.unidades[1],
                ],
            }
        )
        state = GameState.from_scenario(scenario)

        self.assertEqual(get_game_status(state, scenario), "victoria_A")
        with self.assertRaisesRegex(ValueError, "partida está"):
            apply_action(state, scenario, Accion(
                tipo="mover",
                unidad_id="A1",
                origen=Coordenada(fila=0, columna=0),
                destino=Coordenada(fila=0, columna=1),
            ))

    def test_status_is_blocked_when_no_successors_exist(self) -> None:
        state = GameState(
            unidades=(
                self.state.unidades[0].__class__("A1", "A", (1, 1)),
                self.state.unidades[1],
            ),
            portador_recurso=None,
            posicion_recurso=(2, 2),
            turno="A",
        )
        blocked_scenario = self.scenario.model_copy(
            update={
                "terreno": [
                    ["camino", "muro", "camino", "camino"],
                    ["muro", "muro", "muro", "camino"],
                    ["camino", "muro", "camino", "camino"],
                    ["camino", "camino", "camino", "camino"],
                ],
            }
        )
        self.assertEqual(get_game_status(state, blocked_scenario), "bloqueado")

    def test_endpoint_applies_valid_turn(self) -> None:
        action = {
            "tipo": "mover",
            "unidad_id": "A1",
            "origen": {"fila": 0, "columna": 1},
            "destino": {"fila": 0, "columna": 2},
        }
        result = asyncio.run(
            run_game_turn(
                UploadFile(
                    BytesIO(json.dumps(self.scenario.model_dump()).encode()),
                    filename="partida.json",
                ),
                json.dumps(action),
            )
        )

        self.assertEqual(result.estado.turno, "B")
        self.assertEqual(result.estado_partida, "en curso")
        self.assertEqual(result.accion.unidad_id, "A1")

    def test_endpoint_rejects_invalid_action(self) -> None:
        action = {
            "tipo": "mover",
            "unidad_id": "B1",
            "origen": {"fila": 3, "columna": 2},
            "destino": {"fila": 3, "columna": 1},
        }
        with self.assertRaisesRegex(Exception, "No se pudo aplicar el turno"):
            asyncio.run(
                run_game_turn(
                    UploadFile(
                        BytesIO(json.dumps(self.scenario.model_dump()).encode()),
                        filename="partida.json",
                    ),
                    json.dumps(action),
                )
            )

    def test_endpoint_reports_victory(self) -> None:
        scenario = self.scenario.model_copy(
            update={
                "juego": self.scenario.juego.model_copy(
                    update={"portador_recurso": "A1"}
                ),
                "recurso": Coordenada(fila=0, columna=1),
                "unidades": [
                    self.scenario.unidades[0].model_copy(
                        update={"fila": 0, "columna": 1}
                    ),
                    self.scenario.unidades[1],
                ],
            }
        )
        action = {
            "tipo": "mover",
            "unidad_id": "A1",
            "origen": {"fila": 0, "columna": 1},
            "destino": {"fila": 0, "columna": 0},
        }
        result = asyncio.run(
            run_game_turn(
                UploadFile(
                    BytesIO(json.dumps(scenario.model_dump()).encode()),
                    filename="partida.json",
                ),
                json.dumps(action),
            )
        )
        self.assertEqual(result.estado_partida, "victoria_A")
        self.assertIsNone(result.turno_siguiente)


if __name__ == "__main__":
    unittest.main()
