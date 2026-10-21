# Manual de usuario: TacticalGrid

Guía de uso de la interfaz. Explica cómo cargar escenarios, ejecutar búsquedas
y decisiones adversariales, simular partidas y interpretar las alertas.

Cada elemento se describe y se referencia al código de la interfaz. Los recuadros
`[IMAGEN]` indican dónde adjuntar la captura de pantalla correspondiente al
exportar este manual a PDF.

> **[IMAGEN 0 — Vista general de la aplicación]**
> Adjuntar una captura de la interfaz completa recién abierta, mostrando el
> tablero, la barra superior, el panel de controles y el espacio del dashboard.
> *Pie de figura sugerido:* "Pantalla principal de TacticalGrid."

---

## 1. Flujo de carga de escenarios

1. Pulsa **"Cargar escenario"** para abrir el selector de archivos
   (`frontend/src/App.tsx:473`). Solo se aceptan archivos `.json`.
2. El archivo se valida en el backend (`POST /api/scenario/validate`). Si es
   válido, se aplica al tablero con un aviso de éxito.
3. Si el archivo es inválido, se muestra una alerta con la regla incumplida y
   **el escenario actual no se borra**: `handleFile` solo llama a `setScenario`
   cuando la validación tiene éxito (`frontend/src/App.tsx:125`).

> **[IMAGEN 1 — Botón "Cargar escenario"]**
> Adjuntar una captura del botón "Cargar escenario" resaltado en el panel de
> controles.
> *Pie de figura sugerido:* "Botón para cargar un escenario JSON."

> **[IMAGEN 2 — Alerta de escenario cargado con éxito]**
> Adjuntar una captura de la alerta verde de éxito tras cargar un escenario
> válido.
> *Pie de figura sugerido:* "Confirmación de carga válida."

> **[IMAGEN 3 — Alerta de escenario inválido]**
> Adjuntar una captura de la alerta de error mostrando la regla incumplida y el
> tablero anterior que se conserva.
> *Pie de figura sugerido:* "Rechazo de un escenario inválido sin borrar el
> actual."

### Selector de ejemplos

El desplegable **"Casos demostrativos"** (`frontend/src/App.tsx:479`) carga los
Casos 1 a 10 desde `frontend/public/casos/` sin usar el selector de archivos.
También se pueden cargar escenarios externos (`examples/externo_*.json`)
manualmente con el botón de carga.

El selector incluye las dos variantes del Caso 6:

- `Caso 6 · Portador A`
- `Caso 6 · Portador B`

> **[IMAGEN 4 — Desplegable "Casos demostrativos"]**
> Adjuntar una captura del desplegable abierto mostrando la lista de casos.

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
ejecución con su algoritmo, parámetros y métricas comparables. Las dos
ejecuciones de A* se conservan como filas independientes cuando se usan
Manhattan y Euclídea.

> **[IMAGEN 5 — Controles de búsqueda]**
> Adjuntar una captura del panel con "Método de búsqueda", "Heurística", "Ancho
> de memoria (k)" y el botón "Ejecutar búsqueda".
> *Pie de figura sugerido:* "Controles del modo búsqueda."

> **[IMAGEN 6 — Ruta resaltada en el tablero]**
> Adjuntar una captura del tablero con el camino hallado resaltado tras ejecutar
> una búsqueda.

> **[IMAGEN 7 — Dashboard de resultados]**
> Adjuntar una captura del dashboard mostrando algoritmo, parámetros, éxito,
> costo, longitud, nodos generados/expandidos, frontera y camino.
> *Pie de figura sugerido:* "Métricas de una ejecución de búsqueda."

## 3. Orden de sucesores

La sección **Orden de sucesores** aparece después de cargar un escenario.
Muestra el orden efectivo que se usará para generar movimientos:

```text
ARRIBA, DERECHA, ABAJO, IZQUIERDA
```

Si el JSON incluye `orden_sucesores`, se muestra ese orden. Si no lo incluye,
se usa el orden predeterminado anterior. Los botones de subir y bajar permiten
editar la lista y **Restaurar orden predeterminado** devuelve la configuración
original.

El orden editado se incorpora al escenario enviado antes de ejecutar búsquedas,
comparaciones adversariales y simulaciones de partida. Esto permite estudiar
cómo cambia la exploración y la poda de Alfa-Beta, especialmente en el Caso 9.

