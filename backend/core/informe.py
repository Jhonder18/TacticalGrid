"""Generación del informe consolidado de resultados (Casos 1 a 10).

Ejecuta los casos de búsqueda, adversariales y de partida del proyecto y
produce una estructura tabular reproducible para la sustentación. Los campos de
tiempo se omiten en el reporte persistido porque no son deterministas.
"""

from pathlib import Path

from backend.algorithms import a_star, beam_search, bfs, dfs, ucs
from backend.core.adversarial_comparison import comparar_adversarial
from backend.core.adversarial_report import registro_comparacion
from backend.core.game_simulation import simular_partida
from backend.models import Escenario, ResultadoBusqueda

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples" / "good"


def cargar_escenario(nombre: str) -> Escenario:
    """Carga un escenario válido desde ``examples/good``.

    Purpose:
        Reutilizar los casos del proyecto desde los generadores de informes.
    Preconditions:
        `nombre` debe ser el nombre de archivo sin la extensión.
    Postconditions:
        Devuelve un `Escenario` validado.
    Complexity:
        O(tamaño del JSON).
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se probará con los Casos 1 a 10.
    """

    import json

    data = json.loads((EXAMPLES_DIR / f"{nombre}.json").read_text(encoding="utf-8"))
    return Escenario.model_validate(data)


def _fila_busqueda(
    algoritmo: str,
    resultado: ResultadoBusqueda,
    parametros: str,
) -> dict:
    """Extrae los campos reproducibles de una búsqueda.

    Purpose:
        Aislar las métricas deterministas de una ejecución de búsqueda.
    Preconditions:
        `resultado` proviene de un algoritmo de búsqueda.
    Postconditions:
        Devuelve un diccionario con algoritmo, parámetros, éxito, costo, nodos
        y camino, sin tiempo.
    Complexity:
        O(longitud del camino).
    AI usage:
        No.
    AI intervention:
        Se omitió el tiempo para que el informe sea reproducible.
    Student validation:
        Se comparará con las capturas de la interfaz.
    """

    return {
        "algoritmo": algoritmo,
        "parametros": parametros,
        "exito": resultado.exito,
        "costo": resultado.costo,
        "longitud_camino": resultado.longitud_camino,
        "nodos_generados": resultado.estados_generados,
        "nodos_expandidos": resultado.estados_expandidos,
        "maximo_frontera": resultado.maximo_frontera,
        "camino": [[step.fila, step.columna] for step in resultado.camino],
    }


def _fila_partida(
    caso: str,
    algoritmo: str,
    heuristica: str,
    scenario: Escenario,
) -> dict:
    """Resume el resultado de una simulación de partida.

    Purpose:
        Registrar el estado terminal de una partida automática.
    Preconditions:
        `scenario` debe estar en modo partida y validado.
    Postconditions:
        Devuelve un diccionario con estado final, motivo y turnos ejecutados.
    Complexity:
        O(costo de la simulación completa).
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se probará con robo de bandera y bandera bloqueada.
    """

    simulacion = simular_partida(scenario, algoritmo, heuristica)
    return {
        "caso": caso,
        "algoritmo": algoritmo,
        "parametros": f"h: {heuristica}",
        "estado_final": simulacion.estado_final,
        "motivo_final": simulacion.motivo_final,
        "turnos_ejecutados": simulacion.turnos_ejecutados,
        "limite_turnos": simulacion.limite_turnos,
    }


def informe_busqueda() -> list[dict]:
    """Genera las secciones de búsqueda de los Casos 1 a 5.

    Purpose:
        Registrar las comparaciones de algoritmos de búsqueda por caso.
    Preconditions:
        Los escenarios `caso_1` a `caso_5` deben existir y ser válidos.
    Postconditions:
        Devuelve una lista de bloques, uno por caso, con sus filas.
    Complexity:
        O(suma de las búsquedas de los cinco casos).
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se probará contra la interfaz por botones rápidos.
    """

    bloques: list[dict] = []

    caso_1 = cargar_escenario("caso_1_bfs_dfs")
    bloques.append({
        "caso": "Caso 1",
        "descripcion": "BFS frente a DFS sobre el mismo escenario.",
        "escenario": "caso_1_bfs_dfs",
        "tipo": "busqueda",
        "filas": [
            _fila_busqueda("BFS", bfs(caso_1), "—"),
            _fila_busqueda("DFS", dfs(caso_1), "—"),
        ],
    })

    caso_2 = cargar_escenario("caso_2_bfs_ucs")
    bloques.append({
        "caso": "Caso 2",
        "descripcion": "BFS (camino más corto) frente a UCS (camino más económico).",
        "escenario": "caso_2_bfs_ucs",
        "tipo": "busqueda",
        "filas": [
            _fila_busqueda("BFS", bfs(caso_2), "—"),
            _fila_busqueda("UCS", ucs(caso_2), "—"),
        ],
    })

    caso_3 = cargar_escenario("caso_3_obstaculo_astar")
    bloques.append({
        "caso": "Caso 3",
        "descripcion": "A* con Manhattan desviándose por los obstáculos.",
        "escenario": "caso_3_obstaculo_astar",
        "tipo": "busqueda",
        "filas": [
            _fila_busqueda("A_ESTRELLA", a_star(caso_3, "MANHATTAN"), "h: MANHATTAN"),
        ],
    })

    caso_4 = cargar_escenario("caso_4_heuristicas")
    bloques.append({
        "caso": "Caso 4",
        "descripcion": "A* con Manhattan frente a A* con Euclídea (propia).",
        "escenario": "caso_4_heuristicas",
        "tipo": "busqueda",
        "filas": [
            _fila_busqueda("A_ESTRELLA", a_star(caso_4, "MANHATTAN"), "h: MANHATTAN"),
            _fila_busqueda("A_ESTRELLA", a_star(caso_4, "EUCLIDEA"), "h: EUCLIDEA"),
        ],
    })

    caso_5 = cargar_escenario("caso_5_beam")
    bloques.append({
        "caso": "Caso 5",
        "descripcion": "Beam Search con k = 1, 2, 4 y 8.",
        "escenario": "caso_5_beam",
        "tipo": "busqueda",
        "filas": [
            _fila_busqueda("BEAM_SEARCH", beam_search(caso_5, k), f"k: {k}")
            for k in (1, 2, 4, 8)
        ],
    })

    return bloques


