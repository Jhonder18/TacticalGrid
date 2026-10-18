import { useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { Grid } from './components/Grid'
import { AdversarialTree } from './components/AdversarialTree'
import { ResultsDashboard } from './components/ResultsDashboard'
import { ScenarioSummary } from './components/ScenarioSummary'
import { runAdversarial, runSearch, validateScenario } from './services/api'
import type {
  AlgoritmoBusquedaDisponible,
  Escenario,
  HeuristicaDisponible,
  ResultadoBusqueda,
  ResultadoAdversarial,
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

const quickCases = [
  { id: 1, label: 'Caso 1 · BFS vs DFS', file: 'caso_1_bfs_dfs.json' },
  { id: 2, label: 'Caso 2 · BFS vs UCS', file: 'caso_2_bfs_ucs.json' },
  { id: 3, label: 'Caso 3 · Obstáculo A*', file: 'caso_3_obstaculo_astar.json' },
  { id: 4, label: 'Caso 4 · Heurísticas', file: 'caso_4_heuristicas.json' },
  { id: 5, label: 'Caso 5 · Beam Search', file: 'caso_5_beam.json' },
  { id: 6, label: 'Caso 6 · Portador A', file: 'caso_6_portador_a.json' },
  { id: 7, label: 'Caso 7 · Interceptar', file: 'caso_7_intercepcion.json' },
  { id: 8, label: 'Caso 8 · Minimax vs Alfa-Beta', file: 'caso_8_poda.json' },
  { id: 9, label: 'Caso 9 · Orden de sucesores', file: 'caso_9_orden_poda.json' },
  { id: 10, label: 'Caso 10 · Profundidades 2/3/5', file: 'caso_10_profundidades.json' },
] as const

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
  const [adversarialResult, setAdversarialResult] = useState<ResultadoAdversarial | null>(null)
  const [adversarialAlgorithm, setAdversarialAlgorithm] = useState<'MINIMAX' | 'ALFA_BETA'>('ALFA_BETA')
  const [depth, setDepth] = useState(2)
  const [resultHistory, setResultHistory] = useState<ResultadoBusqueda[]>([])
  const [isValidating, setIsValidating] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const scenarioMode = scenario?.prueba?.modo ?? 'busqueda'
  const isAdversarialMode = scenarioMode !== 'busqueda'

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
      setAdversarialResult(null)
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

  const handleQuickCase = async (fileName: string) => {
    try {
      const response = await fetch(`/casos/${fileName}`)
      if (!response.ok) {
        throw new Error(`No se pudo cargar el caso (${response.status}).`)
      }
      const blob = await response.blob()
      await handleFile(new File([blob], fileName, { type: 'application/json' }))
    } catch (error) {
      setNotice({
        type: 'error',
        message: error instanceof Error ? error.message : 'No se pudo cargar el caso.',
      })
    }
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

  const handleAdversarial = async () => {
    if (!selectedFile) {
      setNotice({ type: 'error', message: 'Carga un escenario válido antes de evaluar.' })
      return
    }

    setIsRunning(true)
    setNotice(null)
    try {
      const result = await runAdversarial(selectedFile, adversarialAlgorithm, depth)
      setAdversarialResult(result)
      setNotice({ type: 'success', message: `${adversarialAlgorithm} recomendó una acción para el turno ${scenario?.turno ?? ''}.` })
    } catch (error) {
      setNotice({
        type: 'error',
        message: error instanceof Error ? error.message : 'No se pudo evaluar el turno.',
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
            <div className="quick-cases">
              <span className="field-label">Casos demostrativos</span>
              {quickCases.map((quickCase) => (
                <button
                  className="quick-case-button"
                  key={quickCase.id}
                  type="button"
                  onClick={() => void handleQuickCase(quickCase.file)}
                  disabled={isValidating || isRunning}
                >
                  {quickCase.label}
                </button>
              ))}
            </div>
          </div>

          <div className="section-label section-label-spaced">02 / ALGORITMO</div>
          <div className="loaded-mode">
            MODO CARGADO: <strong>{scenarioMode.toUpperCase()}</strong>
          </div>
          {!isAdversarialMode ? (
            <>
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
              <select
                id="beam-width"
                value={beamWidth}
                onChange={(event) => setBeamWidth(Number(event.target.value))}
              >
                {[1, 2, 4, 8].map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
              <small className="field-help">Valores recomendados: 1, 2, 4 y 8.</small>
            </>
          )}
          <button className="secondary-button" type="button" onClick={() => void handleSearch()} disabled={!selectedFile || isRunning || isValidating}>
            {isRunning ? 'Ejecutando...' : 'Ejecutar búsqueda'} <span>→</span>
          </button>
            </>
          ) : (
            <>
              <label className="field-label" htmlFor="adversarial-algorithm">Método adversarial</label>
              <select id="adversarial-algorithm" value={adversarialAlgorithm} onChange={(event) => setAdversarialAlgorithm(event.target.value as 'MINIMAX' | 'ALFA_BETA')}>
                <option value="ALFA_BETA">Alfa-Beta - poda optimizada</option>
                <option value="MINIMAX">Minimax - árbol completo</option>
              </select>
              <label className="field-label" htmlFor="depth">Profundidad máxima</label>
              <select
                id="depth"
                value={depth}
                onChange={(event) => setDepth(Number(event.target.value))}
              >
                {Array.from({ length: 8 }, (_, index) => index + 1).map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
              <small className="field-help">Límite permitido por el proyecto: 1 a 8 niveles.</small>
              <button className="secondary-button" type="button" onClick={() => void handleAdversarial()} disabled={!selectedFile || isRunning || isValidating}>
                {isRunning ? 'Evaluando...' : 'Evaluar turno'} <span>→</span>
              </button>
            </>
          )}
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
          {adversarialResult && (
            <section className="decision-card">
              <div className="section-label">DECISIÓN TÁCTICA / {adversarialResult.algoritmo}</div>
              <h3>Recomendación para el bando {scenario?.turno}</h3>
              <p className="decision-action">
                {adversarialResult.accion_seleccionada
                  ? `${adversarialResult.accion_seleccionada.unidad_id}: (${adversarialResult.accion_seleccionada.origen?.fila}, ${adversarialResult.accion_seleccionada.origen?.columna}) → (${adversarialResult.accion_seleccionada.destino?.fila}, ${adversarialResult.accion_seleccionada.destino?.columna})`
                  : 'No hay una acción legal disponible.'}
              </p>
              <div className="decision-metrics">
                <span>Valor <strong>{adversarialResult.valor_obtenido.toFixed(4)}</strong></span>
                <span>Nodos <strong>{adversarialResult.nodos_generados}</strong></span>
                <span>Evaluados <strong>{adversarialResult.nodos_evaluados}</strong></span>
                <span>Podados <strong>{adversarialResult.nodos_podados}</strong></span>
                <span>Profundidad <strong>{adversarialResult.profundidad_alcanzada}</strong></span>
                <span>Tiempo <strong>{(adversarialResult.tiempo * 1000).toFixed(2)} ms</strong></span>
              </div>
            </section>
          )}
        </div>
      </section>

      {scenario && <ScenarioSummary escenario={scenario} />}

      {isAdversarialMode ? (
        adversarialResult
          ? <AdversarialTree root={adversarialResult.arbol} />
          : (
            <section className="tree-panel tree-empty">
              <div className="section-label">03 / ÁRBOL ADVERSARIAL</div>
              <p>Evalúa el turno para visualizar el árbol de decisiones.</p>
            </section>
          )
      ) : <ResultsDashboard results={resultHistory} />}
    </main>
  )
}

export default App
