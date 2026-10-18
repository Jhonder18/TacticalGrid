import type { Coordenada, Escenario, Unidad } from '../types/types'
import type { CSSProperties } from 'react'
import { getTerrainPresentation } from './terrainStyles'

interface GridProps {
  escenario: Escenario
  camino?: Coordenada[]
  objetivo?: Coordenada
}

function samePosition(first: Coordenada, second: Coordenada): boolean {
  return first.fila === second.fila && first.columna === second.columna
}

function getUnitAt(
  unidades: Unidad[],
  fila: number,
  columna: number,
): Unidad | undefined {
  return unidades.find((unidad) => unidad.fila === fila && unidad.columna === columna)
}

function terrainClass(terrainName: string, transitable: boolean): string {
  if (!transitable) return 'wall'

  const normalizedName = terrainName
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()

  if (normalizedName.includes('bosque') || normalizedName.includes('forest')) {
    return 'forest'
  }
  if (normalizedName.includes('pasto') || normalizedName.includes('grass')) {
    return 'grass'
  }
  if (normalizedName.includes('pantano') || normalizedName.includes('swamp')) {
    return 'swamp'
  }
  return 'path'
}

function terrainStyle(
  terrainName: string,
  transitable: boolean,
): CSSProperties {
  const color = getTerrainPresentation(terrainName, transitable).color
  return { '--terrain-color': color } as CSSProperties
}

function getCellLabel(
  terrainName: string,
  unit: Unidad | undefined,
  isBaseA: boolean,
  isBaseB: boolean,
  isResource: boolean,
  isCarrier: boolean,
): string {
  const elements = [terrainName]
  if (isBaseA) elements.push('Base A')
  if (isBaseB) elements.push('Base B')
  if (isResource) elements.push('recurso')
  if (unit) elements.push(`unidad ${unit.id}, bando ${unit.bando}`)
  if (isCarrier) elements.push('portador del recurso')
  return elements.join(', ')
}

export function Grid({ escenario, camino = [], objetivo }: GridProps) {
  const { mapa, terreno, tipos_terreno, bases, recurso, unidades, juego } = escenario
  const rows = Array.from({ length: mapa.filas }, (_, fila) => fila)
  const columns = Array.from({ length: mapa.columnas }, (_, columna) => columna)

  return (
    <div className="grid-wrap">
      <div
        className="grid-coordinates top"
        style={{ gridTemplateColumns: `repeat(${mapa.columnas}, 1fr)` }}
      >
        {columns.map((column) => (
          <span key={column}>{String(column).padStart(2, '0')}</span>
        ))}
      </div>
      <div className="grid-body">
        <div
          className="grid-coordinates side"
          style={{ gridTemplateRows: `repeat(${mapa.filas}, 1fr)` }}
        >
          {rows.map((row) => (
            <span key={row}>{String(row).padStart(2, '0')}</span>
          ))}
        </div>
        <div
          className="map-grid"
          style={{
            gridTemplateColumns: `repeat(${mapa.columnas}, minmax(0, 1fr))`,
            gridTemplateRows: `repeat(${mapa.filas}, minmax(0, 1fr))`,
          }}
        >
          {rows.flatMap((fila) =>
            columns.map((columna) => {
              const position = { fila, columna }
              const terrainName = terreno[fila][columna]
              const terrain = tipos_terreno[terrainName]
              const unit = getUnitAt(unidades, fila, columna)
              const isBaseA = samePosition(bases.A, position)
              const isBaseB = samePosition(bases.B, position)
              const isCarrier = unit?.id === juego.portador_recurso
              const isResource = juego.portador_recurso === null && samePosition(recurso, position)
              const isRoute = camino.some((point) => samePosition(point, position))
              const isObjective = objetivo !== undefined && samePosition(objetivo, position)
              const classes = [
                'cell',
                terrainClass(terrainName, terrain.transitable),
                isRoute ? 'route-cell' : '',
                isObjective ? 'objective-cell' : '',
                isBaseA ? 'base-a' : '',
                isBaseB ? 'base-b' : '',
                isResource ? 'resource' : '',
                unit ? `unit-${unit.bando.toLowerCase()}` : '',
                isCarrier ? 'carrier' : '',
              ].filter(Boolean).join(' ')

              return (
                <div
                  className={classes}
                  style={terrainStyle(terrainName, terrain.transitable)}
                  key={`${fila}-${columna}`}
                  title={getCellLabel(
                    terrainName,
                    unit,
                    isBaseA,
                    isBaseB,
                    isResource,
                    isCarrier,
                  )}
                  aria-label={getCellLabel(
                    terrainName,
                    unit,
                    isBaseA,
                    isBaseB,
                    isResource,
                    isCarrier,
                  )}
                >
                  {isBaseA && <span className="cell-marker base-marker">A</span>}
                  {isBaseB && <span className="cell-marker base-marker">B</span>}
                  {isResource && <span className="cell-marker resource-marker">◆</span>}
                  {unit && (
                    <span className="cell-marker unit-marker">
                      {unit.bando}
                      {isCarrier && <span className="carrier-badge">◆</span>}
                    </span>
                  )}
                  {isObjective && <span className="cell-marker objective-marker">OBJ</span>}
                </div>
              )
            }),
          )}
        </div>
      </div>
    </div>
  )
}
