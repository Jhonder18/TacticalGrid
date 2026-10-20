"""Registro reproducible de comparaciones adversariales.

Convierte los resultados de `comparar_adversarial` en filas tabulares estables
(sin tiempos de ejecución) para el informe final del proyecto.
"""

from pathlib import Path

from backend.core.adversarial_comparison import comparar_adversarial
from backend.models import Escenario, ResultadoComparacionAdversarial


def _accion_a_texto(resultado) -> str | None:
    """Serializa la acción seleccionada a una cadena estable.

    Purpose:
        Representar la acción de forma legible y comparable en el reporte.
    Preconditions:
        `resultado` es un `ResultadoAdversarial`.
    Postconditions:
        Devuelve ``unidad_id: (origen) -> (destino)`` o ``None``.
    Complexity:
        O(1).
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se probará con los Casos 6 a 10.
    """

    accion = resultado.accion_seleccionada
    if accion is None:
        return None
    origen = accion.origen
    destino = accion.destino
    return (
        f"{accion.unidad_id}: "
        f"({origen.fila}, {origen.columna}) -> ({destino.fila}, {destino.columna})"
    )


def _fila_algoritmo(nombre: str, resultado) -> dict:
    """Extrae los campos reproducibles de un resultado adversarial.

    Purpose:
        Aislar las métricas deterministas de una ejecución adversarial.
    Preconditions:
        `resultado` es un `ResultadoAdversarial`.
    Postconditions:
        Devuelve un diccionario sin campos de tiempo, apto para comparar.
    Complexity:
        O(1).
    AI usage:
        No.
    AI intervention:
        Se decidió omitir el tiempo para que el reporte sea reproducible.
    Student validation:
        Se probará comparando el JSON con una ejecución en vivo.
    """

    return {
        "algoritmo": nombre,
        "profundidad": resultado.profundidad_alcanzada,
        "nodos_generados": resultado.nodos_generados,
        "nodos_evaluados": resultado.nodos_evaluados,
        "nodos_podados": resultado.nodos_podados,
        "accion_seleccionada": _accion_a_texto(resultado),
        "valor_obtenido": resultado.valor_obtenido,
    }


def registro_comparacion(
    escenario: str,
    resultado: ResultadoComparacionAdversarial,
) -> dict:
    """Construye una entrada de reporte para una comparación adversarial.

    Purpose:
        Registrar de forma reproducible una comparación Minimax vs Alfa-Beta.
    Preconditions:
        `resultado` proviene de `comparar_adversarial`.
    Postconditions:
        Devuelve un diccionario con ambos algoritmos, coincidencias y la
        reducción porcentual de nodos.
    Complexity:
        O(1).
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se probará con los Casos 6 a 10.
    """

    return {
        "escenario": escenario,
        "profundidad": resultado.profundidad,
        "misma_accion": resultado.misma_accion,
        "mismo_valor": resultado.mismo_valor,
        "reduccion_nodos_porcentaje": round(
            resultado.reduccion_nodos_porcentaje, 4
        ),
        "minimax": _fila_algoritmo("MINIMAX", resultado.minimax),
        "alpha_beta": _fila_algoritmo("ALFA_BETA", resultado.alpha_beta),
    }


def generar_reporte(casos: list[tuple[str, Escenario]]) -> list[dict]:
    """Genera el reporte completo de una lista de escenarios.

    Purpose:
        Comparar Minimax y Alfa-Beta sobre varios casos en una sola estructura.
    Preconditions:
        Cada entrada contiene un nombre y un escenario adversarial validado.
    Postconditions:
        Devuelve una lista de entradas del reporte, una por caso.
    Complexity:
        O(suma de los tiempos de búsqueda de cada caso).
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        Se probará sobre los Casos 6 a 10.
    """

    return [
        registro_comparacion(nombre, comparar_adversarial(escenario))
        for nombre, escenario in casos
    ]


def escribir_reporte(ruta: Path, entradas: list[dict]) -> None:
    """Escribe el reporte en disco como JSON legible.

    Purpose:
        Persistir los resultados para el informe final.
    Preconditions:
        La carpeta destino debe existir.
    Postconditions:
        El archivo JSON queda escrito con codificación UTF-8.
    Complexity:
        O(n) sobre el número de entradas.
    AI usage:
        No.
    AI intervention:
        No.
    Student validation:
        No.
    """

    import json

    ruta.write_text(
        json.dumps(entradas, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