def informe_adversarial() -> list[dict]:
    """Genera las secciones adversariales de los Casos 6 a 10.

    Purpose:
        Reutilizar el reporte de comparación Minimax vs Alfa-Beta.
    Preconditions:
        Los escenarios `caso_6` a `caso_10` deben existir y ser válidos.
    Postconditions:
        Devuelve una lista de bloques, uno por caso, con sus filas.
    Complexity:
        O(suma de las búsquedas adversariales).
    AI usage:
        No.
    AI intervention:
        Se reutiliza `registro_comparacion` para no duplicar lógica.
    Student validation:
        Se probará contra el árbol adversarial de la interfaz.
    """

    casos = [
        ("Caso 6", "caso_6_portador_a", "Diferencia de portador: A1 lleva el recurso."),
        ("Caso 6", "caso_6_portador_b", "Diferencia de portador: B1 lleva el recurso."),
        ("Caso 7", "caso_7_intercepcion", "Intercepción del portador rival."),
        ("Caso 8", "caso_8_poda", "Minimax frente a Alfa-Beta (poda)."),
        ("Caso 9", "caso_9_orden_poda", "Efecto del orden de sucesores en la poda."),
        ("Caso 10", "caso_10_profundidades", "Carga de profundidad 5 (base)."),
    ]

    bloques: list[dict] = []
    for caso, escenario, descripcion in casos:
        scenario = cargar_escenario(escenario)
        registro = registro_comparacion(escenario, comparar_adversarial(scenario))
        bloques.append({
            "caso": caso,
            "descripcion": descripcion,
            "escenario": escenario,
            "tipo": "adversarial",
            "filas": [registro],
        })

    profundidades = cargar_escenario("caso_10_profundidades")
    filas = []
    for profundidad in (2, 3, 5):
        scenario = profundidades.model_copy(
            deep=True,
            update={
                "juego": profundidades.juego.model_copy(
                    update={"profundidad_maxima_minimax": profundidad}
                )
            },
        )
        filas.append(
            registro_comparacion(
                f"caso_10_p{profundidad}",
                comparar_adversarial(scenario),
            )
        )
    bloques.append({
        "caso": "Caso 10",
        "descripcion": "Carga de profundidades 2, 3 y 5.",
        "escenario": "caso_10_profundidades",
        "tipo": "adversarial",
        "filas": filas,
    })

    return bloques


def informe_partidas() -> list[dict]:
    """Genera la sección de simulaciones de partida.

    Purpose:
        Registrar los estados terminales de partidas automáticas.
    Preconditions:
        Los escenarios de partida deben existir y ser válidos.
    Postconditions:
        Devuelve una lista de bloques con el resultado de cada partida.
    Complexity:
        O(costo de cada simulación completa).
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se probará con robo de bandera y bandera bloqueada.
    """

    escenarios = [
        ("Partida", "escenario_partida", "Partida estándar entre ambos bandos."),
        ("Robo de bandera", "escenario_robo_bandera", "El bando B ya carga el recurso."),
        ("Bandera bloqueada", "escenario_bandera_bloqueada", "Ruta al objetivo bloqueada."),
    ]

    bloques: list[dict] = []
    for caso, escenario, descripcion in escenarios:
        scenario = cargar_escenario(escenario)
        bloques.append({
            "caso": caso,
            "descripcion": descripcion,
            "escenario": escenario,
            "tipo": "partida",
            "filas": [_fila_partida(caso, "BFS", "MANHATTAN", scenario)],
        })

    return bloques


def generar_informe() -> dict:
    """Genera el informe consolidado de los Casos 1 a 10.

    Purpose:
        Producir la estructura completa para el informe de sustentación.
    Preconditions:
        Todos los escenarios del proyecto deben existir y ser válidos.
    Postconditions:
        Devuelve un diccionario con las secciones de búsqueda, adversarial y
        partida, reproducible para el mismo código.
    Complexity:
        O(suma de todos los casos).
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se probará regenerándolo y comparándolo con el test.
    """

    return {
        "casos_busqueda": informe_busqueda(),
        "casos_adversarial": informe_adversarial(),
        "partidas": informe_partidas(),
    }
