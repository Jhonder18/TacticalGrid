import unittest

from backend.algorithms import alpha_beta, minimax
from backend.main import run_adversarial
from backend.models import Escenario, GameState
from fastapi import UploadFile
from io import BytesIO
import asyncio
import json
from pathlib import Path


def build_scenario(depth: int = 2) -> Escenario:
    return Escenario.model_validate(
        {
            "version": "1.0",
            "mapa": {"filas": 3, "columnas": 3},
            "tipos_terreno": {
                "camino": {"costo": 1, "transitable": True},
            },
            "terreno": [["camino"] * 3 for _ in range(3)],
            "bases": {
                "A": {"fila": 0, "columna": 0},
                "B": {"fila": 2, "columna": 2},
            },
            "recurso": {"fila": 1, "columna": 1},
            "unidades": [
                {
                    "id": "A1",
                    "bando": "A",
                    "tipo": "explorador",
                    "fila": 1,
                    "columna": 0,
                },
                {
                    "id": "B1",
                    "bando": "B",
                    "tipo": "defensor",
                    "fila": 2,
                    "columna": 1,
                },
            ],
            "turno": "A",
            "juego": {
                "portador_recurso": None,
                "profundidad_maxima_minimax": depth,
            },
            "prueba": {"modo": "adversarial"},
        }
    )


