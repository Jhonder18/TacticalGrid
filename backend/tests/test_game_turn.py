import unittest
import asyncio
import json
from dataclasses import replace
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile

from backend.core.game import apply_action, get_game_status
from backend.core.game_policy import choose_turn_transition
from backend.core.successors import get_successors
from backend.main import run_game_turn, simulate_game
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

    def test_adjacent_enemy_steals_and_receives_two_escape_moves(self) -> None:
        state = GameState(
            unidades=(
                self.state.unidades[0].__class__("A1", "A", (2, 2)),
                self.state.unidades[1].__class__("B1", "B", (1, 1)),
            ),
            portador_recurso="B1",
            posicion_recurso=None,
            turno="A",
        )
        transition = next(
            item for item in get_successors(state, self.scenario)
            if item.action.unidad_id == "A1"
            and item.action.destino == Coordenada(fila=2, columna=1)
        )

        self.assertEqual(transition.state.portador_recurso, "A1")
        robber = next(
            unit for unit in transition.state.unidades if unit.id == "A1"
        )
        self.assertEqual(robber.posicion, (1, 0))
        self.assertEqual(len(transition.steps), 3)
        self.assertEqual(
            [step.action.destino for step in transition.steps],
            [
                Coordenada(fila=2, columna=1),
                Coordenada(fila=2, columna=0),
                Coordenada(fila=1, columna=0),
            ],
        )
        self.assertEqual(transition.steps[0].state.portador_recurso, "A1")

    def test_blocked_carrier_restores_resource_to_original_position(self) -> None:
        scenario = Escenario.model_validate(
            json.loads(
                (
                    Path("examples/good/escenario_bandera_bloqueada.json")
                ).read_text()
            )
        )
        state = GameState.from_scenario(scenario)

        pickup = choose_turn_transition(state, scenario, "BFS")
        after_pickup = apply_action(state, scenario, pickup.action).estado
        block = choose_turn_transition(after_pickup, scenario, "BFS")
        result = apply_action(after_pickup, scenario, block.action)

        self.assertEqual(pickup.action.unidad_id, "A1")
        self.assertEqual(block.action.unidad_id, "B2")
        self.assertIsNone(result.estado.portador_recurso)
        self.assertEqual(
            result.estado.posicion_recurso,
            (scenario.recurso.fila, scenario.recurso.columna),
        )
        self.assertIsNone(result.pasos[-1].state.portador_recurso)
        self.assertEqual(
            result.pasos[-1].state.posicion_recurso,
            (scenario.recurso.fila, scenario.recurso.columna),
        )

    def test_endpoint_decides_valid_turn(self) -> None:
        result = asyncio.run(
            run_game_turn(
                UploadFile(
                    BytesIO(json.dumps(self.scenario.model_dump()).encode()),
                    filename="partida.json",
                ),
                "BFS",
                "MANHATTAN",
                4,
            )
        )

        self.assertEqual(result.estado.turno, "B")
        self.assertEqual(result.algoritmo, "BFS")
        self.assertEqual(result.accion.unidad_id, "A1")

    def test_endpoint_rejects_invalid_algorithm(self) -> None:
        with self.assertRaisesRegex(Exception, "No se pudo decidir el turno"):
            asyncio.run(
                run_game_turn(
                    UploadFile(
                        BytesIO(json.dumps(self.scenario.model_dump()).encode()),
                        filename="partida.json",
                    ),
                    "INVALID",
                    "MANHATTAN",
                    4,
                )
            )

    def test_endpoint_supports_five_consecutive_turns(self) -> None:
        current_scenario = self.scenario
        expected_turn = "A"

        for _ in range(5):
            state = GameState.from_scenario(current_scenario)
            result = asyncio.run(
                run_game_turn(
                    UploadFile(
                        BytesIO(json.dumps(current_scenario.model_dump()).encode()),
                        filename="partida.json",
                    ),
                    "BFS",
                    "MANHATTAN",
                    4,
                )
            )

            self.assertEqual(result.estado.turno, "B" if expected_turn == "A" else "A")
            if result.estado_partida != "en curso":
                break
            current_scenario = current_scenario.model_copy(
                update={
                    "unidades": [
                        unit.model_copy(
                            update={
                                "fila": next(
                                    item.posicion.fila
                                    for item in result.estado.unidades
                                    if item.id == unit.id
                                ),
                                "columna": next(
                                    item.posicion.columna
                                    for item in result.estado.unidades
                                    if item.id == unit.id
                                ),
                            }
                        )
                        for unit in current_scenario.unidades
                    ],
                    "turno": result.estado.turno,
                    "recurso": (
                        result.estado.posicion_recurso
                        or next(
                            item.posicion
                            for item in result.estado.unidades
                            if item.id == result.estado.portador_recurso
                        )
                        if result.estado.portador_recurso
                        else current_scenario.recurso
                    ),
                    "juego": current_scenario.juego.model_copy(
                        update={"portador_recurso": result.estado.portador_recurso}
                    ),
                }
            )
            expected_turn = result.estado.turno

        self.assertIn(expected_turn, {"A", "B"})

    def test_endpoint_returns_complete_simulation_history(self) -> None:
        result = asyncio.run(
            simulate_game(
                UploadFile(
                    BytesIO(json.dumps(self.scenario.model_dump()).encode()),
                    filename="partida.json",
                ),
                "BFS",
                "MANHATTAN",
                4,
            )
        )

        self.assertGreater(result.turnos_ejecutados, 0)
        self.assertEqual(result.turnos_ejecutados, len(result.historial))
        self.assertLessEqual(result.turnos_ejecutados, result.limite_turnos)

    def test_simulation_stops_when_blocked_resource_cycle_repeats(self) -> None:
        scenario = Escenario.model_validate(
            json.loads(
                (
                    Path("examples/good/escenario_bandera_bloqueada.json")
                ).read_text()
            )
        )
        result = asyncio.run(
            simulate_game(
                UploadFile(
                    BytesIO(json.dumps(scenario.model_dump()).encode()),
                    filename="partida_bloqueada.json",
                ),
                "BFS",
                "MANHATTAN",
                4,
            )
        )

        self.assertEqual(result.estado_final, "empate")
        self.assertIsNotNone(result.motivo_final)
        self.assertIn("Se detectó un bucle", result.motivo_final)
        self.assertLess(result.turnos_ejecutados, result.limite_turnos)

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
        result = asyncio.run(
            run_game_turn(
                UploadFile(
                    BytesIO(json.dumps(scenario.model_dump()).encode()),
                    filename="partida.json",
                ),
                "BFS",
                "MANHATTAN",
                4,
            )
        )
        self.assertEqual(result.estado_partida, "victoria_A")
        self.assertIsNone(result.turno_siguiente)

    def test_defender_chases_enemy_carrier_instead_of_own_base(self) -> None:
        state = GameState(
            unidades=(
                replace(
                    self.state.unidades[0],
                    posicion=(0, 1),
                ),
                replace(
                    self.state.unidades[1],
                    posicion=(3, 2),
                ),
            ),
            portador_recurso="A1",
            posicion_recurso=None,
            turno="B",
        )

        transition = choose_turn_transition(
            state,
            self.scenario,
            "BFS",
        )

        self.assertEqual(transition.action.unidad_id, "B1")
        self.assertEqual(transition.action.destino.fila, 2)
        self.assertEqual(transition.action.destino.columna, 2)


if __name__ == "__main__":
    unittest.main()
