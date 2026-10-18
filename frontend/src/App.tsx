import { useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { Grid } from './components/Grid'
import { ResultsDashboard } from './components/ResultsDashboard'
import { ScenarioSummary } from './components/ScenarioSummary'
import { runSearch, validateScenario } from './services/api'
import type {
  AlgoritmoBusquedaDisponible,
  Escenario,
  HeuristicaDisponible,
  ResultadoBusqueda,
} from './types/types'
import './App.css'

type Notice = { type: 'success' | 'error'; message: string } | null

const algorithmLabels: Record<AlgoritmoBusquedaDisponible, string> = {
  BFS: 'BFS - amplitud',
  DFS: 'DFS - profundidad',
  UCS: 'UCS - costo uniforme',
  A_ESTRELLA: 'A* - búsqueda informada',
  BEAM_SEARCH: 'Beam Search - memoria limitada',
}

function App() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [notice, setNotice] = useState<Notice>(null)
  const [fileName, setFileName] = useState('Ningún escenario cargado')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [scenario, setScenario] = useState<Escenario | null>(null)
  const [algorithm, setAlgorithm] = useState<AlgoritmoBusquedaDisponible>('BFS')
  const [heuristic, setHeuristic] = useState<HeuristicaDisponible>('MANHATTAN')
  const [beamWidth, setBeamWidth] = useState(1)
  const [searchResult, setSearchResult] = useState<ResultadoBusqueda | null>(null)
  const [resultHistory, setResultHistory] = useState<ResultadoBusqueda[]>([])
  const [isValidating, setIsValidating] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  const handleFile = async (file?: File) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.json')) {
      setNotice({ type: 'error', message: 'Selecciona un archivo con extensión .json.' })
      return
    }

    setIsValidating(true)
    setNotice(null)
    try {
      const raw = await file.text()
      const result = await validateScenario(file)
      setScenario(JSON.parse(raw) as Escenario)
      setSelectedFile(file)
      setSearchResult(null)
      setResultHistory([])
      setFileName(file.name)
      setNotice({ type: 'success', message: result.mensaje })
    } catch (error) {
      setScenario(null)
      setSelectedFile(null)
      setFileName('Ningún escenario cargado')
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

  const handleSearch = async () => {
    if (!selectedFile) {
      setNotice({ type: 'error', message: 'Carga un escenario válido antes de ejecutar.' })
      return
    }

    setIsRunning(true)
    setSearchResult(null)
    setNotice(null)
    try {
      const result = await runSearch(selectedFile, algorithm, heuristic, beamWidth)
      setSearchResult(result)
      setResultHistory((previous) => [
        result,
        ...previous.filter((entry) => entry.algoritmo !== result.algoritmo),
      ].slice(0, 8))
      setNotice({
        type: result.exito ? 'success' : 'error',
        message: result.exito
          ? `${algorithmLabels[algorithm]} encontró una ruta.`
          : 'No se encontró una ruta para la configuración seleccionada.',
      })
    } catch (error) {
      setNotice({
        type: 'error',
        message: error instanceof Error ? error.message : 'No se pudo ejecutar la búsqueda.',
      })
    } finally {
      setIsRunning(false)
    }
  }

  const rows = scenario?.mapa.filas ?? 8
  const columns = scenario?.mapa.columnas ?? 8

  return (
    <main className="app-shell">
      {notice && (
        <div className={`toast toast-${notice.type}`} role="alert">
          <span className="toast-icon">{notice.type === 'success' ? 'OK' : '!'}</span>
          <span>{notice.message}</span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Cerrar alerta">x</button>
        </div>
      )}

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">TG</div>
          <div><strong>TacticalGrid</strong><span>AI experimentation lab</span></div>
        </div>
        <div className="topbar-status"><span className="status-dot" /> Backend conectado</div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">SISTEMAS INTELIGENTES I / PROYECTO 01</p>
          <h1>Observa cómo <em>piensa</em> el tablero.</h1>
          <p className="hero-copy">Experimenta con búsqueda, costos y decisiones adversariales en un escenario 2D reproducible.</p>
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
          <select id="algorithm" value={algorithm} onChange={(event) => setAlgorithm(event.target.value as AlgoritmoBusquedaDisponible)}>
            <option value="BFS">{algorithmLabels.BFS}</option>
            <option value="DFS">{algorithmLabels.DFS}</option>
            <option value="UCS">{algorithmLabels.UCS}</option>
            <option value="A_ESTRELLA">{algorithmLabels.A_ESTRELLA}</option>
            <option value="BEAM_SEARCH">{algorithmLabels.BEAM_SEARCH}</option>
          </select>
          <label className="field-label" htmlFor="heuristic">Heurística</label>
          <select id="heuristic" value={heuristic} disabled={algorithm !== 'A_ESTRELLA'} onChange={(event) => setHeuristic(event.target.value as HeuristicaDisponible)}>
            <option value="MANHATTAN">Manhattan</option>
            <option value="EUCLIDEA">Heurística Propia</option>
          </select>
          {algorithm === 'BEAM_SEARCH' && (
            <>
              <label className="field-label" htmlFor="beam-width">Ancho de memoria (k)</label>
              <input
                id="beam-width"
                type="number"
                min="1"
                step="1"
                value={beamWidth}
                onChange={(event) => setBeamWidth(Math.max(1, Number(event.target.value) || 1))}
              />
              <small className="field-help">Valores recomendados: 1, 2, 4 y 8.</small>
            </>
          )}
          <button className="secondary-button" type="button" onClick={() => void handleSearch()} disabled={!selectedFile || isRunning || isValidating}>
            {isRunning ? 'Ejecutando...' : 'Ejecutar búsqueda'} <span>→</span>
          </button>
        </aside>

        <div className="board-column">
          <div className="board-heading">
            <div>
              <span className="live-pill">{scenario ? 'SCENARIO' : 'LIVE MAP'}</span>
              <h2>Vista previa del escenario <small>{rows} × {columns}</small></h2>
              {scenario?.prueba?.objetivo && (
                <p className="objective-label">
                  Objetivo de búsqueda: <strong>({scenario.prueba.objetivo.fila}, {scenario.prueba.objetivo.columna})</strong>
                  <span> coordenadas 0-based</span>
                </p>
              )}
            </div>
            <div className="turn-badge"><span>Turno actual</span><strong>{scenario?.turno ?? 'A'}</strong></div>
          </div>
          <div className="board-card">
            {scenario ? (
              <Grid
                escenario={scenario}
                camino={searchResult?.camino ?? []}
                objetivo={scenario.prueba?.objetivo}
              />
            ) : (
              <div className="empty-board">Carga un escenario válido para visualizar el mapa.</div>
            )}
            <div className="legend">
              <span><i className="legend-swatch base-a" /> Base A</span>
              <span><i className="legend-swatch base-b" /> Base B</span>
              <span><i className="legend-swatch resource" /> Recurso</span>
              <span><i className="legend-swatch wall" /> Obstáculo</span>
              <span><i className="legend-swatch route-cell" /> Camino encontrado</span>
              <span><i className="legend-swatch carrier" /> Portador</span>
            </div>
          </div>
          <div className="status-line">
            <span className="status-dot" />
            {isRunning ? 'Ejecutando búsqueda...' : searchResult?.exito ? 'Ruta encontrada y resaltada en el tablero.' : 'Carga un escenario para ejecutar una búsqueda.'}
          </div>
        </div>
      </section>

      {scenario && <ScenarioSummary escenario={scenario} />}

      <ResultsDashboard results={resultHistory} />
    </main>
  )
}

export default App
