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
    | ScenarioValidationResponse
    | { detail?: string }

  if (!response.ok) {
    throw new Error('detail' in body ? body.detail : 'No se pudo validar el escenario')
  }

  return body as ScenarioValidationResponse
}

export { API_BASE_URL }
