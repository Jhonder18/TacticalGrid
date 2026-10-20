import { useCallback, useEffect, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { Grid } from './components/Grid'
import { AdversarialTree } from './components/AdversarialTree'
import { AdversarialComparison } from './components/AdversarialComparison'
import { ResultsDashboard } from './components/ResultsDashboard'
import { ScenarioSummary } from './components/ScenarioSummary'
import { runAdversarial, runAdversarialComparison, runFullReport, runGameTurn, runSearch, simulateGame, validateScenario } from './services/api'
import type {
  AlgoritmoBusquedaDisponible,
  Escenario,
  EjecucionBusqueda,
  HeuristicaDisponible,
  ResultadoBusqueda,
  ResultadoAdversarial,
  ResultadoComparacionAdversarial,
  EstadoPartida,
  ResultadoTurno,
  ResultadoSimulacion,
} from './types/types'
import './App.css'

type Notice = { type: 'success' | 'error'; message: string } | null
const NOTICE_DURATION_MS = 10_000

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
  const [noticeRemaining, setNoticeRemaining] = useState(NOTICE_DURATION_MS)
  const noticePausedRef = useRef(false)
  const [fileName, setFileName] = useState('Ningún escenario cargado')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [scenario, setScenario] = useState<Escenario | null>(null)
  const [initialScenario, setInitialScenario] = useState<Escenario | null>(null)
  const [algorithm, setAlgorithm] = useState<AlgoritmoBusquedaDisponible>('BFS')
  const [heuristic, setHeuristic] = useState<HeuristicaDisponible>('MANHATTAN')
  const [beamWidth, setBeamWidth] = useState(1)
  const [searchResult, setSearchResult] = useState<ResultadoBusqueda | null>(null)
  const [adversarialResult, setAdversarialResult] = useState<ResultadoAdversarial | null>(null)
  const [adversarialComparison, setAdversarialComparison] = useState<ResultadoComparacionAdversarial | null>(null)
  const [adversarialAlgorithm, setAdversarialAlgorithm] = useState<'MINIMAX' | 'ALFA_BETA'>('ALFA_BETA')
  const [depth, setDepth] = useState(2)
  const [resultHistory, setResultHistory] = useState<EjecucionBusqueda[]>([])
  const [isValidating, setIsValidating] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [gameStatus, setGameStatus] = useState<EstadoPartida>('en curso')
  const [lastGameAction, setLastGameAction] = useState<ResultadoTurno['accion'] | null>(null)
  const [gameAlgorithm, setGameAlgorithm] = useState<AlgoritmoBusquedaDisponible>('BFS')
  const [gameHeuristic, setGameHeuristic] = useState<HeuristicaDisponible>('MANHATTAN')
  const [gameBeamWidth, setGameBeamWidth] = useState(4)
  const [gameSimulation, setGameSimulation] = useState<ResultadoSimulacion | null>(null)
  const [gameHistoryIndex, setGameHistoryIndex] = useState(-1)
  const [gameStepIndex, setGameStepIndex] = useState(-1)
  const [isGamePlaying, setIsGamePlaying] = useState(false)
  const [gameSpeed, setGameSpeed] = useState(50)
  const scenarioMode = scenario?.prueba?.modo ?? 'busqueda'
  const isAdversarialMode = scenarioMode !== 'busqueda'
  const isPartidaMode = scenarioMode === 'partida'
  const nextTurn = scenario?.turno === 'A' ? 'B' : 'A'

  useEffect(() => {
    noticePausedRef.current = false
    if (!notice) return

    const startedAt = Date.now()
    let pausedAt: number | null = null
    let pausedDuration = 0
    const resetProgress = window.setTimeout(
      () => setNoticeRemaining(NOTICE_DURATION_MS),
      0,
    )
    const timer = window.setInterval(() => {
      if (noticePausedRef.current) {
        pausedAt ??= Date.now()
        return
      }
      if (pausedAt !== null) {
        pausedDuration += Date.now() - pausedAt
        pausedAt = null
      }
      const elapsed = Date.now() - startedAt - pausedDuration
      const remaining = Math.max(0, NOTICE_DURATION_MS - elapsed)
      setNoticeRemaining(remaining)
      if (remaining === 0) {
        setNotice(null)
      }
    }, 100)

    return () => {
      window.clearTimeout(resetProgress)
      window.clearInterval(timer)
    }
  }, [notice])

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
      const loadedScenario = JSON.parse(raw) as Escenario
      setScenario(loadedScenario)
      setInitialScenario(loadedScenario)
      setSelectedFile(file)
      setSearchResult(null)
      setAdversarialResult(null)
      setAdversarialComparison(null)
      setResultHistory([])
      setGameStatus('en curso')
      setLastGameAction(null)
      setGameSimulation(null)
      setGameHistoryIndex(-1)
      setGameStepIndex(-1)
      setIsGamePlaying(false)
      setFileName(file.name)
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

  const handleGameTurn = async () => {
    if (!selectedFile || !scenario || gameStatus !== 'en curso') return
    if (gameSimulation) {
      advanceGameHistory(1)
      return
    }
    setIsRunning(true)
    setNotice(null)
    try {
      const result = await runGameTurn(selectedFile, gameAlgorithm, gameHeuristic, gameBeamWidth)
      const updatedScenario = applyTurnResult(scenario, result)
      setScenario(updatedScenario)
      setSelectedFile(new File([JSON.stringify(updatedScenario)], fileName, { type: 'application/json' }))
      setGameStatus(result.estado_partida)
      setLastGameAction(result.accion)
      setNotice({
        type: 'success',
        message: result.estado_partida === 'en curso'
          ? `Turno aplicado. Ahora juega el bando ${result.turno_siguiente}.`
          : `La partida terminó: ${result.estado_partida}.`,
      })
    } catch (error) {
      setNotice({
        type: 'error',
        message: error instanceof Error ? error.message : 'No se pudo aplicar el turno.',
      })
    } finally {
      setIsRunning(false)
    }

  }

  const handlePlayGame = async () => {
    if (!selectedFile || !scenario || gameStatus !== 'en curso') return
    setIsRunning(true)
    setIsGamePlaying(false)
    setNotice(null)
    try {
      const simulation = await simulateGame(selectedFile, gameAlgorithm, gameHeuristic, gameBeamWidth)
      setGameSimulation(simulation)
      setGameHistoryIndex(-1)
      setGameStepIndex(-1)
      setNotice({
        type: simulation.estado_final === 'empate' ? 'error' : 'success',
        message: simulation.motivo_final
          ? `${simulation.motivo_final} Se calcularon ${simulation.turnos_ejecutados} turnos.`
          : `Simulación calculada: ${simulation.turnos_ejecutados} turnos. Usa los controles para recorrerla.`,
      })
    } catch (error) {
      setNotice({
        type: 'error',
        message: error instanceof Error ? error.message : 'No se pudo ejecutar la partida.',
      })
    } finally {
      setIsRunning(false)
    }
  }

  const showGameStep = useCallback((turnIndex: number, stepIndex: number) => {
    if (!gameSimulation || !initialScenario) return
    let frame = structuredClone(initialScenario)
    for (let index = 0; index < turnIndex; index += 1) {
      frame = applyTurnResult(frame, gameSimulation.historial[index])
    }
    const turn = gameSimulation.historial[turnIndex]
    const step = turn.pasos[stepIndex]
    setGameHistoryIndex(turnIndex)
    setGameStepIndex(stepIndex)
    setScenario(applyStateToScenario(frame, step.estado))
    setGameStatus(stepIndex === turn.pasos.length - 1 ? turn.estado_partida : 'en curso')
    setLastGameAction(step.accion)
  }, [gameSimulation, initialScenario])

  const advanceGameHistory = useCallback((direction: 1 | -1) => {
    if (!gameSimulation || !scenario) return
    let nextTurnIndex = gameHistoryIndex
    let nextStepIndex = gameStepIndex
    if (direction === 1) {
      if (nextTurnIndex < 0) {
        nextTurnIndex = 0
        nextStepIndex = 0
      } else if (nextStepIndex + 1 < gameSimulation.historial[nextTurnIndex].pasos.length) {
        nextStepIndex += 1
      } else if (nextTurnIndex + 1 < gameSimulation.historial.length) {
        nextTurnIndex += 1
        nextStepIndex = 0
      }
    } else if (nextTurnIndex < 0) {
      return
    } else if (nextStepIndex > 0) {
      nextStepIndex -= 1
    } else if (nextTurnIndex > 0) {
      nextTurnIndex -= 1
      nextStepIndex = gameSimulation.historial[nextTurnIndex].pasos.length - 1
    } else {
      nextTurnIndex = -1
      nextStepIndex = -1
    }

    setGameHistoryIndex(nextTurnIndex)
    setGameStepIndex(nextStepIndex)
    if (nextTurnIndex < 0) {
      setScenario(structuredClone(initialScenario ?? scenario))
      setGameStatus('en curso')
      setLastGameAction(null)
      return
    }
    showGameStep(nextTurnIndex, nextStepIndex)
  }, [gameHistoryIndex, gameSimulation, gameStepIndex, initialScenario, scenario, showGameStep])

  useEffect(() => {
    if (!isGamePlaying || !gameSimulation) return
    const lastTurnIndex = gameSimulation.historial.length - 1
    const lastStepIndex = gameSimulation.historial[lastTurnIndex].pasos.length - 1
    if (gameHistoryIndex === lastTurnIndex && gameStepIndex >= lastStepIndex) {
      const timer = window.setTimeout(() => setIsGamePlaying(false), 0)
      return () => window.clearTimeout(timer)
    }
    const delay = Math.max(100, 1100 - gameSpeed * 10)
    const timer = window.setTimeout(() => advanceGameHistory(1), delay)
    return () => window.clearTimeout(timer)
  }, [advanceGameHistory, gameHistoryIndex, gameSimulation, gameSpeed, gameStepIndex, isGamePlaying])

  const handleRestartGame = () => {
    if (!initialScenario) return
    const restored = structuredClone(initialScenario)
    setScenario(restored)
    setSelectedFile(new File([JSON.stringify(restored)], fileName, { type: 'application/json' }))
    setGameStatus('en curso')
    setLastGameAction(null)
    setGameSimulation(null)
    setGameHistoryIndex(-1)
    setGameStepIndex(-1)
    setIsGamePlaying(false)
    setNotice({ type: 'success', message: 'La partida fue reiniciada.' })
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

  const selectQuickCase = (event: ChangeEvent<HTMLSelectElement>) => {
    if (event.target.value) {
      void handleQuickCase(event.target.value)
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
        { resultado: result, heuristica: heuristic, k: algorithm === 'BEAM_SEARCH' ? beamWidth : null },
        ...previous.filter((entry) => entry.resultado.algoritmo !== result.algoritmo),
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

  const handleAdversarialComparison = async () => {
    if (!selectedFile) {
      setNotice({ type: 'error', message: 'Carga un escenario válido antes de comparar.' })
      return
    }

    setIsRunning(true)
    setNotice(null)
    try {
      const result = await runAdversarialComparison(selectedFile, depth)
      setAdversarialComparison(result)
      setNotice({
        type: 'success',
        message: result.misma_accion && result.mismo_valor
          ? `Minimax y Alfa-Beta coinciden; Alfa-Beta redujo ${result.reduccion_nodos_porcentaje.toFixed(2)}% de nodos.`
          : 'Minimax y Alfa-Beta difieren en su decisión.',
      })
    } catch (error) {
      setNotice({
        type: 'error',
        message: error instanceof Error ? error.message : 'No se pudo comparar los algoritmos.',
      })
    } finally {
      setIsRunning(false)
    }
  }

  const handleDownloadReport = async () => {
    setIsRunning(true)
    setNotice(null)
    try {
      const report = await runFullReport()
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'informe_casos_1_10.json'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      setNotice({ type: 'success', message: 'Informe de los Casos 1 a 10 descargado.' })
    } catch (error) {
      setNotice({
        type: 'error',
        message: error instanceof Error ? error.message : 'No se pudo generar el informe.',
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
        <div
          className={`toast toast-${notice.type}`}
          role="alert"
          onMouseEnter={() => {
            noticePausedRef.current = true
          }}
          onMouseLeave={() => {
            noticePausedRef.current = false
          }}
        >
          <span className="toast-icon">{notice.type === 'success' ? 'OK' : '!'}</span>
          <span className="toast-message">{notice.message}</span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Cerrar alerta">x</button>
          <span className="toast-progress" style={{ width: `${(noticeRemaining / NOTICE_DURATION_MS) * 100}%` }} />
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
              <label className="field-label" htmlFor="quick-case">Casos demostrativos</label>
              <select
                id="quick-case"
                defaultValue=""
                disabled={isValidating || isRunning}
                onChange={selectQuickCase}
              >
                <option value="">Selecciona un ejemplo...</option>
                {quickCases.map((quickCase) => (
                  <option key={quickCase.id} value={quickCase.file}>{quickCase.label}</option>
                ))}
              </select>
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
            <option value="EUCLIDEA">Euclídea (propia)</option>
          </select>
          {algorithm === 'A_ESTRELLA' && (
            <small className="field-help">Heurística activa: {heuristic === 'MANHATTAN' ? 'Manhattan' : 'Euclídea (propia)'}.</small>
          )}
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
          ) : isPartidaMode ? (
            <>
              <div className="game-status-card">
                <strong>Partida automática</strong>
                <span>Estado: {gameStatus}</span>
                <span>Turno del backend: {scenario?.turno}</span>
                {lastGameAction && (
                  <span>
                    Última decisión: {lastGameAction.unidad_id} → ({lastGameAction.destino?.fila}, {lastGameAction.destino?.columna})
                  </span>
                )}
              </div>
              <label className="field-label" htmlFor="partida-algorithm">Algoritmo de ambos bandos</label>
              <select
                id="partida-algorithm"
                value={gameAlgorithm}
                disabled={isRunning || gameStatus !== 'en curso'}
                onChange={(event) => setGameAlgorithm(event.target.value as AlgoritmoBusquedaDisponible)}
              >
                {Object.entries(algorithmLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
              <label className="field-label" htmlFor="partida-heuristic">Heurística</label>
              <select
                id="partida-heuristic"
                value={gameHeuristic}
                disabled={isRunning || gameStatus !== 'en curso' || gameAlgorithm !== 'A_ESTRELLA'}
                onChange={(event) => setGameHeuristic(event.target.value as HeuristicaDisponible)}
              >
                <option value="MANHATTAN">Manhattan</option>
                <option value="EUCLIDEA">Euclídea (propia)</option>
              </select>
              {gameAlgorithm === 'BEAM_SEARCH' && (
                <>
                  <label className="field-label" htmlFor="partida-beam-width">Ancho de Beam Search</label>
                  <select id="partida-beam-width" value={gameBeamWidth} disabled={isRunning || gameStatus !== 'en curso'} onChange={(event) => setGameBeamWidth(Number(event.target.value))}>
                    {[1, 2, 4, 8].map((value) => <option key={value} value={value}>{value}</option>)}
                  </select>
                </>
              )}
              <button className="secondary-button" type="button" onClick={() => void handleGameTurn()} disabled={isRunning || isValidating || gameStatus !== 'en curso'}>
                {isRunning ? 'Ejecutando...' : 'Siguiente turno'} <span>→</span>
              </button>
              <button className="secondary-button" type="button" onClick={() => void handlePlayGame()} disabled={isRunning || isValidating || gameStatus !== 'en curso'}>
                Calcular partida completa <span>↗</span>
              </button>
              <button className="secondary-button game-restart-button" type="button" onClick={handleRestartGame} disabled={isRunning || !initialScenario}>
                Reiniciar partida
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
              <button className="secondary-button" type="button" onClick={() => void handleAdversarialComparison()} disabled={!selectedFile || isRunning || isValidating}>
                Comparar Minimax vs Alfa-Beta <span>⇄</span>
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
            <div className="turn-badge">
              <span>Turno actual</span>
              <strong>{scenario?.turno ?? 'A'}</strong>
              {isPartidaMode && <small>Siguiente: {nextTurn}</small>}
            </div>
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
          {isPartidaMode && gameSimulation && (
            <div className="game-history-controls">
              <div className="game-history-buttons">
                <button type="button" onClick={() => advanceGameHistory(-1)} disabled={isRunning || (gameHistoryIndex < 0 && gameStepIndex < 0)}>Anterior</button>
                <button type="button" className="play-button" onClick={() => setIsGamePlaying((playing) => !playing)} disabled={isRunning || gameSimulation.historial.length === 0}>
                  {isGamePlaying ? 'Pausar' : 'Iniciar'}
                </button>
                <button type="button" onClick={() => advanceGameHistory(1)} disabled={isRunning || (gameHistoryIndex === gameSimulation.historial.length - 1 && gameStepIndex >= gameSimulation.historial[gameHistoryIndex].pasos.length - 1)}>Siguiente</button>
              </div>
              <div className="game-speed-control">
                <label htmlFor="game-speed">Velocidad de juego</label>
                <input id="game-speed" type="range" min="10" max="100" step="10" value={gameSpeed} onChange={(event) => setGameSpeed(Number(event.target.value))} />
                <output htmlFor="game-speed">{gameSpeed}%</output>
              </div>
              <span>
                Turno {Math.max(0, gameHistoryIndex + 1)} · Paso {Math.max(0, gameStepIndex + 1)} · Resultado: {gameSimulation.estado_final}
                {gameSimulation.motivo_final ? ` · ${gameSimulation.motivo_final}` : ''}
              </span>
              <ol className="game-history-list">
                {gameSimulation.historial.map((turn, index) => (
                  <li className={index === gameHistoryIndex ? 'active' : ''} key={`${turn.accion.unidad_id}-${index}`}>
                    <div>
                      T{index + 1}: {turn.accion.unidad_id} ({turn.accion.destino?.fila}, {turn.accion.destino?.columna}) · {turn.estado_partida}
                    </div>
                    {turn.pasos.length > 1 && (
                      <ol className="game-turn-steps">
                        {turn.pasos.map((step, stepIndex) => (
                          <li className={index === gameHistoryIndex && stepIndex === gameStepIndex ? 'active' : ''} key={`${index}-${stepIndex}`}>
                            <button
                              type="button"
                              className="game-step-button"
                              onClick={() => showGameStep(index, stepIndex)}
                            >
                            {stepIndex === 0 ? 'Robo / movimiento' : `Escape ${stepIndex}`}:
                            {' '}
                            ({step.accion.origen?.fila}, {step.accion.origen?.columna})
                            {' → '}
                            ({step.accion.destino?.fila}, {step.accion.destino?.columna})
                            {stepIndex === 0 && turn.estado.portador_recurso === turn.accion.unidad_id
                              ? ' · recurso tomado'
                              : ''}
                            </button>
                          </li>
                        ))}
                      </ol>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          )}
          <div className="status-line">
            <span className="status-dot" />
            {isRunning ? 'Ejecutando búsqueda...' : searchResult?.exito ? 'Ruta encontrada y resaltada en el tablero.' : 'Carga un escenario para ejecutar una búsqueda.'}
          </div>
          <button className="secondary-button report-button" type="button" onClick={() => void handleDownloadReport()} disabled={isRunning || isValidating}>
            Descargar informe JSON <span>↓</span>
          </button>
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

      {isAdversarialMode && !isPartidaMode ? (
        adversarialResult
          ? <AdversarialTree root={adversarialResult.arbol} />
          : (
            <section className="tree-panel tree-empty">
              <div className="section-label">03 / ÁRBOL ADVERSARIAL</div>
              <p>Evalúa el turno para visualizar el árbol de decisiones.</p>
            </section>
          )
      ) : <ResultsDashboard results={resultHistory} />}

      {isAdversarialMode && !isPartidaMode && adversarialComparison && (
        <AdversarialComparison comparacion={adversarialComparison} />
      )}
    </main>
  )
}

function applyTurnResult(scenario: Escenario, result: ResultadoTurno): Escenario {
  return applyStateToScenario(scenario, result.estado)
}

function applyStateToScenario(scenario: Escenario, state: ResultadoTurno['estado']): Escenario {
  const units = scenario.unidades.map((unit) => {
    const updated = state.unidades.find((candidate) => candidate.id === unit.id)
    return updated ? { ...unit, ...updated.posicion } : unit
  })
  const carrier = state.portador_recurso
  const carrierUnit = units.find((unit) => unit.id === carrier)
  return {
    ...scenario,
    unidades: units,
    turno: state.turno,
    recurso: carrierUnit ? { fila: carrierUnit.fila, columna: carrierUnit.columna } : state.posicion_recurso ?? scenario.recurso,
    juego: { ...scenario.juego, portador_recurso: carrier },
  }
}

export default App
