import type {
  AlgoritmoBusquedaDisponible,
  HeuristicaDisponible,
  ResultadoBusqueda,
  ResultadoAdversarial,
  Accion,
  ResultadoTurno,
} from '../types/types'

const API_BASE_URL = 'http://localhost:8000'

export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/health`)

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`)
  }

  return response.json() as Promise<{ status: string }>
}

export interface ScenarioValidationResponse {
  valido: boolean
  mensaje: string
}

export async function validateScenario(
  file: File,
): Promise<ScenarioValidationResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/scenario/validate`, {
    method: 'POST',
    body: formData,
  })
  const body = (await response.json()) as
    ScenarioValidationResponse | { detail?: string }

  if (!response.ok) {
    throw new Error(
      'detail' in body ? body.detail : 'No se pudo validar el escenario',
    )
  }

  return body as ScenarioValidationResponse
}

export async function runSearch(
  file: File,
  algoritmo: AlgoritmoBusquedaDisponible,
  heuristica: HeuristicaDisponible = 'MANHATTAN',
  k = 1,
): Promise<ResultadoBusqueda> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('algoritmo', algoritmo)
  formData.append('heuristica', heuristica)
  formData.append('k', String(k))

  const response = await fetch(`${API_BASE_URL}/api/search/run`, {
    method: 'POST',
    body: formData,
  })
  const body = (await response.json()) as
    ResultadoBusqueda | { detail?: string }

  if (!response.ok) {
    throw new Error(
      'detail' in body ? body.detail : 'No se pudo ejecutar la búsqueda',
    )
  }

  return body as ResultadoBusqueda
}

export async function runAdversarial(
  file: File,
  algoritmo: 'MINIMAX' | 'ALFA_BETA',
  profundidad: number,
): Promise<ResultadoAdversarial> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('algoritmo', algoritmo)
  formData.append('profundidad', String(profundidad))

  const response = await fetch(`${API_BASE_URL}/api/adversarial/run`, {
    method: 'POST',
    body: formData,
  })
  const body = (await response.json()) as ResultadoAdversarial | { detail?: string }

  if (!response.ok) {
    throw new Error(
      'detail' in body ? body.detail : 'No se pudo evaluar el turno',
    )
  }

  return body as ResultadoAdversarial
}

export async function runGameTurn(
  file: File,
  accion: Accion,
): Promise<ResultadoTurno> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('accion', JSON.stringify(accion))

  const response = await fetch(`${API_BASE_URL}/api/game/turn`, {
    method: 'POST',
    body: formData,
  })
  const body = (await response.json()) as ResultadoTurno | { detail?: string }

  if (!response.ok) {
    throw new Error(
      'detail' in body ? body.detail : 'No se pudo aplicar el turno',
    )
  }

  return body as ResultadoTurno
}

export { API_BASE_URL }
