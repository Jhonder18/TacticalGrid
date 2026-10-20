import asyncio
import json
import unittest
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from fastapi.exceptions import HTTPException

from backend.main import run_search


EXAMPLES_DIR = Path(__file__).parents[2] / "examples"


class SearchEndpointTests(unittest.TestCase):
    RESULT_FIELDS = {
        "algoritmo",
        "exito",
        "camino",
        "costo",
        "longitud_camino",
        "estados_generados",
        "estados_expandidos",
        "maximo_frontera",
        "tiempo",
        "k",
    }

    def call_endpoint(self, filename: str, algorithm: str) -> Any:
        path = EXAMPLES_DIR / "good" / filename
        return asyncio.run(
            run_search(
                UploadFile(BytesIO(path.read_bytes()), filename=path.name),
                algorithm,
                "MANHATTAN",
                1,
            )
        )

    def test_runs_bfs_from_a_valid_scenario(self) -> None:
        result = self.call_endpoint("escenario_busqueda.json", "BFS")

        self.assertEqual(result.algoritmo, "BFS")
        self.assertTrue(result.exito)
        self.assertGreater(result.longitud_camino, 0)
        self.assertGreater(result.estados_generados, 0)

    def test_all_search_algorithms_return_the_same_schema(self) -> None:
        for algorithm in ("BFS", "DFS", "UCS", "A_ESTRELLA", "BEAM_SEARCH"):
            result = self.call_endpoint("escenario_busqueda.json", algorithm)

            self.assertEqual(set(result.model_dump()), self.RESULT_FIELDS)

    def test_runs_dfs_from_a_valid_scenario(self) -> None:
        result = self.call_endpoint("escenario_busqueda.json", "DFS")

        self.assertEqual(result.algoritmo, "DFS")
        self.assertTrue(result.exito)
        self.assertGreater(result.longitud_camino, 0)
        self.assertGreater(result.estados_generados, 0)

    def test_runs_ucs_from_a_valid_scenario(self) -> None:
        result = self.call_endpoint("escenario_busqueda.json", "UCS")

        self.assertEqual(result.algoritmo, "UCS")
        self.assertTrue(result.exito)
        self.assertGreater(result.longitud_camino, 0)
        self.assertGreater(result.estados_generados, 0)

    def test_runs_a_star_with_manhattan_from_a_valid_scenario(self) -> None:
        result = asyncio.run(
            run_search(
                UploadFile(
                    BytesIO(
                        (EXAMPLES_DIR / "good" / "escenario_busqueda.json")
                        .read_bytes()
                    ),
                    filename="escenario_busqueda.json",
                ),
                "A_ESTRELLA",
                "MANHATTAN",
            )
        )

        self.assertEqual(result.algoritmo, "A_ESTRELLA")
        self.assertTrue(result.exito)
        self.assertGreater(result.longitud_camino, 0)
        self.assertGreater(result.estados_generados, 0)

    def test_runs_a_star_with_euclidean_from_a_valid_scenario(self) -> None:
        result = asyncio.run(
            run_search(
                UploadFile(
                    BytesIO(
                        (EXAMPLES_DIR / "good" / "escenario_busqueda.json")
                        .read_bytes()
                    ),
                    filename="escenario_busqueda.json",
                ),
                "A_ESTRELLA",
                "EUCLIDEA",
            )
        )

        self.assertEqual(result.algoritmo, "A_ESTRELLA")
        self.assertTrue(result.exito)
        self.assertGreater(result.longitud_camino, 0)

    def test_runs_beam_search_with_k(self) -> None:
        path = EXAMPLES_DIR / "good" / "escenario_busqueda.json"
        result = asyncio.run(
            run_search(
                UploadFile(BytesIO(path.read_bytes()), filename=path.name),
                "BEAM_SEARCH",
                "MANHATTAN",
                2,
            )
        )

        self.assertEqual(result.algoritmo, "BEAM_SEARCH")
        self.assertTrue(result.exito)
        self.assertLessEqual(result.maximo_frontera, 2)

    def test_returns_bad_request_when_search_configuration_is_missing(self) -> None:
        path = EXAMPLES_DIR / "good" / "escenario_busqueda.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["prueba"] = None
        upload = UploadFile(
            BytesIO(json.dumps(payload).encode("utf-8")),
            filename="without-test.json",
        )

        with self.assertRaises(HTTPException) as context:
            asyncio.run(run_search(upload, "BFS"))

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("configuración de prueba", context.exception.detail)


if __name__ == "__main__":
    unittest.main()
