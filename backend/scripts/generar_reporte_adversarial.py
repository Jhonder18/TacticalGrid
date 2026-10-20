"""Genera el reporte reproducible de comparaciones adversariales.

Ejecuta Minimax y Alfa-Beta sobre los Casos 6 a 10 y sobre el Caso 10 con
varias profundidades, escribiendo el resultado en
``examples/reportes/adversarial_casos_6_10.json``.

Uso:
    python -m backend.scripts.generar_reporte_adversarial
"""

import json
from pathlib import Path

from backend.core.adversarial_report import (
    escribir_reporte,
    registro_comparacion,
)
from backend.core.adversarial_comparison import comparar_adversarial
from backend.models import Escenario

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples" / "good"
REPORT_PATH = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "reportes"
    / "adversarial_casos_6_10.json"
)

CASOS = [
    "caso_6_portador_a",
    "caso_6_portador_b",
    "caso_7_intercepcion",
    "caso_8_poda",
    "caso_9_orden_poda",
    "caso_10_profundidades",
]

PROFUNDIDADES_CASO_10 = [2, 3, 5]


def _cargar(nombre: str) -> Escenario:
    data = json.loads((EXAMPLES_DIR / f"{nombre}.json").read_text(encoding="utf-8"))
    return Escenario.model_validate(data)


def main() -> None:
    entradas = []
    for nombre in CASOS:
        scenario = _cargar(nombre)
        entradas.append(registro_comparacion(nombre, comparar_adversarial(scenario)))

    for profundidad in PROFUNDIDADES_CASO_10:
        scenario = _cargar("caso_10_profundidades")
        scenario = scenario.model_copy(
            deep=True,
            update={
                "juego": scenario.juego.model_copy(
                    update={"profundidad_maxima_minimax": profundidad}
                )
            },
        )
        entradas.append(
            registro_comparacion(
                f"caso_10_profundidades_p{profundidad}",
                comparar_adversarial(scenario),
            )
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    escribir_reporte(REPORT_PATH, entradas)
    print(f"Reporte escrito en {REPORT_PATH} ({len(entradas)} entradas)")


if __name__ == "__main__":
    main()
