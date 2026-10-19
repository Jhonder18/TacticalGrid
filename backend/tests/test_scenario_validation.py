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

    def test_static_demonstration_cases_are_accepted(self) -> None:
        for path in sorted((EXAMPLES_DIR / "good").glob("caso_*.json")):
            with self.subTest(path=path.name):
                self.assertEqual(self.call_endpoint(path)["valido"], True)

    def test_bad_examples_are_rejected(self) -> None:
        expected_messages = {
            "dimensiones_inconsistentes.json": "matriz terreno",
            "terreno_desconocido.json": "terrenos no definidos",
            "posicion_fuera_del_mapa.json": "fuera del mapa",
            "unidad_sobre_obstaculo.json": "unidad A1",
            "base_sobre_obstaculo.json": "Base A",
            "recurso_sobre_obstaculo.json": "Recurso",
            "portador_desincronizado.json": "misma posición que el recurso",
            "unidad_inicio_inexistente.json": "unidad_inicio debe identificar una unidad existente",
            "objetivo_sobre_obstaculo.json": "El objetivo está sobre un terreno no transitable",
            "unidades_superpuestas.json": "posiciones iniciales de las unidades no pueden repetirse",
            "bases_iguales.json": "Las bases A y B deben estar en posiciones diferentes",
            "orden_direcciones_repetidas.json": "no puede contener direcciones repetidas",
            "profundidad_fuera_de_rango.json": "profundidad_maxima_minimax",
        }
        for filename, message in expected_messages.items():
            with self.subTest(filename=filename):
                self.assert_rejected(EXAMPLES_DIR / "bad" / filename, message)

    def test_search_mode_requires_unit_and_objective(self) -> None:
        base = json.loads(
            (EXAMPLES_DIR / "fixtures" / "ucs_demo.json").read_text(encoding="utf-8")
        )

        missing_unit = json.loads(json.dumps(base))
        missing_unit["prueba"]["unidad_inicio"] = None
        self.assert_rejected_payload(missing_unit, "debe indicar unidad_inicio")

        missing_objective = json.loads(json.dumps(base))
        missing_objective["prueba"]["objetivo"] = None
        self.assert_rejected_payload(missing_objective, "debe indicar objetivo")

    def assert_rejected_payload(
        self,
        payload: dict[str, Any],
        expected_message: str,
    ) -> None:
        file = UploadFile(
            BytesIO(json.dumps(payload).encode("utf-8")),
            filename="payload.json",
        )
        with self.assertRaises(HTTPException) as context:
            asyncio.run(validate_scenario(file))
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn(expected_message, context.exception.detail)

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
