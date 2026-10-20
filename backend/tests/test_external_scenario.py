"""Compatibilidad con escenarios externos no preparados previamente.

Purpose:
    Comprobar que los algoritmos, la decisión adversarial y la simulación de
    partidas funcionan con escenarios externos sin depender de los ejemplos
    internos ni de posiciones codificadas en el código.
Preconditions:
    Los archivos ``examples/externo_*.json`` y ``examples/bad/externo_*.json``
    deben existir.
Postconditions:
    Todos los escenarios externos se procesan correctamente y la variante
    inválida se rechaza.
Complexity:
    O(T · (u + b^d)) por la simulación de partida; el resto es lineal respecto
    al tamaño del árbol explorado.
AI usage:
    No.
AI intervention:
    Se redactaron las aserciones a partir de los resultados observados.
Student validation:
    Se revisará la carga de los externos desde el selector de archivos.
"""

import asyncio
import json
import re
import unittest
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from fastapi.exceptions import HTTPException

from backend.algorithms import a_star, alpha_beta, beam_search, bfs, minimax, ucs
from backend.core.game_simulation import simular_partida
from backend.core.route_verification import (
    recalcular_costo,
    verificar_resultado_busqueda,
)
from backend.main import validate_scenario
from backend.models import Escenario


EXAMPLES_DIR = Path(__file__).parents[2] / "examples"
ALGORITHMS_DIR = Path(__file__).parents[1] / "algorithms"


def load_external(filename: str) -> Escenario:
    payload = json.loads(
        (EXAMPLES_DIR / filename).read_text(encoding="utf-8")
    )
    return Escenario.model_validate(payload)


class ExternalSearchTests(unittest.TestCase):
    def test_external_cost_scenario_search_algorithms_run(self) -> None:
        scenario = load_external("externo_busqueda_costos.json")
        executions = {
            "BFS": lambda: bfs(scenario),
            "UCS": lambda: ucs(scenario),
            "A*_MANHATTAN": lambda: a_star(scenario, "MANHATTAN"),
            "A*_EUCLIDEA": lambda: a_star(scenario, "EUCLIDEA"),
            "BEAM_SEARCH": lambda: beam_search(scenario, 4),
        }
        for name, run in executions.items():
            with self.subTest(algoritmo=name):
                result = run()
                self.assertTrue(result.exito)
                verificar_resultado_busqueda(scenario, result)

    def test_external_costs_are_read_from_json(self) -> None:
        scenario = load_external("externo_busqueda_costos.json")
        for name, run in (
            ("UCS", ucs),
            ("A*_MANHATTAN", lambda s: a_star(s, "MANHATTAN")),
        ):
            with self.subTest(algoritmo=name):
                result = run(scenario)
                self.assertAlmostEqual(
                    recalcular_costo(scenario, result),
                    result.costo,
                )

    def test_external_walled_objective_reports_failure(self) -> None:
        scenario = load_external("externo_busqueda_muro.json")
        for name, run in (
            ("BFS", bfs),
            ("UCS", ucs),
            ("A*_MANHATTAN", lambda s: a_star(s, "MANHATTAN")),
            ("BEAM_SEARCH", lambda s: beam_search(s, 4)),
        ):
            with self.subTest(algoritmo=name):
                result = run(scenario)
                self.assertFalse(result.exito)
                self.assertEqual(result.longitud_camino, 0)


class ExternalAdversarialTests(unittest.TestCase):
    def test_external_adversarial_alpha_beta_prunes(self) -> None:
        scenario = load_external("externo_adversarial_3v3.json")
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


class ExternalGameTests(unittest.TestCase):
    def test_external_game_simulation_reaches_terminal_state(self) -> None:
        scenario = load_external("externo_partida_3v3.json")
        simulation = simular_partida(scenario)
        self.assertGreater(simulation.turnos_ejecutados, 0)
        self.assertEqual(len(simulation.historial), simulation.turnos_ejecutados)
        self.assertNotEqual(simulation.estado_final, "en curso")
        for turn in simulation.historial:
            self.assertTrue(turn.pasos)


class ExternalValidationTests(unittest.TestCase):
    def call_endpoint(self, path: Path) -> dict:
        file = UploadFile(BytesIO(path.read_bytes()), filename=path.name)
        return asyncio.run(validate_scenario(file))

    def test_external_valid_scenarios_are_accepted(self) -> None:
        for path in sorted(EXAMPLES_DIR.glob("externo_*.json")):
            with self.subTest(path=path.name):
                self.assertTrue(self.call_endpoint(path)["valido"])

    def test_external_invalid_variant_is_rejected(self) -> None:
        path = EXAMPLES_DIR / "bad" / "externo_costo_negativo.json"
        file = UploadFile(BytesIO(path.read_bytes()), filename=path.name)
        with self.assertRaises(HTTPException) as context:
            asyncio.run(validate_scenario(file))
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("greater than 0", context.exception.detail)


class NoHardcodedPositionsTests(unittest.TestCase):
    def test_algorithms_have_no_literal_coordinates(self) -> None:
        pattern = re.compile(r"\(\s*\d+\s*,\s*\d+\s*\)")
        for path in sorted(ALGORITHMS_DIR.glob("*.py")):
            with self.subTest(archivo=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertIsNone(
                    pattern.search(source),
                    f"{path.name} contiene coordenadas literales",
                )

    def test_algorithms_have_no_literal_map_dimensions(self) -> None:
        pattern = re.compile(
            r"\b(filas|columnas)\s*==\s*\d+|\b(filas|columnas)\s*=\s*\d+"
        )
        for path in sorted(ALGORITHMS_DIR.glob("*.py")):
            with self.subTest(archivo=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertIsNone(
                    pattern.search(source),
                    f"{path.name} codifica dimensiones del mapa",
                )


if __name__ == "__main__":
    unittest.main()
