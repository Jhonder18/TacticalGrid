import asyncio
import json
from io import BytesIO
from pathlib import Path
from typing import Any
import unittest

from fastapi import UploadFile
from fastapi.exceptions import HTTPException

from backend.main import validate_scenario


EXAMPLES_DIR = Path(__file__).parents[2] / "examples"


def upload_for(path: Path) -> UploadFile:
    return UploadFile(
        BytesIO(path.read_bytes()),
        filename=path.name,
    )


class ScenarioValidationTests(unittest.TestCase):
    def call_endpoint(self, path: Path) -> dict[str, Any]:
        return asyncio.run(validate_scenario(upload_for(path)))

    def assert_rejected(self, path: Path, expected_message: str) -> None:
        with self.assertRaises(HTTPException) as context:
            self.call_endpoint(path)
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn(expected_message, context.exception.detail)

    def test_good_examples_are_accepted(self) -> None:
        for path in sorted((EXAMPLES_DIR / "good").glob("*.json")):
            with self.subTest(path=path.name):
                response = self.call_endpoint(path)
                self.assertEqual(response["valido"], True)

    def test_bad_examples_are_rejected(self) -> None:
        expected_messages = {
            "dimensiones_inconsistentes.json": "matriz terreno",
            "terreno_desconocido.json": "terrenos no definidos",
            "posicion_fuera_del_mapa.json": "fuera del mapa",
            "unidad_sobre_obstaculo.json": "unidad A1",
            "base_sobre_obstaculo.json": "Base A",
            "recurso_sobre_obstaculo.json": "Recurso",
            "portador_desincronizado.json": "misma posición que el recurso",
        }
        for filename, message in expected_messages.items():
            with self.subTest(filename=filename):
                self.assert_rejected(EXAMPLES_DIR / "bad" / filename, message)

    def test_non_json_file_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as context:
            asyncio.run(
                validate_scenario(
                    UploadFile(BytesIO(b"{}"), filename="scenario.txt")
                )
            )
        self.assertEqual(context.exception.status_code, 400)

    def test_malformed_json_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as context:
            asyncio.run(
                validate_scenario(
                    UploadFile(BytesIO(b'{"version":'), filename="broken.json")
                )
            )
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("JSON válido", context.exception.detail)


if __name__ == "__main__":
    unittest.main()
