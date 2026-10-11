import { useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { validateScenario } from './services/api'
import './App.css'

type Notice = { type: 'success' | 'error'; message: string } | null

const demoCells = [
  'base-a', 'path', 'path', 'forest', 'forest', 'path', 'path', 'base-b',
  'path', 'unit-a', 'path', 'wall', 'forest', 'path', 'unit-b', 'path',
  'path', 'path', 'resource', 'wall', 'path', 'path', 'forest', 'path',
  'path', 'wall', 'path', 'path', 'forest', 'path', 'path', 'path',
  'path', 'path', 'unit-a', 'path', 'forest', 'path', 'unit-b', 'path',
  'forest', 'path', 'path', 'path', 'path', 'wall', 'path', 'path',
  'path', 'path', 'path', 'forest', 'path', 'path', 'path', 'path',
  'path', 'path', 'wall', 'path', 'forest', 'path', 'path', 'base-b',
]

function App() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [notice, setNotice] = useState<Notice>(null)
  const [fileName, setFileName] = useState('Ningún escenario cargado')
  const [isValidating, setIsValidating] = useState(false)

  const handleFile = async (file?: File) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.json')) {
      setNotice({ type: 'error', message: 'Selecciona un archivo con extensión .json.' })
      return
    }

    setFileName(file.name)
    setIsValidating(true)
    setNotice(null)
    try {
      const result = await validateScenario(file)
      setNotice({ type: 'success', message: result.mensaje })
    } catch (error) {
      setNotice({
        type: 'error',
        message: error instanceof Error ? error.message : 'No se pudo validar el escenario.',
      })
    } finally {
      setIsValidating(false)
    }
  }

  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    void handleFile(event.target.files?.[0])
    event.target.value = ''
  }

  return (
    <main className="app-shell">
      {notice && (
        <div className={`toast toast-${notice.type}`} role="alert">
          <span className="toast-icon">{notice.type === 'success' ? 'OK' : '!'}</span>
          <span>{notice.message}</span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Cerrar alerta">
            x
          </button>
        </div>
      )}

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">TG</div>
          <div>
            <strong>TacticalGrid</strong>
            <span>AI experimentation lab</span>
          </div>
        </div>
        <div className="topbar-status"><span className="status-dot" /> Backend conectado</div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">SISTEMAS INTELIGENTES I / PROYECTO 01</p>
          <h1>Observa cómo <em>piensa</em> el tablero.</h1>
          <p className="hero-copy">
            Experimenta con búsqueda, costos y decisiones adversariales en un
            escenario 2D reproducible.
          </p>
        </div>
        <div className="hero-orbit"><span>AI</span><i /><i /><i /></div>
      </section>

      <section className="workspace">
        <aside className="sidebar">
          <div className="section-label">01 / ESCENARIO</div>
          <div className="upload-card">
            <div className="upload-icon">↑</div>
            <h2>Carga tu escenario</h2>
            <p>Valida la estructura JSON antes de iniciar una experimentación.</p>
            <button className="primary-button" type="button" onClick={() => inputRef.current?.click()}>
              {isValidating ? 'Validando...' : 'Seleccionar JSON'}
            </button>
            <input ref={inputRef} type="file" accept=".json,application/json" hidden onChange={onFileChange} />
            <span className="file-name">{fileName}</span>
          </div>

          <div className="section-label section-label-spaced">02 / ALGORITMO</div>
          <label className="field-label" htmlFor="algorithm">Método de búsqueda</label>
          <select id="algorithm" defaultValue="A*">
            <option>BFS — amplitud</option>
            <option>DFS — profundidad</option>
            <option>UCS — costo uniforme</option>
            <option>A* — heurística</option>
            <option>Beam Search</option>
            <option>Minimax</option>
            <option>Alfa-beta</option>
          </select>
          <button className="secondary-button" type="button">Ejecutar experimento <span>→</span></button>
        </aside>

        <div className="board-column">
          <div className="board-heading">
            <div><span className="live-pill">LIVE MAP</span><h2>Vista previa del escenario <small>demo 8 × 8</small></h2></div>
            <div className="turn-badge"><span>Turno actual</span><strong>A</strong></div>
          </div>
          <div className="board-card">
            <div className="grid-wrap">
              <div className="grid-coordinates top">{[1, 2, 3, 4, 5, 6, 7, 8].map((n) => <span key={n}>{String(n).padStart(2, '0')}</span>)}</div>
              <div className="grid-body">
                <div className="grid-coordinates side">{[1, 2, 3, 4, 5, 6, 7, 8].map((n) => <span key={n}>{String(n).padStart(2, '0')}</span>)}</div>
                <div className="map-grid">{demoCells.map((cell, index) => <div className={`cell ${cell}`} key={`${cell}-${index}`} aria-label={cell} />)}</div>
              </div>
            </div>
            <div className="legend">
              <span><i className="legend-swatch base-a" /> Base A</span>
              <span><i className="legend-swatch base-b" /> Base B</span>
              <span><i className="legend-swatch resource" /> Recurso</span>
              <span><i className="legend-swatch wall" /> Obstáculo</span>
              <span><i className="legend-swatch path" /> Camino</span>
            </div>
          </div>
          <div className="status-line"><span className="status-dot" /> Escenario de demostración · listo para ejecutar</div>
        </div>
      </section>

      <section className="metrics-section">
        <div className="section-label">03 / MÉTRICAS DE EXPERIMENTACIÓN</div>
        <div className="metrics-grid">
          <article><span>ESTADOS GENERADOS</span><strong>—</strong><small>Se mostrará al ejecutar</small></article>
          <article><span>COSTO TOTAL</span><strong>—</strong><small>Según terreno recorrido</small></article>
          <article><span>LONGITUD</span><strong>—</strong><small>Movimientos del camino</small></article>
          <article><span>TIEMPO</span><strong>—</strong><small>Rendimiento del algoritmo</small></article>
        </div>
      </section>
    </main>
  )
}

export default App
