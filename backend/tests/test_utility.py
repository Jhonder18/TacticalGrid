import unittest

from backend.core.utility import (
    TERMINAL_WIN_UTILITY,
    evaluate_utility,
)
from backend.models import Escenario, GameState, UnidadEstado


def build_scenario() -> Escenario:
    return Escenario.model_validate(
        {
            "version": "1.0",
            "mapa": {"filas": 3, "columnas": 4},
            "tipos_terreno": {
                "camino": {"costo": 1, "transitable": True},
            },
            "terreno": [["camino"] * 4 for _ in range(3)],
            "bases": {
                "A": {"fila": 0, "columna": 0},
                "B": {"fila": 2, "columna": 3},
            },
            "recurso": {"fila": 1, "columna": 2},
            "unidades": [
                {
                    "id": "A1",
                    "bando": "A",
                    "tipo": "explorador",
                    "fila": 1,
                    "columna": 1,
                },
                {
                    "id": "B1",
                    "bando": "B",
                    "tipo": "defensor",
                    "fila": 2,
                    "columna": 3,
                },
            ],
            "turno": "A",
            "juego": {
                "portador_recurso": None,
                "profundidad_maxima_minimax": 2,
            },
            "prueba": {"modo": "adversarial"},
        }
    )


class UtilityTests(unittest.TestCase):
    def test_nearer_player_to_resource_has_positive_advantage(self) -> None:
        scenario = build_scenario()
        state = GameState.from_scenario(scenario)

        self.assertGreater(evaluate_utility(state, "A", scenario), 0)
        self.assertLess(evaluate_utility(state, "B", scenario), 0)

    def test_carrier_progress_favors_the_bando_closer_to_its_base(self) -> None:
        scenario = build_scenario()
        initial_state = GameState.from_scenario(scenario)
        state = GameState(
            unidades=(
                UnidadEstado("A1", "A", (0, 2)),
                initial_state.unidades[1],
            ),
            portador_recurso="A1",
            posicion_recurso=None,
            turno="A",
        )

        self.assertGreater(evaluate_utility(state, "A", scenario), 0)

    def test_terminal_utility_is_symmetric_and_dominant(self) -> None:
        scenario = build_scenario()
        initial_state = GameState.from_scenario(scenario)
        state = GameState(
            unidades=(
                UnidadEstado("A1", "A", (0, 0)),
                initial_state.unidades[1],
            ),
            portador_recurso="A1",
            posicion_recurso=None,
            turno="A",
        )

        self.assertEqual(evaluate_utility(state, "A", scenario), TERMINAL_WIN_UTILITY)
        self.assertEqual(evaluate_utility(state, "B", scenario), -TERMINAL_WIN_UTILITY)


if __name__ == "__main__":
    unittest.main()
