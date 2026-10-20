import type { ResultadoBusqueda } from '../types/types'

interface ResultsDashboardProps {
  results: ResultadoBusqueda[]
}

const algorithmLabels: Record<ResultadoBusqueda['algoritmo'], string> = {
  BFS: 'BFS',
  DFS: 'DFS',
  UCS: 'UCS',
  A_ESTRELLA: 'A*',
  BEAM_SEARCH: 'Beam Search',
}

function formatCost(cost: number): string {
  return Number.isInteger(cost) ? String(cost) : cost.toFixed(2)
}

export function ResultsDashboard({ results }: ResultsDashboardProps) {
  return (
    <section className="metrics-section">
      <div className="dashboard-heading">
        <div>
          <div className="section-label">03 / DASHBOARD DE RESULTADOS</div>
          <h2>Comparativa de ejecuciones</h2>
        </div>
        <span className="dashboard-caption">
          {results.length ? 'Última ejecución por método' : 'Ejecuta una búsqueda para comenzar'}
        </span>
      </div>
      <div className="results-table-wrap">
        <table className="results-table">
          <thead>
            <tr>
              <th>Método</th>
              <th>Éxito</th>
              <th>Camino</th>
              <th>Longitud</th>
              <th>Costo</th>
              <th>Nodos</th>
              <th>Expansiones</th>
              <th>Frontera</th>
              <th>Tiempo</th>
            </tr>
          </thead>
          <tbody>
            {results.length ? results.map((result) => {
              const beamFailed = result.algoritmo === 'BEAM_SEARCH' && !result.exito
              return (
              <tr
                key={result.algoritmo}
                className={beamFailed ? 'beam-failed-row' : undefined}
              >
                <td><strong>{algorithmLabels[result.algoritmo]}</strong></td>
                <td><span className={`result-status ${result.exito ? 'success' : 'failure'}`}>
                  {result.exito ? 'Sí' : 'No'}
                </span></td>
                <td className="result-path">
                  {beamFailed
                    ? `Sin solución con k=${result.k ?? 1}`
                    : result.camino.length
                      ? result.camino.map((step) => `(${step.fila},${step.columna})`).join(' → ')
                      : 'Sin camino'}
                </td>
                <td>{result.longitud_camino}</td>
                <td>{formatCost(result.costo)}</td>
                <td>{result.estados_generados}</td>
                <td>{result.estados_expandidos}</td>
                <td>{result.maximo_frontera}</td>
                <td>{(result.tiempo * 1000).toFixed(2)} ms</td>
              </tr>
              )
            }) : (
              <tr>
                <td className="results-empty" colSpan={9}>
                  Todavía no hay ejecuciones almacenadas en esta sesión.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
