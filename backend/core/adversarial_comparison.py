"""Comparación reproducible entre Minimax y Alfa-Beta.

Ejecuta ambos algoritmos sobre el mismo escenario y con la misma profundidad
para comprobar que toman la misma decisión y cuantificar el ahorro de nodos
que aporta la poda Alfa-Beta.
"""

from backend.algorithms.adversarial import alpha_beta, minimax
from backend.models import (
    Escenario,
    ResultadoAdversarial,
    ResultadoComparacionAdversarial,
)


def _reduccion_nodos(minimax_result: ResultadoAdversarial, alpha_beta_result: ResultadoAdversarial) -> float:
    """Calcula el porcentaje de nodos evitados por Alfa-Beta.

    Purpose:
        Cuantificar el ahorro de la poda frente a Minimax.
    Preconditions:
        `minimax_result.nodos_generados` debe ser mayor que cero.
    Postconditions:
        Devuelve un porcentaje entre 0 y 100, o 0 si Minimax no generó nodos.
    Complexity:
        O(1).
    AI usage:
        No.
    AI intervention:
        Se propuso comparar nodos generados porque es la métrica de poda.
    Student validation:
        Se probará con el Caso 8, donde Alfa-Beta debe reducir nodos.
    """

    total = minimax_result.nodos_generados
    if total <= 0:
        return 0.0
    return (total - alpha_beta_result.nodos_generados) / total * 100.0


def comparar_adversarial(scenario: Escenario) -> ResultadoComparacionAdversarial:
    """Ejecuta Minimax y Alfa-Beta y resume sus diferencias.

    Purpose:
        Producir una comparación directa para el informe y la interfaz.
    Preconditions:
        `scenario` debe estar validado y en modo adversarial con profundidad
        dentro del límite del proyecto.
    Postconditions:
        Devuelve ambos resultados con la misma profundidad, si comparten
        acción y valor, y el porcentaje de reducción de nodos de Alfa-Beta.
    Complexity:
        O(T_minimax + T_alpha_beta), dominado por las dos búsquedas.
    AI usage:
        No.
    AI intervention:
        Se propuso reutilizar `minimax` y `alpha_beta` sin duplicar lógica.
    Student validation:
        Se probará sobre los Casos 6 a 10 del proyecto.
    """

    minimax_result = minimax(scenario)
    alpha_beta_result = alpha_beta(scenario)

    return ResultadoComparacionAdversarial(
        profundidad=scenario.juego.profundidad_maxima_minimax,
        minimax=minimax_result,
        alpha_beta=alpha_beta_result,
        misma_accion=(
            alpha_beta_result.accion_seleccionada
            == minimax_result.accion_seleccionada
        ),
        mismo_valor=abs(
            alpha_beta_result.valor_obtenido - minimax_result.valor_obtenido
        )
        < 1e-9,
        reduccion_nodos_porcentaje=_reduccion_nodos(
            minimax_result, alpha_beta_result
        ),
    )