> **[IMAGEN 8 — Editor de orden de sucesores]**
> Adjuntar una captura del listado de direcciones con los botones para subir,
> bajar y restaurar el orden predeterminado.
> *Pie de figura sugerido:* "Configuración interactiva del orden de sucesores."

## 4. Controles adversariales

Cuando el escenario es de modo `adversarial`:

- **Profundidad máxima** (`frontend/src/App.tsx`): 1 a 8.
- **Analizar Minimax y Alfa-Beta**: ejecuta ambos algoritmos con la misma
  profundidad y orden de sucesores.

La comparación muestra una tabla con la acción, el valor, los nodos generados,
los nodos evaluados, los nodos podados, la profundidad y el tiempo de cada
algoritmo. También dibuja dos árboles independientes:

- **Árbol Minimax**: representa la exploración completa.
- **Árbol Alfa-Beta**: muestra además las ramas podadas.

La leyenda distingue nodos **explorados**, **evaluados** y **podados**; los
nodos podados se resaltan en rojo. La reducción de nodos se calcula como:

```text
((nodos Minimax - nodos Alfa-Beta) / nodos Minimax) × 100
```

> **[IMAGEN 9 — Controles y comparación adversarial]**
> Adjuntar una captura con la profundidad, el botón de análisis, la tabla y los
> dos árboles.
> *Pie de figura sugerido:* "Comparación visual de Minimax y Alfa-Beta."

## 5. Flujo del modo partida automática

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

> **[IMAGEN 10 — Controles del modo partida]**
> Adjuntar una captura del panel con los botones "Siguiente turno", "Calcular
> partida completa" y "Reiniciar partida".

> **[IMAGEN 11 — Reproducción de la partida]**
> Adjuntar una captura durante la reproducción, mostrando los controles
> "Anterior", "Iniciar/Pausar", "Siguiente" y "Velocidad de juego".
> *Pie de figura sugerido:* "Reproducción paso a paso de una partida."

## 6. Robo, escape, bloqueo y empate por bucle

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

> **[IMAGEN 12 — Recolección del recurso]**
> Adjuntar una captura del momento en que una unidad pisa la casilla del recurso
> libre y lo recoge.

> **[IMAGEN 13 — Robo y escape]**
> Adjuntar una captura del instante posterior a un robo, con el ladrón
> alejándose (escenario `escenario_robo_bandera`).

> **[IMAGEN 14 — Bloqueo y retorno del recurso]**
> Adjuntar una captura del mensaje/estado en que el recurso vuelve a su posición
> original por bloqueo (escenario `escenario_bandera_bloqueada`).

> **[IMAGEN 15 — Empate por bucle]**
> Adjuntar una captura del fin de partida en `empate` indicando que se repitió el
> estado completo.

## 7. Alertas temporales

Las alertas aparecen en la parte superior de la interfaz.

- **Duración**: 10 segundos (`NOTICE_DURATION_MS`, `frontend/src/App.tsx:24`).
- **Pausa al pasar el cursor**: al mantener el puntero sobre la alerta, su
  tiempo se detiene y se reanuda al salir
  (`frontend/src/App.tsx:435`).
- **Barra de tiempo**: la franja inferior muestra el tiempo restante
  (`frontend/src/App.tsx:445`).
- **Cierre manual**: el botón `x` cierra la alerta de inmediato.

> **[IMAGEN 16 — Alerta temporal con barra de tiempo]**
> Adjuntar una captura de una alerta con la barra inferior mostrando el tiempo
> restante y el botón de cierre `x`.
> *Pie de figura sugerido:* "Alerta temporal de 10 segundos."

## 8. Ventana pequeña

La interfaz se adapta al ancho de la ventana:

- Por debajo de 800 px, el espacio de trabajo pasa a una sola columna
  (`frontend/src/App.css:1151`).
- Por debajo de 480 px, se oculta la barra de estado superior y se reduce el
  margen (`frontend/src/App.css:1177`).

> **[IMAGEN 17 — Vista en ventana pequeña]**
> Adjuntar una captura del diseño en una sola columna (ancho < 800 px) y, si es
> posible, otra con la barra de estado oculta (ancho < 480 px).
> *Pie de figura sugerido:* "Diseño adaptable a ventanas estrechas."
