import type { Escenario } from '../types/types'

interface ScenarioSummaryProps {
  escenario: Escenario
}

export function ScenarioSummary({ escenario }: ScenarioSummaryProps) {
  return (
    <section className="scenario-summary">
      <div className="summary-heading">
        <div>
          <span className="section-label">04 / RESUMEN DEL ESCENARIO</span>
          <h2>Estado cargado</h2>
        </div>
        <span className="summary-version">v{escenario.version}</span>
      </div>

      <div className="summary-cards">
        <div><span>MAPA</span><strong>{escenario.mapa.filas} × {escenario.mapa.columnas}</strong></div>
        <div><span>TURNO</span><strong className={`team-${escenario.turno.toLowerCase()}`}>{escenario.turno}</strong></div>
        <div><span>MODO</span><strong>{escenario.prueba?.modo ?? '—'}</strong></div>
        <div><span>PROFUNDIDAD</span><strong>{escenario.juego.profundidad_maxima_minimax}</strong></div>
      </div>

      <div className="summary-details">
        <div className="summary-panel">
          <h3>Elementos del mapa</h3>
          <dl>
            <div><dt>Base A</dt><dd>({escenario.bases.A.fila}, {escenario.bases.A.columna})</dd></div>
            <div><dt>Base B</dt><dd>({escenario.bases.B.fila}, {escenario.bases.B.columna})</dd></div>
            <div>
              <dt>Recurso</dt>
              <dd>
                {escenario.juego.portador_recurso
                  ? `Transportado por ${escenario.juego.portador_recurso}`
                  : `(${escenario.recurso.fila}, ${escenario.recurso.columna})`}
              </dd>
            </div>
            <div><dt>Portador</dt><dd>{escenario.juego.portador_recurso ?? 'Sin portador'}</dd></div>
          </dl>
        </div>
        <div className="summary-panel">
          <h3>Tipos de terreno</h3>
          <div className="terrain-summary-list">
            {Object.entries(escenario.tipos_terreno).map(([name, terrain]) => (
              <span key={name}>
                <b>{name}</b>
                {terrain.transitable ? `costo ${terrain.costo}` : 'bloqueado'}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="units-panel">
        <h3>Unidades por bando</h3>
        <div className="units-table-wrap">
          <table>
            <thead>
              <tr><th>ID</th><th>Bando</th><th>Tipo</th><th>Posición</th><th>Estado</th></tr>
            </thead>
            <tbody>
              {escenario.unidades.map((unidad) => {
                const isCarrier = unidad.id === escenario.juego.portador_recurso
                return (
                  <tr key={unidad.id}>
                    <td><strong>{unidad.id}</strong></td>
                    <td><span className={`team-badge team-${unidad.bando.toLowerCase()}`}>{unidad.bando}</span></td>
                    <td>{unidad.tipo}</td>
                    <td>({unidad.fila}, {unidad.columna})</td>
                    <td>{isCarrier ? <span className="carrier-label">◆ Portador</span> : 'Disponible'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
