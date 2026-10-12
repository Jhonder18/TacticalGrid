import unittest

from backend.core.successors import get_successors
from backend.models import Escenario, GameState, UnidadEstado


def build_scenario() -> Escenario:
    return Escenario.model_validate(
        {
            "version": "1.0",
            "mapa": {"filas": 3, "columnas": 4},
            "tipos_terreno": {
                "camino": {"costo": 1, "transitable": True},
                "pasto": {"costo": 3, "transitable": True},
                "muro": {"transitable": False},
            },
            "terreno": [
                ["camino", "camino", "muro", "camino"],
                ["camino", "pasto", "camino", "camino"],
                ["camino", "camino", "camino", "camino"],
            ],
            "bases": {
                "A": {"fila": 0, "columna": 0},
                "B": {"fila": 2, "columna": 3},
            },
            "recurso": {"fila": 0, "columna": 1},
            "unidades": [
                {"id": "A1", "bando": "A", "tipo": "explorador", "fila": 0, "columna": 0},
                {"id": "B1", "bando": "B", "tipo": "defensor", "fila": 2, "columna": 2},
            ],
            "turno": "A",
            "juego": {
                "portador_recurso": None,
                "profundidad_maxima_minimax": 2,
            },
            "prueba": {
                "modo": "busqueda",
                "unidad_inicio": "A1",
                "objetivo": {"fila": 2, "columna": 3},
            },
        }
    )


class GameStateTests(unittest.TestCase):
    def test_same_state_has_same_key_hash_and_serialization(self) -> None:
        scenario = build_scenario()
        first = GameState.from_scenario(scenario)
        second = GameState(
            unidades=tuple(reversed(first.unidades)),
            portador_recurso=None,
            posicion_recurso=(0, 1),
            turno="A",
        )

        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertEqual(first.state_key(), second.state_key())
        self.assertEqual(first.serialize(), second.serialize())

    def test_turn_and_resource_are_part_of_state_identity(self) -> None:
        scenario = build_scenario()
        state = GameState.from_scenario(scenario)

        different_turn = GameState(
            unidades=state.unidades,
            portador_recurso=state.portador_recurso,
            posicion_recurso=state.posicion_recurso,
            turno="B",
        )
        carrying_resource = GameState(
            unidades=state.unidades,
            portador_recurso="A1",
            posicion_recurso=None,
            turno="A",
        )

        self.assertNotEqual(state, different_turn)
        self.assertNotEqual(state, carrying_resource)

    def test_successors_respect_obstacles_occupancy_and_dynamic_cost(self) -> None:
        scenario = build_scenario()
        state = GameState(
            unidades=(
                UnidadEstado("A1", "A", (0, 1)),
                UnidadEstado("B1", "B", (0, 0)),
            ),
            portador_recurso=None,
            posicion_recurso=(0, 1),
            turno="A",
        )

        successors = get_successors(state, scenario)
        destinations = {
            (transition.action.destino.fila, transition.action.destino.columna): transition
            for transition in successors
        }

        self.assertNotIn((0, 2), destinations)
        self.assertNotIn((0, 0), destinations)
        self.assertIn((1, 1), destinations)
        self.assertEqual(destinations[(1, 1)].cost, 3)
        self.assertEqual(destinations[(1, 1)].state.turno, "B")

    def test_entering_resource_cell_assigns_carrier(self) -> None:
        scenario = build_scenario()
        state = GameState.from_scenario(scenario)

        successors = get_successors(state, scenario)
        pickup = next(
            transition
            for transition in successors
            if transition.action.destino.fila == 0
            and transition.action.destino.columna == 1
        )

        self.assertEqual(pickup.state.portador_recurso, "A1")
        self.assertIsNone(pickup.state.posicion_recurso)


if __name__ == "__main__":
    unittest.main()