"""Genera el informe consolidado de resultados de los Casos 1 a 10.

Escribe ``examples/reportes/informe_casos_1_10.json`` con las tablas de
búsqueda, adversariales y de partida, listas para la sustentación.

Uso:
    python -m backend.scripts.generar_informe_casos
"""

import json
from pathlib import Path

from backend.core.informe import generar_informe

REPORT_PATH = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "reportes"
    / "informe_casos_1_10.json"
)


def main() -> None:
    informe = generar_informe()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(informe, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    total = sum(
        len(informe[seccion])
        for seccion in ("casos_busqueda", "casos_adversarial", "partidas")
    )
    print(f"Informe escrito en {REPORT_PATH} ({total} bloques)")


if __name__ == "__main__":
    main()
