export function normalizeTerrainName(name: string): string {
  return name
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

function terrainHash(name: string): number {
  return [...name].reduce(
    (hash, character) => (hash * 31 + character.charCodeAt(0)) % 360,
    0,
  )
}

function getTerrainColor(name: string, transitable: boolean): string {
  if (!transitable) return '#4b5563'

  const normalizedName = normalizeTerrainName(name)
  const knownColors: Record<string, string> = {
    agua: '#3b82f6',
    bosque: '#277a52',
    camino: '#8b7355',
    desierto: '#d79b3d',
    hielo: '#61b7d9',
    lava: '#d94b32',
    montana: '#777b80',
    pantano: '#4d8076',
    pasto: '#64a85b',
    tierra: '#9a673d',
  }

  const knownColor = Object.entries(knownColors).find(([keyword]) =>
    normalizedName.includes(keyword),
  )
  return knownColor
    ? knownColor[1]
    : `hsl(${terrainHash(normalizedName)}, 38%, 52%)`
}

function getContrastColor(background: string): '#182229' | '#ffffff' {
  const hslMatch = background.match(/hsl\(\d+,\s*\d+%,\s*(\d+)%\)/)
  if (hslMatch) return Number(hslMatch[1]) > 58 ? '#182229' : '#ffffff'

  const match = background.match(/\d+/g)
  if (!match || match.length < 3) return '#ffffff'
  const [red, green, blue] = match.slice(-3).map(Number)
  const luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255
  return luminance > 0.58 ? '#182229' : '#ffffff'
}

export function getTerrainPresentation(
  terrainName: string,
  transitable: boolean,
): { color: string; textColor: '#182229' | '#ffffff' } {
  const color = getTerrainColor(terrainName, transitable)
  return { color, textColor: getContrastColor(color) }
}
