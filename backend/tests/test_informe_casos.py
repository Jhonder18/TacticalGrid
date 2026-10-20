import json
import unittest
from pathlib import Path

from backend.core.informe import generar_informe, informe_busqueda

REPORT = (
    Path(__file__).parents[2]
    / "examples"
    / "reportes"
    / "informe_casos_1_10.json"
)


class InformeCasosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.informe = generar_informe()

    def setUp(self) -> None:
        self.informe = type(self).informe

    def test_report_file_matches_live_generation(self) -> None:
        self.assertTrue(REPORT.exists(), "Falta el informe generado")
        stored = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(stored, self.informe)

    def test_report_sections_present(self) -> None:
        self.assertEqual(
            set(self.informe),
            {"casos_busqueda", "casos_adversarial", "partidas"},
        )

    def test_search_rows_have_required_fields(self) -> None:
        bloques = self.informe["casos_busqueda"]
        self.assertEqual(len(bloques), 5)
        for bloque in bloques:
            for fila in bloque["filas"]:
                with self.subTest(caso=bloque["caso"], algoritmo=fila["algoritmo"]):
                    for field in (
                        "algoritmo",
                        "parametros",
                        "exito",
                        "costo",
                        "nodos_generados",
                        "camino",
                    ):
                        self.assertIn(field, fila)
                    self.assertNotIn("tiempo", fila)

    def test_case_1_bfs_and_dfs_present(self) -> None:
        filas = self.informe["casos_busqueda"][0]["filas"]
        algoritmos = [fila["algoritmo"] for fila in filas]
        self.assertEqual(algoritmos, ["BFS", "DFS"])
        self.assertTrue(all(fila["exito"] for fila in filas))

    def test_case_2_bfs_vs_ucs_cost(self) -> None:
        filas = self.informe["casos_busqueda"][1]["filas"]
        bfs_row = next(fila for fila in filas if fila["algoritmo"] == "BFS")
        ucs_row = next(fila for fila in filas if fila["algoritmo"] == "UCS")
        self.assertLessEqual(ucs_row["costo"], bfs_row["costo"])
        self.assertTrue(ucs_row["exito"] and bfs_row["exito"])

    def test_case_4_heuristics_are_labelled(self) -> None:
        filas = self.informe["casos_busqueda"][3]["filas"]
        parametros = {fila["parametros"] for fila in filas}
        self.assertEqual(parametros, {"h: MANHATTAN", "h: EUCLIDEA"})

    def test_case_5_beam_has_four_k_values(self) -> None:
        filas = self.informe["casos_busqueda"][4]["filas"]
        self.assertEqual(
            [fila["parametros"] for fila in filas],
            ["k: 1", "k: 2", "k: 4", "k: 8"],
        )

    def test_case_10_depths_two_three_five(self) -> None:
        bloques = [
            bloque
            for bloque in self.informe["casos_adversarial"]
            if bloque["caso"] == "Caso 10" and len(bloque["filas"]) == 3
        ]
        self.assertEqual(len(bloques), 1)
        profundidades = [fila["profundidad"] for fila in bloques[0]["filas"]]
        self.assertEqual(profundidades, [2, 3, 5])

    def test_partida_terminal_states_present(self) -> None:
        partidas = self.informe["partidas"]
        self.assertEqual(len(partidas), 3)
        nombres = {bloque["escenario"] for bloque in partidas}
        self.assertEqual(
            nombres,
            {
                "escenario_partida",
                "escenario_robo_bandera",
                "escenario_bandera_bloqueada",
            },
        )
        for bloque in partidas:
            fila = bloque["filas"][0]
            with self.subTest(escenario=bloque["escenario"]):
                self.assertIn(
                    fila["estado_final"],
                    {"en curso", "victoria_A", "victoria_B", "bloqueado", "empate"},
                )
                self.assertGreater(fila["turnos_ejecutados"], 0)

    def test_informe_es_reproducible(self) -> None:
        self.assertEqual(informe_busqueda(), informe_busqueda())


if __name__ == "__main__":
    unittest.main()