class MinimaxTests(unittest.TestCase):
    def test_minimax_returns_root_action_and_tree_metrics(self) -> None:
        result = minimax(build_scenario())

        self.assertEqual(result.algoritmo, "MINIMAX")
        self.assertIsNotNone(result.accion_seleccionada)
        self.assertGreater(result.nodos_generados, 1)
        self.assertGreater(result.nodos_evaluados, 0)
        self.assertEqual(result.profundidad_alcanzada, 2)
        self.assertGreaterEqual(result.nodos_podados, 0)

    def test_minimax_stops_at_configured_depth(self) -> None:
        result = minimax(build_scenario(depth=1))

        self.assertEqual(result.profundidad_alcanzada, 1)
        self.assertGreater(result.nodos_evaluados, 0)

    def test_minimax_rejects_non_positive_depth(self) -> None:
        with self.assertRaises(ValueError):
            minimax(build_scenario(depth=0))

    def test_minimax_rejects_depth_above_project_limit(self) -> None:
        with self.assertRaises(ValueError):
            minimax(build_scenario(depth=9))

    def test_alpha_beta_returns_same_decision_and_value_as_minimax(self) -> None:
        scenario = build_scenario(depth=4)

        minimax_result = minimax(scenario)
        alpha_beta_result = alpha_beta(scenario)

        self.assertEqual(
            alpha_beta_result.accion_seleccionada,
            minimax_result.accion_seleccionada,
        )
        self.assertEqual(alpha_beta_result.valor_obtenido, minimax_result.valor_obtenido)
        self.assertEqual(alpha_beta_result.profundidad_alcanzada, 4)
        self.assertGreater(alpha_beta_result.nodos_podados, 0)
        self.assertLess(
            alpha_beta_result.nodos_generados,
            minimax_result.nodos_generados,
        )

    def test_alpha_beta_rejects_depth_above_project_limit(self) -> None:
        with self.assertRaises(ValueError):
            alpha_beta(build_scenario(depth=9))

    def test_adversarial_endpoint_returns_structured_decision(self) -> None:
        payload = build_scenario(depth=2).model_dump()
        result = asyncio.run(
            run_adversarial(
                UploadFile(
                    BytesIO(json.dumps(payload).encode("utf-8")),
                    filename="adversarial.json",
                ),
                "ALFA_BETA",
                1,
            )
        )

        self.assertEqual(result.algoritmo, "ALFA_BETA")
        self.assertIsNotNone(result.accion_seleccionada)
        self.assertEqual(result.profundidad_alcanzada, 1)
        self.assertEqual(result.arbol.id, "root")
        self.assertGreater(len(result.arbol.hijos), 0)

    def test_case_6_same_map_with_different_carrier_is_a_different_state(self) -> None:
        examples = Path(__file__).parents[2] / "examples" / "good"
        carrier_a = Escenario.model_validate(
            json.loads((examples / "caso_6_portador_a.json").read_text())
        )
        carrier_b = Escenario.model_validate(
            json.loads((examples / "caso_6_portador_b.json").read_text())
        )
        self.assertEqual(carrier_a.terreno, carrier_b.terreno)
        self.assertEqual(carrier_a.unidades, carrier_b.unidades)
        self.assertEqual(carrier_a.turno, carrier_b.turno)
        self.assertEqual(carrier_a.recurso, carrier_b.recurso)
        self.assertEqual(carrier_a.juego.portador_recurso, "A1")
        self.assertEqual(carrier_b.juego.portador_recurso, "B1")
        self.assertNotEqual(
            GameState.from_scenario(carrier_a).state_key(),
            GameState.from_scenario(carrier_b).state_key(),
        )

    def test_cases_7_and_8_preserve_decision_and_alpha_beta_prunes(self) -> None:
        examples = Path(__file__).parents[2] / "examples" / "good"
        for filename in ("caso_7_intercepcion.json", "caso_8_poda.json"):
            with self.subTest(filename=filename):
                scenario = Escenario.model_validate(
                    json.loads((examples / filename).read_text())
                )
                minimax_result = minimax(scenario)
                alpha_beta_result = alpha_beta(scenario)
                self.assertEqual(
                    alpha_beta_result.accion_seleccionada,
                    minimax_result.accion_seleccionada,
                )
                self.assertEqual(
                    alpha_beta_result.valor_obtenido,
                    minimax_result.valor_obtenido,
                )
                self.assertLess(
                    alpha_beta_result.nodos_generados,
                    minimax_result.nodos_generados,
                )

    def test_case_7_intercepts_carrier_instead_of_chasing_free_resource(self) -> None:
        examples = Path(__file__).parents[2] / "examples" / "good"
        scenario = Escenario.model_validate(
            json.loads((examples / "caso_7_intercepcion.json").read_text())
        )
        result = minimax(scenario)
        action = result.accion_seleccionada
        self.assertIsNotNone(action)
        self.assertEqual(action.unidad_id, "A1")
        carrier = next(unit for unit in scenario.unidades if unit.id == "B1")
        self.assertLess(
            abs(action.destino.fila - carrier.fila)
            + abs(action.destino.columna - carrier.columna),
            abs(action.origen.fila - carrier.fila)
            + abs(action.origen.columna - carrier.columna),
        )

    def test_case_9_successor_order_increases_pruning(self) -> None:
        examples = Path(__file__).parents[2] / "examples" / "good"
        scenario = Escenario.model_validate(
            json.loads((examples / "caso_9_orden_poda.json").read_text())
        )
        default_order = scenario.model_copy(update={"orden_sucesores": None})
        ordered_result = alpha_beta(scenario)
        default_result = alpha_beta(default_order)
        self.assertEqual(
            ordered_result.accion_seleccionada,
            default_result.accion_seleccionada,
        )
        self.assertLess(ordered_result.nodos_generados, default_result.nodos_generados)
        self.assertGreater(ordered_result.nodos_podados, 0)

    def test_case_10_depths_increase_minimax_load(self) -> None:
        examples = Path(__file__).parents[2] / "examples" / "good"
        base = Escenario.model_validate(
            json.loads((examples / "caso_10_profundidades.json").read_text())
        )
        generated = []
        for depth in (2, 3, 5):
            scenario = base.model_copy(
                update={
                    "juego": base.juego.model_copy(
                        update={"profundidad_maxima_minimax": depth}
                    )
                }
            )
            result = minimax(scenario)
            self.assertEqual(result.profundidad_alcanzada, depth)
            generated.append(result.nodos_generados)
        self.assertLess(generated[0], generated[1])
        self.assertLess(generated[1], generated[2])


if __name__ == "__main__":
    unittest.main()
