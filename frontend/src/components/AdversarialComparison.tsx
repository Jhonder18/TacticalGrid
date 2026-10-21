import type {
  Accion,
  MetricasAdversariales,
  ResultadoComparacionAdversarial,
} from '../types/types'

interface AdversarialComparisonProps {
  comparacion: ResultadoComparacionAdversarial
}

function formatAccion(accion: Accion | null): string {
  if (!accion) {
    return 'Sin acción legal'
  }
  return `${accion.unidad_id}: (${accion.origen?.fila}, ${accion.origen?.columna}) → (${accion.destino?.fila}, ${accion.destino?.columna})`
}

function AlgorithmRow({
  etiqueta,
  metricas,
}: {
  etiqueta: string
  metricas: MetricasAdversariales
}) {
  return (
    <tr>
      <th scope="row">{etiqueta}</th>
      <td className="comparison-action">{formatAccion(metricas.accion_seleccionada)}</td>
      <td>{metricas.valor_obtenido.toFixed(4)}</td>
      <td>{metricas.nodos_generados}</td>
      <td>{metricas.nodos_evaluados}</td>
      <td>{metricas.nodos_podados}</td>
      <td>{metricas.profundidad_alcanzada}</td>
      <td>{(metricas.tiempo * 1000).toFixed(2)} ms</td>
    </tr>
  )
}

export function AdversarialComparison({ comparacion }: AdversarialComparisonProps) {
  const coincides = comparacion.misma_accion && comparacion.mismo_valor
  return (
    <section className="comparison-panel">
      <div className="tree-heading">
        <div>
          <div className="section-label">04 / COMPARACIÓN ADVERSARIAL</div>
          <h2>Minimax vs Alfa-Beta</h2>
        </div>
        <span className="tree-caption">Profundidad {comparacion.profundidad}</span>
      </div>
      <div className="comparison-scroll">
        <table className="comparison-table">
          <thead>
            <tr>
              <th scope="col">Algoritmo</th>
              <th scope="col">Acción seleccionada</th>
              <th scope="col">Valor</th>
              <th scope="col">Nodos</th>
              <th scope="col">Evaluados</th>
              <th scope="col">Podados</th>
              <th scope="col">Profundidad</th>
              <th scope="col">Tiempo</th>
            </tr>
          </thead>
          <tbody>
            <AlgorithmRow etiqueta="Minimax" metricas={comparacion.minimax} />
            <AlgorithmRow etiqueta="Alfa-Beta" metricas={comparacion.alpha_beta} />
          </tbody>
        </table>
      </div>
      <div className={`comparison-summary ${coincides ? 'comparison-match' : 'comparison-diff'}`}>
        <span>
          {coincides
            ? 'Ambos algoritmos coinciden en acción y valor.'
            : 'Los algoritmos difieren en acción o valor.'}
        </span>
        <span>
          Reducción de nodos con Alfa-Beta:{' '}
          <strong>{comparacion.reduccion_nodos_porcentaje.toFixed(2)}%</strong>
        </span>
        <small>
          Fórmula: ((nodos generados por Minimax - nodos generados por Alfa-Beta)
          {' / '}nodos generados por Minimax) × 100.
        </small>
      </div>
    </section>
  )
}
