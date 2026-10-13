import unittest

from backend.algorithms import bfs, dfs, ucs
from backend.models import Coordenada, Escenario


def build_search_scenario() -> Escenario:
    return Escenario.model_validate(
        {
            "version": "1.0",
            "mapa": {"filas": 5, "columnas": 5},
            "tipos_terreno": {
                "camino": {"costo": 1, "transitable": True},
                "muro": {"transitable": False},
            },
            "terreno": [
                ["camino", "camino", "muro", "camino", "camino"],
                ["camino", "camino", "muro", "camino", "camino"],
                ["camino", "camino", "camino", "camino", "camino"],
                ["camino", "camino", "camino", "camino", "camino"],
                ["camino", "camino", "camino", "camino", "camino"],
            ],
            "bases": {
                "A": {"fila": 0, "columna": 0},
                "B": {"fila": 4, "columna": 4},
            },
            "recurso": {"fila": 4, "columna": 0},
            "unidades": [
                {
                    "id": "A1",
                    "bando": "A",
                    "tipo": "estandar",
                    "fila": 0,
                    "columna": 0,
                },
                {
                    "id": "B1",
                    "bando": "B",
                    "tipo": "estandar",
                    "fila": 4,
                    "columna": 4,
                },
            ],
            "turno": "A",
            "juego": {
                "portador_recurso": None,
                "profundidad_maxima_minimax": 2,
            },
            "prueba": {
                "modo": "busqueda",
                "unidad_inicio": "A1",
                "objetivo": {"fila": 0, "columna": 4},
            },
        }
    )


def build_cost_scenario() -> Escenario:
    return Escenario.model_validate(
        {
            "version": "1.0",
            "mapa": {"filas": 3, "columnas": 5},
            "tipos_terreno": {
                "camino": {"costo": 1, "transitable": True},
                "barato": {"costo": 1, "transitable": True},
                "caro": {"costo": 8, "transitable": True},
            },
            "terreno": [
                ["camino", "caro", "caro", "caro", "camino"],
                ["barato", "barato", "barato", "barato", "barato"],
                ["barato", "barato", "barato", "barato", "barato"],
            ],
            "bases": {
                "A": {"fila": 0, "columna": 0},
                "B": {"fila": 2, "columna": 4},
            },
            "recurso": {"fila": 2, "columna": 0},
            "unidades": [
                {
                    "id": "A1",
                    "bando": "A",
                    "tipo": "estandar",
                    "fila": 0,
                    "columna": 0,
                },
                {
                    "id": "B1",
                    "bando": "B",
                    "tipo": "estandar",
                    "fila": 2,
                    "columna": 4,
                },
            ],
            "turno": "A",
            "juego": {
                "portador_recurso": None,
                "profundidad_maxima_minimax": 2,
            },
            "prueba": {
                "modo": "busqueda",
                "unidad_inicio": "A1",
                "objetivo": {"fila": 0, "columna": 4},
            },
        }
    )


class BlindSearchTests(unittest.TestCase):
    def test_bfs_finds_shortest_path_and_records_metrics(self) -> None:
        result = bfs(build_search_scenario())

        self.assertTrue(result.exito)
        self.assertEqual(result.longitud_camino, 8)
        self.assertEqual((result.camino[0].fila, result.camino[0].columna), (0, 0))
        self.assertEqual((result.camino[-1].fila, result.camino[-1].columna), (0, 4))
        self.assertGreaterEqual(result.estados_generados, result.estados_expandidos)
        self.assertGreaterEqual(result.maximo_frontera, 1)
        self.assertGreaterEqual(result.tiempo, 0)

    def test_dfs_finds_a_path_with_a_stack(self) -> None:
        result = dfs(build_search_scenario())

        self.assertTrue(result.exito)
        self.assertGreaterEqual(result.longitud_camino, 8)
        self.assertGreaterEqual(result.estados_generados, result.estados_expandidos)
        self.assertGreaterEqual(result.maximo_frontera, 1)
        self.assertGreaterEqual(result.tiempo, 0)

    def test_ucs_prefers_lower_cost_over_fewer_movements(self) -> None:
        scenario = build_cost_scenario()

        bfs_result = bfs(scenario)
        ucs_result = ucs(scenario)

        self.assertTrue(bfs_result.exito)
        self.assertTrue(ucs_result.exito)
        self.assertLess(bfs_result.longitud_camino, ucs_result.longitud_camino)
        self.assertGreater(bfs_result.costo, ucs_result.costo)
        self.assertEqual(ucs_result.costo, 6)

    def test_search_reports_failure_when_target_is_blocked(self) -> None:
        scenario = build_search_scenario()
        scenario = scenario.model_copy(
            update={
                "prueba": scenario.prueba.model_copy(
                    update={"objetivo": Coordenada(fila=0, columna=2)}
                )
            }
        )

        bfs_result = bfs(scenario)
        dfs_result = dfs(scenario)

        self.assertFalse(bfs_result.exito)
        self.assertFalse(dfs_result.exito)
        self.assertEqual(bfs_result.camino, [])
        self.assertEqual(dfs_result.camino, [])
        self.assertGreater(bfs_result.estados_expandidos, 0)
        self.assertGreater(dfs_result.estados_expandidos, 0)

    def test_search_requires_navigation_configuration(self) -> None:
        scenario = build_search_scenario().model_copy(update={"prueba": None})

        with self.assertRaises(ValueError):
            bfs(scenario)


if __name__ == "__main__":
    unittest.main()
