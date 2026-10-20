import re
import unittest
from pathlib import Path

from backend.algorithms.adversarial import MAX_MINIMAX_DEPTH
from backend.core.utility import (
    TERMINAL_WIN_UTILITY,
    WEIGHT_PROGRESS,
    WEIGHT_RESOURCE,
    WEIGHT_THREAT,
)

DOC = Path(__file__).parents[2] / "docs" / "heuristicas_y_utilidad.md"


class DocumentationConsistencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            DOC.exists(),
            "Falta docs/heuristicas_y_utilidad.md",
        )
        self.document = DOC.read_text(encoding="utf-8")

    def test_document_mentions_all_required_sections(self) -> None:
        required = [
            "f(n) = g(n) + h(n)",
            "Distancia Manhattan",
            "Distancia Euclidiana",
            "Costo computacional",
            "Admisibilidad",
            "evaluate_utility",
            "TERMINAL_WIN_UTILITY",
            "MAX",
            "MIN",
            "orden_sucesores",
        ]
        for term in required:
            with self.subTest(term=term):
                self.assertIn(term, self.document)

    def test_documented_weights_match_code(self) -> None:
        for weight in (WEIGHT_RESOURCE, WEIGHT_PROGRESS, WEIGHT_THREAT):
            with self.subTest(weight=weight):
                self.assertIn(f"{weight:.2f}", self.document)

    def test_documented_terminal_value_matches_code(self) -> None:
        self.assertIn("100000", self.document)
        self.assertEqual(TERMINAL_WIN_UTILITY, 100_000.0)
        self.assertIn("±100000", self.document)

    def test_documented_depth_limit_matches_code(self) -> None:
        self.assertEqual(MAX_MINIMAX_DEPTH, 8)
        self.assertIn("MAX_MINIMAX_DEPTH = 8", self.document)

    def test_admissibility_values_are_consistent(self) -> None:
        weights = "0.30 × proximity"
        self.assertIn(weights, self.document)
        self.assertAlmostEqual(
            WEIGHT_RESOURCE + WEIGHT_PROGRESS + WEIGHT_THREAT,
            1.0,
            places=9,
        )

    def test_traceability_references_real_files(self) -> None:
        references = re.findall(r"`(backend/[\w/]+\.py):\d+`", self.document)
        self.assertGreater(len(references), 10)
        root = Path(__file__).parents[2]
        for reference in references:
            with self.subTest(reference=reference):
                self.assertTrue((root / reference).exists())


if __name__ == "__main__":
    unittest.main()
