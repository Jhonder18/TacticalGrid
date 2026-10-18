import { useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { runSearch, validateScenario } from './services/api'
import type {
  AlgoritmoBusquedaDisponible,
  Coordenada,
  Escenario,
  HeuristicaDisponible,
  ResultadoBusqueda,
} from './types/types'
import './App.css'

type Notice = { type: 'success' | 'error'; message: string } | null

const demoCells = [
  'base-a',
  'path',
  'path',
  'forest',
  'forest',
  'path',
  'path',
  'base-b',
  'path',
  'unit-a',
  'path',
  'wall',
  'forest',
  'path',
  'unit-b',
  'path',
  'path',
  'path',
  'resource',
  'wall',
  'path',
  'path',
  'forest',
  'path',
  'path',
  'wall',
  'path',
  'path',
  'forest',
  'path',
  'path',
  'path',
  'path',
  'path',
  'unit-a',
  'path',
  'forest',
  'path',
  'unit-b',
  'path',
  'forest',
  'path',
  'path',
  'path',
  'path',
  'wall',
  'path',
  'path',
  'path',
  'path',
  'path',
  'forest',
  'path',
  'path',
  'path',
  'path',
  'path',
  'path',
  'wall',
  'path',
  'forest',
  'path',
  'path',
  'base-b',
]

const algorithmLabels: Record<AlgoritmoBusquedaDisponible, string> = {
  BFS: 'BFS - amplitud',
  DFS: 'DFS - profundidad',
  UCS: 'UCS - costo uniforme',
  A_ESTRELLA: 'A* - búsqueda informada',
}

function coordinateKey(coordinate: Coordenada): string {
  return `${coordinate.fila},${coordinate.columna}`
}

function terrainClass(name: string, transitable: boolean): string {
  if (!transitable) return 'wall'
  const normalized = name.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  if (normalized === 'camino') return 'path'
  if (normalized === 'pasto') return 'grass'
  if (normalized === 'bosque') return 'forest'
  if (normalized === 'pantano') return 'swamp'
  return 'path'
}

function scenarioCellClass(
  scenario: Escenario,
  result: ResultadoBusqueda | null,
  fila: number,
  columna: number,
): string {
  const terrainName = scenario.terreno[fila][columna]
  const terrain = scenario.tipos_terreno[terrainName]
  const classes = ['cell', terrainClass(terrainName, terrain.transitable)]
  const coordinate = { fila, columna }

  if (
    result?.camino.some(
      (point) => coordinateKey(point) === coordinateKey(coordinate),
    )
  ) {
    classes.push('route-cell')
  }
  if (scenario.bases.A.fila === fila && scenario.bases.A.columna === columna) {
    classes.push('base-a')
  }
  if (scenario.bases.B.fila === fila && scenario.bases.B.columna === columna) {
    classes.push('base-b')
  }
  if (scenario.recurso.fila === fila && scenario.recurso.columna === columna) {
    classes.push('resource')
  }

  const unit = scenario.unidades.find(
    (candidate) => candidate.fila === fila && candidate.columna === columna,
  )
  if (unit) classes.push(unit.bando === 'A' ? 'unit-a' : 'unit-b')

  return classes.join(' ')
}

function App() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [notice, setNotice] = useState<Notice>(null)
  const [fileName, setFileName] = useState('Ningún escenario cargado')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [scenario, setScenario] = useState<Escenario | null>(null)
  const [algorithm, setAlgorithm] = useState<AlgoritmoBusquedaDisponible>('BFS')
  const [heuristic, setHeuristic] = useState<HeuristicaDisponible>('MANHATTAN')
  const [searchResult, setSearchResult] = useState<ResultadoBusqueda | null>(
    null,
  )
  const [isValidating, setIsValidating] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  const handleFile = async (file?: File) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.json')) {
      setNotice({
        type: 'error',
        message: 'Selecciona un archivo con extensión .json.',
      })
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
      setFileName(file.name)
      setNotice({ type: 'success', message: result.mensaje })
    } catch (error) {
      setScenario(null)
      setSelectedFile(null)
      setFileName('Ningún escenario cargado')
      setNotice({
        type: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'No se pudo validar el escenario.',
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
      setNotice({
        type: 'error',
        message: 'Carga un escenario válido antes de ejecutar.',
      })
      return
    }

    setIsRunning(true)
    setSearchResult(null)
    setNotice(null)
    try {
      const result = await runSearch(selectedFile, algorithm, heuristic)
      setSearchResult(result)
      setNotice({
        type: result.exito ? 'success' : 'error',
        message: result.exito
          ? `${algorithmLabels[algorithm]} encontró una ruta.`
          : 'No se encontró una ruta para la configuración seleccionada.',
      })
    } catch (error) {
      setNotice({
        type: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'No se pudo ejecutar la búsqueda.',
      })
    } finally {
      setIsRunning(false)
    }
  }

  const rows = scenario?.mapa.filas ?? 8
  const columns = scenario?.mapa.columnas ?? 8
  const rowCoordinates = Array.from({ length: rows }, (_, index) => index + 1)
  const columnCoordinates = Array.from(
    { length: columns },
    (_, index) => index + 1,
  )
  const gridCells = scenario
    ? Array.from({ length: rows * columns }, (_, index) => ({
        fila: Math.floor(index / columns),
        columna: index % columns,
      }))
    : null

  return (
    <main className="app-shell">
      {notice && (
        <div className={`toast toast-${notice.type}`} role="alert">
          <span className="toast-icon">
            {notice.type === 'success' ? 'OK' : '!'}
          </span>
          <span>{notice.message}</span>
          <button
            type="button"
            onClick={() => setNotice(null)}
            aria-label="Cerrar alerta"
          >
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
        <div className="topbar-status">
          <span className="status-dot" /> Backend conectado
        </div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">SISTEMAS INTELIGENTES I / PROYECTO 01</p>
          <h1>
            Observa cómo <em>piensa</em> el tablero.
          </h1>
          <p className="hero-copy">
            Experimenta con búsqueda, costos y decisiones adversariales en un
            escenario 2D reproducible.
          </p>
        </div>
        <div className="hero-orbit">
          <span>AI</span>
          <i />
          <i />
          <i />
        </div>
      </section>

      <section className="workspace">
        <aside className="sidebar">
          <div className="section-label">01 / ESCENARIO</div>
          <div className="upload-card">
            <div className="upload-icon">↑</div>
            <h2>Carga tu escenario</h2>
            <p>
              Valida la estructura JSON antes de iniciar una experimentación.
            </p>
            <button
              className="primary-button"
              type="button"
              onClick={() => inputRef.current?.click()}
            >
              {isValidating ? 'Validando...' : 'Seleccionar JSON'}
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".json,application/json"
              hidden
              onChange={onFileChange}
            />
            <span className="file-name">{fileName}</span>
          </div>

          <div className="section-label section-label-spaced">
            02 / ALGORITMO
          </div>
          <label className="field-label" htmlFor="algorithm">
            Método de búsqueda
          </label>
          <select
            id="algorithm"
            value={algorithm}
            onChange={(event) =>
              setAlgorithm(event.target.value as AlgoritmoBusquedaDisponible)
            }
          >
            <option value="BFS">{algorithmLabels.BFS}</option>
            <option value="DFS">{algorithmLabels.DFS}</option>
            <option value="UCS">{algorithmLabels.UCS}</option>
            <option value="A_ESTRELLA">{algorithmLabels.A_ESTRELLA}</option>
          </select>
          <label className="field-label" htmlFor="heuristic">
            Heurística
          </label>
          <select
            id="heuristic"
            value={heuristic}
            disabled={algorithm !== 'A_ESTRELLA'}
            onChange={(event) =>
              setHeuristic(event.target.value as HeuristicaDisponible)
            }
          >
            <option value="MANHATTAN">Manhattan</option>
          </select>
          <button
            className="secondary-button"
            type="button"
            onClick={() => void handleSearch()}
            disabled={!selectedFile || isRunning || isValidating}
          >
            {isRunning ? 'Ejecutando...' : 'Ejecutar búsqueda'} <span>→</span>
          </button>
        </aside>

        <div className="board-column">
          <div className="board-heading">
            <div>
              <span className="live-pill">
                {scenario ? 'SCENARIO' : 'LIVE MAP'}
              </span>
              <h2>
                Vista previa del escenario{' '}
                <small>
                  {rows} × {columns}
                </small>
              </h2>
            </div>
            <div className="turn-badge">
              <span>Turno actual</span>
              <strong>{scenario?.turno ?? 'A'}</strong>
            </div>
          </div>
          <div className="board-card">
            <div className="grid-wrap">
              <div
                className="grid-coordinates top"
                style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
              >
                {columnCoordinates.map((number) => (
                  <span key={number}>{String(number).padStart(2, '0')}</span>
                ))}
              </div>
              <div className="grid-body">
                <div
                  className="grid-coordinates side"
                  style={{ gridTemplateRows: `repeat(${rows}, 1fr)` }}
                >
                  {rowCoordinates.map((number) => (
                    <span key={number}>{String(number).padStart(2, '0')}</span>
                  ))}
                </div>
                <div
                  className="map-grid"
                  style={{
                    gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
                  }}
                >
                  {gridCells
                    ? gridCells.map(({ fila, columna }) => (
                        <div
                          className={scenarioCellClass(
                            scenario!,
                            searchResult,
                            fila,
                            columna,
                          )}
                          key={`${fila}-${columna}`}
                          aria-label={`Fila ${fila + 1}, columna ${columna + 1}`}
                        />
                      ))
                    : demoCells.map((cell, index) => (
                        <div
                          className={`cell ${cell}`}
                          key={`${cell}-${index}`}
                          aria-label={cell}
                        />
                      ))}
                </div>
              </div>
            </div>
            <div className="legend">
              <span>
                <i className="legend-swatch base-a" /> Base A
              </span>
              <span>
                <i className="legend-swatch base-b" /> Base B
              </span>
              <span>
                <i className="legend-swatch resource" /> Recurso
              </span>
              <span>
                <i className="legend-swatch wall" /> Obstáculo
              </span>
              <span>
                <i className="legend-swatch route-cell" /> Camino encontrado
              </span>
            </div>
          </div>
          <div className="status-line">
            <span className="status-dot" />
            {isRunning
              ? 'Ejecutando búsqueda...'
              : searchResult?.exito
                ? 'Ruta encontrada y resaltada en el tablero.'
                : 'Carga un escenario para ejecutar una búsqueda.'}
          </div>
        </div>
      </section>

      <section className="metrics-section">
        <div className="section-label">03 / MÉTRICAS DE EXPERIMENTACIÓN</div>
        <div className="metrics-grid">
          <article>
            <span>ESTADOS GENERADOS</span>
            <strong>{searchResult?.estados_generados ?? '—'}</strong>
            <small>Estados incorporados a la búsqueda</small>
          </article>
          <article>
            <span>COSTO ACUMULADO</span>
            <strong>{searchResult ? searchResult.costo : '—'}</strong>
            <small>Según terreno recorrido</small>
          </article>
          <article>
            <span>LONGITUD</span>
            <strong>{searchResult?.longitud_camino ?? '—'}</strong>
            <small>Movimientos del camino</small>
          </article>
          <article>
            <span>TIEMPO</span>
            <strong>
              {searchResult
                ? `${(searchResult.tiempo * 1000).toFixed(2)} ms`
                : '—'}
            </strong>
            <small>Rendimiento del algoritmo</small>
          </article>
        </div>
      </section>
    </main>
  )
}

export default App
