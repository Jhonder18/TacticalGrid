import json
import unittest
from pathlib import Path

from backend.algorithms import a_star, beam_search, bfs, dfs, ucs
from backend.core.route_verification import (
    recalcular_costo,
    verificar_objetivo,
    verificar_resultado_busqueda,
    verificar_ruta_continua,
    verificar_ruta_transitable,
)
from backend.models import Coordenada, Escenario, ResultadoBusqueda


EXAMPLES_DIR = Path(__file__).parents[2] / "examples"


def load_case(filename: str) -> Escenario:
    payload = json.loads((EXAMPLES_DIR / "good" / filename).read_text(encoding="utf-8"))
    return Escenario.model_validate(payload)


def load_external(filename: str) -> Escenario:
    payload = json.loads((EXAMPLES_DIR / filename).read_text(encoding="utf-8"))
    return Escenario.model_validate(payload)


class RouteIntegrityTests(unittest.TestCase):
    def test_all_algorithms_produce_verifiable_routes(self) -> None:
        scenario = load_case("caso_1_bfs_dfs.json")
        executions = {
            "BFS": lambda: bfs(scenario),
            "DFS": lambda: dfs(scenario),
            "UCS": lambda: ucs(scenario),
            "A*_MANHATTAN": lambda: a_star(scenario, "MANHATTAN"),
            "A*_EUCLIDEA": lambda: a_star(scenario, "EUCLIDEA"),
            "BEAM_SEARCH": lambda: beam_search(scenario, 8),
        }
        for name, run in executions.items():
            with self.subTest(algoritmo=name):
                result = run()
                verificar_resultado_busqueda(scenario, result)

    def test_routes_do_not_cross_obstacles(self) -> None:
        scenario = load_case("caso_3_obstaculo_astar.json")
        for run in (bfs, ucs, lambda s: a_star(s, "MANHATTAN")):
            with self.subTest(algoritmo=run):
                result = run(scenario)
                verificar_ruta_transitable(scenario, result)

    def test_recalculated_cost_matches_ucs(self) -> None:
        scenario = load_external("externo_busqueda_costos.json")
        result = ucs(scenario)
        self.assertTrue(result.exito)
        self.assertAlmostEqual(
            recalcular_costo(scenario, result),
            result.costo,
        )


class ReproducibleCaseTests(unittest.TestCase):
    def test_case_1_bfs_is_not_longer_than_dfs(self) -> None:
        scenario = load_case("caso_1_bfs_dfs.json")
        bfs_result = bfs(scenario)
        dfs_result = dfs(scenario)
        self.assertTrue(bfs_result.exito)
        self.assertTrue(dfs_result.exito)
        self.assertLessEqual(
            bfs_result.longitud_camino,
            dfs_result.longitud_camino,
        )
        verificar_resultado_busqueda(scenario, bfs_result)
        verificar_resultado_busqueda(scenario, dfs_result)

    def test_case_2_bfs_shortest_ucs_cheapest(self) -> None:
        scenario = load_case("caso_2_bfs_ucs.json")
        bfs_result = bfs(scenario)
        ucs_result = ucs(scenario)
        self.assertLessEqual(
            bfs_result.longitud_camino,
            ucs_result.longitud_camino,
        )
        self.assertLessEqual(ucs_result.costo, bfs_result.costo)
        verificar_resultado_busqueda(scenario, ucs_result)

    def test_case_3_astar_goes_around_obstacle(self) -> None:
        scenario = load_case("caso_3_obstaculo_astar.json")
        result = a_star(scenario, "MANHATTAN")
        verificar_resultado_busqueda(scenario, result)

    def test_case_4_heuristics_reach_same_optimal_cost(self) -> None:
        scenario = load_case("caso_4_heuristicas.json")
        manhattan = a_star(scenario, "MANHATTAN")
        euclidean = a_star(scenario, "EUCLIDEA")
        self.assertEqual(manhattan.costo, euclidean.costo)
        verificar_resultado_busqueda(scenario, manhattan)
        verificar_resultado_busqueda(scenario, euclidean)

    def test_case_5_beam_reaches_objective(self) -> None:
        scenario = load_case("caso_5_beam.json")
        result = beam_search(scenario, 4)
        verificar_resultado_busqueda(scenario, result)


class BeamWidthTests(unittest.TestCase):
    def test_beam_respects_frontier_for_each_k(self) -> None:
        scenario = load_case("caso_5_beam.json")
        for k in (1, 2, 4, 8):
            with self.subTest(k=k):
                result = beam_search(scenario, k)
                self.assertEqual(result.algoritmo, "BEAM_SEARCH")
                self.assertEqual(result.k, k)
                self.assertLessEqual(result.maximo_frontera, k)

    def test_beam_failure_is_reported_with_width(self) -> None:
        scenario = load_case("caso_5_beam.json")
        scenario = scenario.model_copy(
            update={
                "prueba": scenario.prueba.model_copy(
                    update={"objetivo": Coordenada(fila=0, columna=0)}
                )
            }
        )
        result = beam_search(scenario, 1)
        self.assertEqual(result.k, 1)


class InvalidRouteTests(unittest.TestCase):
    def build_valid_result(self) -> tuple[Escenario, ResultadoBusqueda]:
        scenario = load_case("caso_1_bfs_dfs.json")
        return scenario, bfs(scenario)

    def test_detects_discontinuous_route(self) -> None:
        scenario, result = self.build_valid_result()
        broken = result.model_copy(
            update={
                "camino": [result.camino[0], result.camino[-1]],
                "longitud_camino": 1,
            }
        )
        with self.assertRaises(AssertionError):
            verificar_ruta_continua(broken)

    def test_detects_route_through_wall(self) -> None:
        scenario = load_case("caso_3_obstaculo_astar.json")
        wall = self._find_wall(scenario)
        forged = ResultadoBusqueda(
            algoritmo="BFS",
            exito=True,
            camino=[wall],
            costo=0.0,
            longitud_camino=0,
            estados_generados=1,
            estados_expandidos=0,
            maximo_frontera=1,
            tiempo=0.0,
        )
        with self.assertRaises(AssertionError):
            verificar_ruta_transitable(scenario, forged)

    def test_detects_wrong_objective(self) -> None:
        scenario, result = self.build_valid_result()
        wrong = result.model_copy(
            update={"camino": [result.camino[0]]}
        )
        with self.assertRaises(AssertionError):
            verificar_objetivo(scenario, wrong)

    def test_detects_inconsistent_cost(self) -> None:
        scenario, result = self.build_valid_result()
        wrong = result.model_copy(update={"costo": result.costo + 100})
        with self.assertRaises(AssertionError):
            verificar_resultado_busqueda(scenario, wrong)

    def _find_wall(self, scenario: Escenario) -> Coordenada:
        for fila, row in enumerate(scenario.terreno):
            for columna, nombre in enumerate(row):
                if not scenario.tipos_terreno[nombre].transitable:
                    return Coordenada(fila=fila, columna=columna)
        raise AssertionError("El escenario no tiene obstáculos")


if __name__ == "__main__":
    unittest.main()
