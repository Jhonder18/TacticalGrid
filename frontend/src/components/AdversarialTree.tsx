import type { NodoArbolAdversarial } from '../types/types'

interface AdversarialTreeProps {
  root: NodoArbolAdversarial
}

function TreeNode({ node }: { node: NodoArbolAdversarial }) {
  const action = node.accion
  return (
    <li className={`tree-node tree-node-${node.estado}`}>
      <div className="tree-node-card">
        <strong>{node.id}</strong>
        <span>{node.jugador} · nivel {node.profundidad}</span>
        <span className="tree-node-status">{node.estado}</span>
        {action && (
          <small>
            {action.unidad_id}: ({action.origen?.fila},{action.origen?.columna}) → ({action.destino?.fila},{action.destino?.columna})
          </small>
        )}
        {node.valor !== null && <small>valor: {node.valor.toFixed(4)}</small>}
      </div>
      {node.hijos.length > 0 && (
        <div className="tree-children">
          <div className="tree-connector-vertical" aria-hidden="true" />
          <div className="tree-children-row">
            {node.hijos.map((child) => (
              <div className="tree-child-branch" key={child.id}>
                <div className="tree-connector-to-child" aria-hidden="true" />
                <TreeNode node={child} />
              </div>
            ))}
          </div>
        </div>
      )}
    </li>
  )
}

export function AdversarialTree({ root }: AdversarialTreeProps) {
  return (
    <section className="tree-panel">
      <div className="tree-heading">
        <div>
          <div className="section-label">03 / ÁRBOL ADVERSARIAL</div>
          <h2>Decisiones exploradas</h2>
        </div>
        <span className="tree-caption">Los nodos rojos fueron podados</span>
      </div>
      <div className="tree-legend">
        <span className="tree-legend-explored">Explorado</span>
        <span className="tree-legend-evaluated">Evaluado</span>
        <span className="tree-legend-pruned">Podado</span>
      </div>
      <div className="tree-scroll">
        <ul className="adversarial-tree"><TreeNode node={root} /></ul>
      </div>
    </section>
  )
}
