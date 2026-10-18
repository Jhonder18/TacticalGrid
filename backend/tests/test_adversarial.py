import unittest

from backend.algorithms import alpha_beta, minimax
from backend.main import run_adversarial
from backend.models import Escenario
from fastapi import UploadFile
from io import BytesIO
import asyncio
import json


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


if __name__ == "__main__":
    unittest.main()
