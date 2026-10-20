import asyncio
import json
import unittest
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile

from backend.algorithms import alpha_beta, minimax
from backend.core.adversarial_comparison import comparar_adversarial
from backend.core.adversarial_report import (
    generar_reporte,
    registro_comparacion,
)
from backend.main import compare_adversarial
from backend.models import Escenario

EXAMPLES = Path(__file__).parents[2] / "examples" / "good"
REPORT = (
    Path(__file__).parents[2]
    / "examples"
    / "reportes"
    / "adversarial_casos_6_10.json"
)


def load_case(filename: str) -> Escenario:
    return Escenario.model_validate(
        json.loads((EXAMPLES / filename).read_text(encoding="utf-8"))
    )


def with_depth(scenario: Escenario, depth: int) -> Escenario:
    return scenario.model_copy(
        update={
            "juego": scenario.juego.model_copy(
                update={"profundidad_maxima_minimax": depth}
            )
        }
    )


class AdversarialComparisonTests(unittest.TestCase):
    def test_cases_6_to_10_share_action_value_and_depth(self) -> None:
        for filename in (
            "caso_6_portador_a.json",
            "caso_6_portador_b.json",
            "caso_7_intercepcion.json",
            "caso_8_poda.json",
            "caso_9_orden_poda.json",
            "caso_10_profundidades.json",
        ):
            with self.subTest(filename=filename):
                scenario = load_case(filename)
                result = comparar_adversarial(scenario)
                self.assertTrue(result.misma_accion)
                self.assertTrue(result.mismo_valor)
                self.assertEqual(
                    result.profundidad,
                    scenario.juego.profundidad_maxima_minimax,
                )
                self.assertEqual(
                    result.minimax.profundidad_alcanzada,
                    result.alpha_beta.profundidad_alcanzada,
                )

    def test_case_8_alpha_beta_generates_fewer_nodes(self) -> None:
        result = comparar_adversarial(load_case("caso_8_poda.json"))
        self.assertLess(
            result.alpha_beta.nodos_generados,
            result.minimax.nodos_generados,
        )
        self.assertGreater(result.alpha_beta.nodos_podados, 0)

    def test_case_9_ordered_successors_improve_pruning(self) -> None:
        scenario = load_case("caso_9_orden_poda.json")
        ordered = comparar_adversarial(scenario)
        default = comparar_adversarial(
            scenario.model_copy(update={"orden_sucesores": None})
        )
        self.assertTrue(ordered.misma_accion)
        self.assertTrue(default.misma_accion)
        self.assertLess(
            ordered.alpha_beta.nodos_generados,
            default.alpha_beta.nodos_generados,
        )

    def test_case_10_depths_increase_load_for_both_algorithms(self) -> None:
        base = load_case("caso_10_profundidades.json")
        minimax_generated = []
        alpha_beta_generated = []
        for depth in (2, 3, 5):
            result = comparar_adversarial(with_depth(base, depth))
            self.assertEqual(result.minimax.profundidad_alcanzada, depth)
            self.assertEqual(result.alpha_beta.profundidad_alcanzada, depth)
            self.assertTrue(result.misma_accion)
            self.assertTrue(result.mismo_valor)
            minimax_generated.append(result.minimax.nodos_generados)
            alpha_beta_generated.append(result.alpha_beta.nodos_generados)
        self.assertLess(minimax_generated[0], minimax_generated[1])
        self.assertLess(minimax_generated[1], minimax_generated[2])
        self.assertLess(alpha_beta_generated[0], alpha_beta_generated[1])
        self.assertLess(alpha_beta_generated[1], alpha_beta_generated[2])

    def test_reduction_percentage_matches_node_counts(self) -> None:
        result = comparar_adversarial(load_case("caso_8_poda.json"))
        expected = (
            (result.minimax.nodos_generados - result.alpha_beta.nodos_generados)
            / result.minimax.nodos_generados
            * 100.0
        )
        self.assertAlmostEqual(result.reduccion_nodos_porcentaje, expected, places=9)
        self.assertGreater(result.reduccion_nodos_porcentaje, 0.0)
        self.assertLessEqual(result.reduccion_nodos_porcentaje, 100.0)

    def test_compare_endpoint_returns_structured_comparison(self) -> None:
        payload = load_case("caso_8_poda.json").model_dump()
        result = asyncio.run(
            compare_adversarial(
                UploadFile(
                    BytesIO(json.dumps(payload).encode("utf-8")),
                    filename="caso_8_poda.json",
                ),
                None,
            )
        )
        self.assertTrue(result.misma_accion)
        self.assertTrue(result.mismo_valor)
        self.assertEqual(result.profundidad, 4)
        self.assertLess(
            result.alpha_beta.nodos_generados,
            result.minimax.nodos_generados,
        )

    def test_report_entry_is_reproducible_and_time_free(self) -> None:
        scenario = load_case("caso_8_poda.json")
        entry = registro_comparacion("caso_8_poda", comparar_adversarial(scenario))
        self.assertEqual(entry["escenario"], "caso_8_poda")
        self.assertNotIn("tiempo", entry)
        for algorithm_key in ("minimax", "alpha_beta"):
            self.assertNotIn("tiempo", entry[algorithm_key])
            self.assertIn("nodos_generados", entry[algorithm_key])
            self.assertIn("accion_seleccionada", entry[algorithm_key])
        self.assertEqual(entry["minimax"]["algoritmo"], "MINIMAX")
        self.assertEqual(entry["alpha_beta"]["algoritmo"], "ALFA_BETA")
        self.assertEqual(entry["minimax"]["nodos_generados"], minimax(scenario).nodos_generados)
        self.assertEqual(
            entry["alpha_beta"]["nodos_generados"],
            alpha_beta(scenario).nodos_generados,
        )

    def test_generated_report_file_matches_live_execution(self) -> None:
        self.assertTrue(REPORT.exists(), "Falta el reporte generado")
        entries = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(entries), 9)
        by_name = {entry["escenario"]: entry for entry in entries}
        live = registro_comparacion(
            "caso_8_poda", comparar_adversarial(load_case("caso_8_poda.json"))
        )
        self.assertEqual(by_name["caso_8_poda"], live)

    def test_generar_reporte_returns_one_entry_per_case(self) -> None:
        casos = [
            ("a", with_depth(load_case("caso_10_profundidades.json"), 2)),
            ("b", with_depth(load_case("caso_10_profundidades.json"), 3)),
        ]
        entradas = generar_reporte(casos)
        self.assertEqual(len(entradas), 2)
        self.assertEqual([entry["escenario"] for entry in entradas], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
