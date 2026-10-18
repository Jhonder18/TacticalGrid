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
}

export type AlgoritmoBusquedaDisponible =
  | 'BFS'
  | 'DFS'
  | 'UCS'
  | 'A_ESTRELLA'
  | 'BEAM_SEARCH'

export type HeuristicaDisponible = 'MANHATTAN' | 'EUCLIDEA'

export type ResultadoBusqueda = MetricasBusqueda

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
}

export type ResultadoMetricas = MetricasBusqueda | MetricasAdversariales
