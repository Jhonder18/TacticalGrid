# Manual de usuario: TacticalGrid

Guía de uso de la interfaz. Explica cómo cargar escenarios, ejecutar búsquedas
y decisiones adversariales, simular partidas y interpretar las alertas.

No se incluyen capturas de pantalla; cada elemento se describe y se referencia
al código de la interfaz.

---

## 1. Flujo de carga de escenarios

1. Pulsa **"Cargar escenario"** para abrir el selector de archivos
   (`frontend/src/App.tsx:473`). Solo se aceptan archivos `.json`.
2. El archivo se valida en el backend (`POST /api/scenario/validate`). Si es
   válido, se aplica al tablero con un aviso de éxito.
3. Si el archivo es inválido, se muestra una alerta con la regla incumplida y
   **el escenario actual no se borra**: `handleFile` solo llama a `setScenario`
   cuando la validación tiene éxito (`frontend/src/App.tsx:125`).

### Selector de ejemplos

El desplegable **"Casos demostrativos"** (`frontend/src/App.tsx:479`) carga los
Casos 1 a 10 desde `frontend/public/casos/` sin usar el selector de archivos.
También se pueden cargar escenarios externos (`examples/externo_*.json`)
manualmente con el botón de carga.

## 2. Controles de búsqueda

Cuando el escenario es de modo `busqueda`:

- **Método de búsqueda** (`frontend/src/App.tsx:500`): BFS, DFS, UCS, A*,
  Beam Search.
- **Heurística** (`frontend/src/App.tsx:508`): Manhattan o Euclídea (propia);
  solo aplica a A*.
- **Ancho de memoria (k)** (`frontend/src/App.tsx:518`): 1, 2, 4 u 8; solo
  aplica a Beam Search.
- **Ejecutar búsqueda** (`frontend/src/App.tsx:529`): resalta la ruta en el
  tablero y muestra las métricas en el dashboard.

El dashboard (`frontend/src/components/ResultsDashboard.tsx`) lista cada
ejecución con su algoritmo, parámetros y métricas comparables.

## 3. Controles adversariales

Cuando el escenario es de modo `adversarial`:

- **Método adversarial** (`frontend/src/App.tsx:584`): Alfa-Beta o Minimax.
- **Profundidad máxima** (`frontend/src/App.tsx:589`): 1 a 8.
- **Evaluar turno** (`frontend/src/App.tsx:600`): calcula la acción recomendada y
  su árbol.
- **Comparar Minimax vs Alfa-Beta** (`frontend/src/App.tsx:603`): ejecuta ambos y
  resume coincidencia de decisión y reducción de nodos.

El **árbol adversarial** (`frontend/src/components/AdversarialTree.tsx`) dibuja
los nodos explorados con sus conectores. La leyenda distingue nodos
**explorados**, **evaluados** y **podados**; los nodos podados se resaltan en
rojo.

## 4. Flujo del modo partida automática

Cuando el escenario es de modo `partida`:

- **Algoritmo de ambos bandos** y **Heurística**: controlan cómo decide cada
  bando (mismas reglas para ambos; no son inteligencias distintas).
- **Siguiente turno** (`frontend/src/App.tsx:572`): aplica un turno y actualiza
  el tablero.
- **Calcular partida completa** (`frontend/src/App.tsx:575`): simula toda la
  partida y habilita la reproducción por pasos.
- **Reiniciar partida** (`frontend/src/App.tsx:578`): vuelve al estado inicial.

Durante la reproducción (`frontend/src/App.tsx:649`):

- **Anterior** / **Siguiente** avanzan paso a paso;
- **Iniciar / Pausar** reproduce automáticamente;
- **Velocidad de juego** (`frontend/src/App.tsx:657`) ajusta el ritmo.

La simulación devuelve el historial completo; la interfaz reconstruye cada
fotograma desde el estado inicial.

## 5. Robo, escape, bloqueo y empate por bucle

- **Recolección**: si una unidad pisa la casilla del recurso libre, lo recoge
  automáticamente.
- **Robo**: una unidad del bando contrario roba al quedar adyacente al portador
  tras moverse.
- **Escape**: tras robar, el ladrón realiza dos movimientos adicionales para
  alejarse, rompiendo el ciclo de robo inmediato.
- **Bloqueo**: si el portador no tiene camino legal a su base (el rival cerró el
  corredor), el recurso vuelve a su posición original y queda libre.
- **Empate por bucle**: si el estado completo de la partida se repite, la
  partida termina en empate y se muestra el motivo.

Escenarios de ejemplo: `escenario_robo_bandera.json` (robo y escape),
`escenario_bandera_bloqueada.json` (bloqueo y retorno).

## 6. Alertas temporales

Las alertas aparecen en la parte superior de la interfaz.

- **Duración**: 10 segundos (`NOTICE_DURATION_MS`, `frontend/src/App.tsx:24`).
- **Pausa al pasar el cursor**: al mantener el puntero sobre la alerta, su
  tiempo se detiene y se reanuda al salir
  (`frontend/src/App.tsx:435`).
- **Barra de tiempo**: la franja inferior muestra el tiempo restante
  (`frontend/src/App.tsx:445`).
- **Cierre manual**: el botón `x` cierra la alerta de inmediato.

## 7. Ventana pequeña

La interfaz se adapta al ancho de la ventana:

- Por debajo de 800 px, el espacio de trabajo pasa a una sola columna
  (`frontend/src/App.css:1151`).
- Por debajo de 480 px, se oculta la barra de estado superior y se reduce el
  margen (`frontend/src/App.css:1177`).
