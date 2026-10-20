export interface Coordenada {
  fila: number
  columna: number
}

export interface Terreno {
  costo?: number
  transitable: boolean
}

export interface Mapa {
  filas: number
  columnas: number
}

export interface Bases {
  A: Coordenada
  B: Coordenada
}

export type Bando = 'A' | 'B'

export interface Unidad extends Coordenada {
  id: string
  bando: Bando
  tipo: string
}

export type Unidades = Unidad[]

export type Recurso = Coordenada

export interface Juego {
  portador_recurso: string | null
  profundidad_maxima_minimax: number
}

export type ModoPrueba = 'busqueda' | 'partida' | 'adversarial'

export interface Prueba {
  modo: ModoPrueba
  unidad_inicio?: string
  objetivo?: Coordenada
}

export interface Escenario {
  version: string
  mapa: Mapa
  tipos_terreno: Record<string, Terreno>
  terreno: string[][]
  bases: Bases
  recurso: Recurso
  unidades: Unidades
  turno: Bando
  juego: Juego
  prueba?: Prueba
}

export type EstadoPartida =
  | 'en curso'
  | 'victoria_A'
  | 'victoria_B'
  | 'bloqueado'

export interface EstadoPartidaActual {
  unidades: UnidadEstadoResponse[]
  portador_recurso: string | null
  posicion_recurso: Coordenada | null
  turno: Bando
}

export interface UnidadEstadoResponse {
  id: string
  bando: Bando
  posicion: Coordenada
}

export interface ResultadoTurno {
  algoritmo: AlgoritmoBusquedaDisponible
  heuristica: HeuristicaDisponible
  estado: EstadoPartidaActual
  accion: Accion
  costo: number
  estado_partida: EstadoPartida
  turno_siguiente: Bando | null
  pasos: PasoTurno[]
}

export interface PasoTurno {
  accion: Accion
  estado: EstadoPartidaActual
  costo: number
}

export interface ResultadoSimulacion {
  algoritmo: AlgoritmoBusquedaDisponible
  heuristica: HeuristicaDisponible
  limite_turnos: number
  turnos_ejecutados: number
  estado_final: EstadoPartida | 'empate'
  motivo_final: string | null
  historial: ResultadoTurno[]
}

export type AlgoritmoBusqueda =
  'BFS' | 'DFS' | 'UCS' | 'A_ESTRELLA' | 'BEAM_SEARCH'

export interface MetricasBusqueda {
  algoritmo: AlgoritmoBusqueda
  exito: boolean
  camino: Coordenada[]
  costo: number
  longitud_camino: number
  estados_generados: number
  estados_expandidos: number
  maximo_frontera: number
  tiempo: number
  k?: number | null
}

export type AlgoritmoBusquedaDisponible =
  | 'BFS'
  | 'DFS'
  | 'UCS'
  | 'A_ESTRELLA'
  | 'BEAM_SEARCH'

export type HeuristicaDisponible = 'MANHATTAN' | 'EUCLIDEA'

export type ResultadoBusqueda = MetricasBusqueda

export interface EjecucionBusqueda {
  resultado: ResultadoBusqueda
  heuristica: HeuristicaDisponible
  k: number | null
}

export type AlgoritmoAdversarial = 'MINIMAX' | 'ALFA_BETA'

export interface Accion {
  tipo: string
  unidad_id: string
  origen?: Coordenada
  destino?: Coordenada
}

export interface MetricasAdversariales {
  algoritmo: AlgoritmoAdversarial
  nodos_generados: number
  nodos_evaluados: number
  nodos_podados: number
  profundidad_alcanzada: number
  tiempo: number
  accion_seleccionada: Accion | null
  valor_obtenido: number
  arbol: NodoArbolAdversarial
}

export interface NodoArbolAdversarial {
  id: string
  profundidad: number
  jugador: 'MAX' | 'MIN'
  accion: Accion | null
  valor: number | null
  estado: 'explorado' | 'evaluado' | 'podado' | 'terminal'
  hijos: NodoArbolAdversarial[]
}

export type ResultadoAdversarial = MetricasAdversariales

export interface ResultadoComparacionAdversarial {
  profundidad: number
  minimax: MetricasAdversariales
  alpha_beta: MetricasAdversariales
  misma_accion: boolean
  mismo_valor: boolean
  reduccion_nodos_porcentaje: number
}

export type ResultadoMetricas = MetricasBusqueda | MetricasAdversariales
