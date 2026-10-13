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
    def call_endpoint(self, filename: str, algorithm: str) -> Any:
        path = EXAMPLES_DIR / "good" / filename
        return asyncio.run(
            run_search(
                UploadFile(BytesIO(path.read_bytes()), filename=path.name),
                algorithm,
            )
        )

    def test_runs_bfs_from_a_valid_scenario(self) -> None:
        result = self.call_endpoint("escenario_busqueda.json", "BFS")

        self.assertEqual(result.algoritmo, "BFS")
        self.assertTrue(result.exito)
        self.assertGreater(result.longitud_camino, 0)
        self.assertGreater(result.estados_generados, 0)

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
