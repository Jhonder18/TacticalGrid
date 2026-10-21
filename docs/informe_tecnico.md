# Informe técnico: TacticalGrid

**Sistemas Inteligentes I — Primer corte**
**Integrantes:** Carlos Gómez, Jhon Hander Patiño Londoño
**Versión:** v1.0

---

## Índice

1. [Introducción y pregunta central](#1-introducción-y-pregunta-central)
2. [Modelado del problema](#2-modelado-del-problema)
3. [Representación de estados](#3-representación-de-estados)
4. [Reglas del juego](#4-reglas-del-juego)
5. [Costos del terreno](#5-costos-del-terreno)
6. [Algoritmos de búsqueda](#6-algoritmos-de-búsqueda)
7. [Heurísticas de A*](#7-heurísticas-de-a)
8. [Beam Search](#8-beam-search)
9. [Minimax, Alfa-Beta y función de utilidad](#9-minimax-alfa-beta-y-función-de-utilidad)
10. [Visualización en la interfaz](#10-visualización-en-la-interfaz)
11. [Validación de escenarios y verificación de soluciones](#11-validación-de-escenarios-y-verificación-de-soluciones)
12. [Metodología experimental](#12-metodología-experimental)
13. [Resultados de los Casos 1 a 10](#13-resultados-de-los-casos-1-a-10)
14. [Análisis de complejidad](#14-análisis-de-complejidad)
15. [Limitaciones](#15-limitaciones)
16. [Reporte del uso de IA](#16-reporte-del-uso-de-ia)
17. [Cómo reproducir los experimentos](#17-cómo-reproducir-los-experimentos)

---

## 1. Introducción y pregunta central

TacticalGrid es una plataforma académica para ejecutar, observar y medir
algoritmos de inteligencia artificial sobre un tablero cuadriculado 2D. Dos
bandos compiten por un recurso estratégico situado en zona neutral: cada equipo
intenta tomarlo y llevarlo a su propia base.

La pregunta central del proyecto es:

> ¿Cómo cambia la forma de decidir de un sistema inteligente cuando pasa de
> encontrar una ruta, a optimizar su costo, a usar conocimiento heurístico y,
> finalmente, a actuar frente a un adversario que también razona?

La solución separa estrictamente cuatro capas: representación del escenario,
lógica del juego, algoritmos de búsqueda/decisión e interfaz. Los algoritmos no
contienen posiciones ni dimensiones codificadas: todo se lee del JSON del
escenario.

> **[IMAGEN — Vista general de la aplicación]**
> Adjuntar una captura de la interfaz completa con un escenario cargado,
> mostrando el tablero, los controles y el dashboard.
> *Pie de figura sugerido:* "Plataforma TacticalGrid en ejecución."

---

## 2. Modelado del problema

El proyecto recorre cuatro etapas de complejidad creciente, cada una con la
misma base de escenario:

1. **Navegación (búsqueda no informada).** Una unidad se desplaza de un inicio a
   un objetivo ignorando al adversario. Se resuelve con BFS y DFS.
2. **Costo (búsqueda basada en costos).** Entran los costos del terreno. Se
   resuelve con UCS, que minimiza el costo acumulado y no la cantidad de
   movimientos.
3. **Conocimiento del entorno (búsqueda informada).** A* con `f(n) = g(n) + h(n)`
   y dos heurísticas. Beam Search limita la memoria de la frontera.
4. **Adversario (decisión adversarial).** Ambos bandos razonan. Se resuelve con
   Minimax y Alfa-Beta sobre un árbol de profundidad limitada.

La representación interna del estado se diseña para cubrir las cuatro etapas:
una simple coordenada no basta cuando hay varias unidades, turnos y posesión del
recurso.

---

## 3. Representación de estados

El estado interno es `GameState` (`backend/models/game_state.py`) e incluye:

- Posición de **todas** las unidades (no solo de una).
- Bando y turno activo.
- Identificador del **portador del recurso** (`None` si está libre).
- **Posición del recurso** cuando no lo transporta nadie.

La clave del estado (`state_key`) combina estos elementos, de modo que dos
situaciones con una unidad en la misma casilla pueden ser **estados distintos**:
por ejemplo, si en una la unidad transporta el recurso y en la otra no. Esto se
demuestra en el Caso 6.

> **[IMAGEN — Estados con misma posición y distinto portador]**
> Adjuntar dos capturas del Caso 6 (portador A1 y portador B1) que muestren la
> misma posición de unidad pero distinto portador y distinta decisión.
> *Pie de figura sugerido:* "La posesión del recurso forma parte del estado."

El `GameState` permite identificar de forma inequívoca: el estado inicial, las
acciones válidas, los estados sucesores, la condición objetivo y el costo de cada
acción.

---

## 4. Reglas del juego

Las reglas se acordaron explícitamente y son deterministas:

- **Turnos:** en cada turno un bando mueve **una** unidad con **un** movimiento.
- **Movimiento:** únicamente ortogonal (sin diagonales); no se permite permanecer
  inmóvil.
- **Recolección:** si una unidad pisa la casilla del recurso libre, lo recoge
  automáticamente.
- **Robo:** una unidad del bando contrario roba al quedar adyacente (Manhattan = 1)
  al portador tras moverse. El robo es automático, no una acción aparte.
- **Escape:** tras robar, el ladrón realiza hasta **dos movimientos adicionales**
  para alejarse. Rompe el ciclo inmediato de robo y recuperación.
- **Bloqueo:** si el portador queda sin camino legal a su base (el rival cerró el
  corredor), el recurso vuelve a su posición original y queda libre.
- **Victoria:** gana el bando cuyo portador llega a su **propia** base.
- **Empate:** si se repite el estado completo (bucle) o se agota el límite de
  turnos, la partida termina en empate.
- **No hay capturas:** las unidades no se eliminan; solo se bloquean posiciones.

El código de estas reglas está en `backend/core/successors.py` (generación de
sucesores, robo y escape) y `backend/core/game.py` (`apply_action`,
`get_game_status`, retorno del recurso bloqueado).

> **[IMAGEN — Recolección y robo del recurso]**
> Adjuntar capturas de la secuencia: unidad pisa el recurso (recolección) y una
> unidad rival queda adyacente al portador (robo).
> *Pie de figura sugerido:* "Recolección y robo del recurso."

---

## 5. Costos del terreno

El catálogo de terrenos vive en el JSON, dentro de `tipos_terreno`, con su
`costo` y `transitable`:

| Terreno | Costo | Transitable |
| --- | --- | --- |
| camino | 1 | Sí |
| pasto | 2 | Sí |
| bosque | 4 | Sí |
| pantano | 7 | Sí |
| muro | — | No |

Los costos **no** están codificados en los algoritmos: se leen del escenario
(`backend/core/successors.py:137`). El costo de una transición es el costo del
terreno de **destino**. El profesor puede cambiar el costo de un terreno sin tocar
el código; la aplicación se adapta (verificado en T-22 y T-27).

> **[IMAGEN — Laberinto con distintos tipos de terreno]**
> Adjuntar una captura del tablero con los tipos de terreno visibles (camino,
> pasto, bosque, pantano, muro) y su estilo/leyenda de colores.
> *Pie de figura sugerido:* "Tipos de terreno y sus costos."

---

## 6. Algoritmos de búsqueda

| Algoritmo | Criterio | Frontera | Idea |
| --- | --- | --- | --- |
| BFS | Número de movimientos | Cola FIFO | Explora por niveles; ruta más corta en pasos |
| DFS | Número de movimientos | Pila LIFO | Baja por una rama; pocos nodos, ruta más larga |
| UCS | Costo acumulado | Cola de prioridad | Minimiza el costo, no los pasos |
| A* | `g(n) + h(n)` | Cola de prioridad | Usa heurística para orientar la búsqueda |
| Beam Search | Heurística | Solo los `k` mejores | Limita la frontera a `k` nodos |

Todos comparten la misma generación de sucesores, por lo que la única diferencia
entre ellos es el criterio de orden en la frontera. Código en
`backend/algorithms/blind_search.py`.

> **[IMAGEN — Rutas de BFS, DFS y UCS]**
> Adjuntar capturas de las tres rutas sobre el mismo mapa (Casos 1 y 2)
> mostrando cómo BFS/DFS minimizan pasos y UCS minimiza costo.
> *Pie de figura sugerido:* "Ruta más corta (BFS) frente a ruta más económica
> (UCS)."

---

## 7. Heurísticas de A*

A* evalúa `f(n) = g(n) + h(n)`, donde `g(n)` es el costo acumulado y `h(n)` una
estimación del costo restante. Se implementan dos heurísticas
(`backend/algorithms/heuristics.py`):

### Manhattan

- **Qué estima:** distancia ortogonal `|Δfila| + |Δcolumna|`.
- **Información:** posiciones de origen y objetivo.
- **Costo:** `O(1)`.
- **Admisible:** sí (nunca sobreestima, porque cada movimiento avanza una celda
  ortogonal).
- **Fortalezas/debilidades:** orienta bien en mapas abiertos; pierde
  discriminación cuando los obstáculos obligan a rodear.

### Euclídea (heurística propia)

- **Qué estima:** distancia en línea recta
  `sqrt(Δfila² + Δcolumna²)`, ajustada por el costo mínimo transitable.
- **Información:** posiciones y el costo mínimo del catálogo de terrenos.
- **Costo:** `O(1)` por estado, `O(t)` una vez por búsqueda (`t` tipos de terreno).
- **Admisible:** sí, es una subestimación del costo real.
- **Fortalezas/debilidades:** útil cuando los terrenos baratos dominan; pierde
  discriminación cuando el costo real se aleja del producto distancia × costo
  mínimo.

Ambas pueden entregar la **misma ruta y costo** (son admisibles); la diferencia
aparece en el orden de exploración, medido por los nodos generados/expandidos
(Caso 4). El detalle está en `docs/heuristicas_y_utilidad.md`.

> **[IMAGEN — A* con Manhattan y A* con Euclídea]**
> Adjuntar dos capturas del Caso 4 (misma ruta, distinto conteo de nodos) y una
> del Caso 3 donde A* rodea el obstáculo.
> *Pie de figura sugerido:* "Ambas heurísticas hallan la misma ruta con distinto
> orden de exploración."

---

## 8. Beam Search

Beam Search conserva solo los `k` mejores nodos de cada nivel. Con `k` pequeño la
búsqueda es barata pero puede descartar el camino conveniente y **no encontrar
solución**; al crecer `k` explora más y aumenta la probabilidad de hallarla, a
mayor costo. El efecto se mide en el Caso 5 con `k = 1, 2, 4 y 8`.

> **[IMAGEN — Beam Search con k = 1 y k = 2]**
> Adjuntar dos capturas del Caso 5: con `k = 1` (sin solución) y con `k = 2`
> (con solución), comparando nodos generados.
> *Pie de figura sugerido:* "Efecto del ancho de memoria en Beam Search."

---

## 9. Minimax, Alfa-Beta y función de utilidad

- **Minimax** explora el árbol de decisiones con profundidad limitada (máx 8).
- **Alfa-Beta** aplica la misma evaluación con poda α/β: descarta ramas que no
  pueden mejorar la decisión.
- **MAX** representa al bando que mueve primero; **MIN** al contrario. No son
  inteligencias distintas: ambos usan las mismas reglas. Disminuir la utilidad de
  MAX es, por definición, favorecer a MIN.

### Función de utilidad

`evaluate_utility(state, player, scenario)` (`backend/core/utility.py:16`) evalúa
desde la perspectiva del jugador que representa a MAX. Combina tres componentes
normalizados:

| Componente | Peso |
| --- | --- |
| Cercanía relativa al recurso | 0.30 |
| Avance del portador hacia su base | 0.40 |
| Amenaza relativa de las unidades enemigas | 0.30 |

Valores terminales: victoria de MAX `+100000`, victoria de MIN `-100000`, empate
`0`. La utilidad terminal domina la fórmula heurística. Con la misma
configuración (profundidad, utilidad y orden), Minimax y Alfa-Beta eligen la
**misma acción y el mismo valor**; Alfa-Beta genera menos nodos (Casos 8, 10).

El orden de sucesores es configurable vía `orden_sucesores` (extensión propia del
JSON). Cambiarlo puede aumentar la poda sin cambiar la decisión (Caso 9).

> **[IMAGEN — Árbol adversarial y poda alfa-beta]**
> Adjuntar una captura del árbol de decisión con la leyenda de colores y nodos
> podados en rojo (Casos 7 u 8).
> *Pie de figura sugerido:* "Árbol explorado con poda alfa-beta."

> **[IMAGEN — Comparación Minimax vs Alfa-Beta]**
> Adjuntar una captura del resumen de comparación (misma decisión/valor y
> reducción de nodos) para una misma profundidad.

---

## 10. Visualización en la interfaz

La interfaz (React + TypeScript + Vite) muestra la cuadrícula con tipos de
terreno, obstáculos, bases, recurso, unidades, bando, portador y turno. Al
ejecutar una búsqueda se resalta el camino hallado. El panel adversarial dibuja el
**árbol explorado** con conectores y distingue nodos **explorados**, **evaluados**
y **podados** (en rojo). El modo partida reproduce el historial paso a paso, con
pausa, velocidad y detección de bucles. Los detalles de uso están en el manual de
usuario.

> **[IMAGEN — Elementos del tablero]**
> Adjuntar una captura anotada del tablero señalando terreno, obstáculo, base,
> recurso, unidades, bando, portador y turno.
> *Pie de figura sugerido:* "Elementos representados en la cuadrícula."

> **[IMAGEN — Reproducción de la partida]**
> Adjuntar una captura del modo partida durante la reproducción, con los
> controles de paso y velocidad.
> *Pie de figura sugerido:* "Reproducción paso a paso de una partida."

---

## 11. Validación de escenarios y verificación de soluciones

**Validación** (`backend/models/scenario.py`): la carga es completa o no se
aplica. Se comprueba dimensiones positivas, matriz consistente, terrenos
definidos, costos positivos, posiciones dentro del mapa, unidades sobre celdas
transitables, ids únicos, bandos válidos, turno válido y portador coherente. Un
escenario inválido se rechaza sin dejar el estado parcialmente cargado.

**Verificación de soluciones** (`backend/core/route_verification.py`): confirma
que cada movimiento del camino es válido, que no se atraviesan obstáculos, que el
costo reportado coincide con las transiciones y que el estado final cumple el
objetivo. También verifica que las acciones de Minimax sean legales.

> **[IMAGEN — Validación de un escenario inválido]**
> Adjuntar una captura de la alerta de error al cargar un escenario inválido
> (por ejemplo `examples/bad/externo_costo_negativo.json`).
> *Pie de figura sugerido:* "Rechazo de un escenario inválido."

---

## 12. Metodología experimental

Los experimentos se diseñaron como **casos reproducibles y deterministas**:

1. Cada caso es un escenario JSON versionado en `examples/good/`.
2. Los algoritmos son deterministas (mismo escenario → mismo resultado); el
   número aleatorio no interviene.
3. Las métricas se capturan por ejecución real, nunca a mano: el script
   `backend/scripts/generar_informe_casos.py` recorre los casos y escribe
   `examples/reportes/informe_casos_1_10.json`.
4. Para cada caso se declara un **resultado esperado** (razonamiento previo) y se
   contrasta con el **resultado obtenido**.
5. El campo `tiempo` se omite del JSON reproducible por no ser determinista; se
   observa en vivo desde la interfaz.

Los diez casos se alinean con los exigidos por el enunciado: BFS/DFS, ruta corta
vs económica, obstáculo y heurística, comparación de heurísticas, Beam Search,
estado compuesto, decisión adversarial, Minimax vs alfa-beta, orden de acciones y
profundidad.

> **[IMAGEN — Botón "Descargar informe JSON"]**
> Adjuntar una captura del botón "Descargar informe JSON" en la interfaz, que
> genera el informe reproducible vía `POST /api/report/full`.
> *Pie de figura sugerido:* "Generación del informe reproducible desde la
> interfaz."

---

## 13. Resultados de los Casos 1 a 10

Todas las cifras provienen del informe reproducible
(`examples/reportes/informe_casos_1_10.json`). Se muestran las métricas clave.

### Caso 1 — BFS frente a DFS

| Algoritmo | Éxito | Costo | Longitud | Nodos generados |
| --- | --- | --- | --- | --- |
| BFS | Sí | 55 | 34 | 665 |
| DFS | Sí | 67 | 40 | 76 |

BFS logra menor longitud y costo; DFS genera muchos menos nodos pero con ruta más
larga y costosa.

> **[IMAGEN — Caso 1: BFS y DFS]**
> Adjuntar capturas de la ruta hallada por BFS y por DFS sobre el mismo mapa, con
> sus métricas en el dashboard.

### Caso 2 — Ruta corta (BFS) vs ruta económica (UCS)

| Algoritmo | Éxito | Costo | Longitud |
| --- | --- | --- | --- |
| BFS | Sí | 46 | 6 |
| UCS | Sí | 8 | 8 |

BFS llega en 6 movimientos con costo 46; UCS acepta 8 movimientos para bajar el
costo a 8. Los caminos son distintos.

> **[IMAGEN — Caso 2: BFS vs UCS]**
> Adjuntar capturas de ambas rutas (corta y económica) con sus costos y
> longitudes en el dashboard.

### Caso 3 — Obstáculo y heurística (A*)

| Algoritmo | h | Éxito | Costo | Longitud |
| --- | --- | --- | --- | --- |
| A* | MANHATTAN | Sí | 14 | 14 |

A* rodea la barrera y llega al objetivo.

> **[IMAGEN — Caso 3: desvío del obstáculo]**
> Adjuntar la captura del laberinto con el obstáculo y la ruta de A* rodeándolo.

### Caso 4 — Comparación de heurísticas

| Algoritmo | h | Éxito | Costo | Longitud | Nodos generados |
| --- | --- | --- | --- | --- | --- |
| A* | MANHATTAN | Sí | 55 | 34 | 606 |
| A* | Euclídea (propia) | Sí | 55 | 34 | 621 |

Mismo camino y costo; cambia el orden de exploración.

> **[IMAGEN — Caso 4: Manhattan vs Euclídea]**
> Adjuntar las dos capturas del dashboard (mismos costo/longitud y distinto
> conteo de nodos) para ambas heurísticas.

### Caso 5 — Beam Search con distintos `k`

| k | Éxito | Costo | Longitud | Nodos generados |
| --- | --- | --- | --- | --- |
| 1 | No | 0 | 0 | 7 |
| 2 | Sí | 10 | 10 | 30 |
| 4 | Sí | 10 | 10 | 47 |
| 8 | Sí | 10 | 10 | 79 |

Con `k = 1` falla; con `k ≥ 2` encuentra la solución y los nodos crecen con `k`.

> **[IMAGEN — Caso 5: Beam Search k = 1, 2, 4 y 8]**
> Adjuntar capturas de cada valor de `k`, destacando el fallo con `k = 1` y el
> crecimiento de nodos.

### Caso 6 — Estado compuesto (portador distinto)

| Escenario | Misma acción | Mismo valor | Nodos Minimax | Nodos Alfa-Beta |
| --- | --- | --- | --- | --- |
| Portador A (A1) | Sí | Sí | 399 | 88 |
| Portador B (B1) | Sí | Sí | 513 | 164 |

Mismo mapa con distinto portador: cambia la decisión y la carga de nodos.

> **[IMAGEN — Caso 6: portador A1 vs B1]**
> Adjuntar las dos capturas (portador A1 y portador B1) mostrando la distinta
> acción recomendada.

### Caso 7 — Decisión adversarial (intercepción)

| Algoritmo | Acción | Valor | Nodos generados | Nodos podados |
| --- | --- | --- | --- | --- |
| Minimax | A1 (10,10)→(10,11) | -0.2267 | 1150 | 0 |
| Alfa-Beta | A1 (10,10)→(10,11) | -0.2267 | 202 | 184 |

La mejor acción acerca A1 al portador rival en lugar de perseguir el recurso.

> **[IMAGEN — Caso 7: intercepción del portador]**
> Adjuntar la captura del tablero con la acción recomendada que acerca a A1 al
> portador rival, y su árbol adversarial.

### Caso 8 — Minimax frente a Alfa-Beta

| Algoritmo | Acción | Valor | Nodos generados | Nodos podados |
| --- | --- | --- | --- | --- |
| Minimax | A1 (9,9)→(9,10) | 0.2976 | 9247 | 0 |
| Alfa-Beta | A1 (9,9)→(9,10) | 0.2976 | 697 | 1409 |

Misma decisión y valor; Alfa-Beta reduce los nodos un **92.46 %**.

> **[IMAGEN — Caso 8: Minimax vs Alfa-Beta]**
> Adjuntar una captura del resumen de comparación con la misma acción/valor y la
> reducción de nodos del 92.46 %.

### Caso 9 — Orden de acciones

| Variante | Acción | Valor | Nodos Alfa-Beta | Nodos podados |
| --- | --- | --- | --- | --- |
| Orden propio | A1 (9,9)→(9,10) | 0.299 | 174 | 126 |
| Orden por defecto | A1 (9,9)→(9,10) | 0.299 | 174 | 126 |

El orden de sucesores no cambia la decisión pero afecta la poda.

> **[IMAGEN — Caso 9: efecto del orden de sucesores]**
> Adjuntar una captura del árbol podado con `orden_sucesores` aplicado.

### Caso 10 — Profundidad

| Prof. | Algoritmo | Nodos generados | Nodos podados | Reducción Alfa-Beta |
| --- | --- | --- | --- | --- |
| 2 | Minimax | 91 | 0 | — |
| 2 | Alfa-Beta | 37 | 54 | 59.34 % |
| 3 | Minimax | 963 | 0 | — |
| 3 | Alfa-Beta | 208 | 152 | 78.40 % |
| 5 | Minimax | 99003 | 0 | — |
| 5 | Alfa-Beta | 3561 | 3967 | 96.40 % |

A mayor profundidad, más carga; el ahorro de Alfa-Beta crece con la profundidad.

> **[IMAGEN — Caso 10: profundidades 2, 3 y 5]**
> Adjuntar capturas del dashboard para cada profundidad, comparando nodos
> generados de Minimax y Alfa-Beta.

### Simulación de partidas

| Escenario | Estado final | Turnos | Motivo |
| --- | --- | --- | --- |
| `escenario_partida` | victoria_A | 53 | — |
| `escenario_robo_bandera` | victoria_A | 10 | — |
| `escenario_bandera_bloqueada` | empate | 12 | Bucle: se repitió el estado completo |

> **[IMAGEN — Simulación de partidas y estados terminales]**
> Adjuntar capturas del estado final de cada partida: `victoria_A` (partida
> estándar), `victoria_A` (robo de bandera) y `empate` por bucle.
> *Pie de figura sugerido:* "Estados terminales de las partidas simuladas."

---

## 14. Análisis de complejidad

Con `b` = factor de ramificación y `d` = profundidad de la solución:

| Método | Tiempo | Espacio |
| --- | --- | --- |
| BFS | O(b^d) | O(b^d) |
| DFS | O(b^m) | O(b·m) |
| UCS | O((V+E) log V) | O(V) |
| A* | O((V+E) log V) | O(V) |
| Beam Search | O(b·d) por nivel | O(k) en la frontera |
| Manhattan | O(1) | O(1) |
| Euclídea | O(1) por estado | O(1) |
| Generación de sucesores | O(u) ocupación + O(4u) movimientos | O(u) |
| Minimax | O(b^p) | O(b·p) |
| Alfa-Beta | O(b^(p/2)) en el mejor caso | O(b·p) |

`p` es la profundidad adversarial (máx 8), `u` el número de unidades, `V` estados
y `E` transiciones. La poda de Alfa-Beta reduce el factor efectivo del árbol.

---

## 15. Limitaciones

- Una sola acción por turno y una sola unidad movida: no hay movimiento
  simultáneo ni concurrencia.
- Movimiento estrictamente ortogonal (sin diagonales).
- No existen capturas ni eliminación de unidades: solo bloqueo de posiciones.
- El campo `tipo` de la unidad es **descriptivo**; no altera reglas, costos ni
  utilidad.
- El orden de sucesores no se edita desde la interfaz en vivo; se configura en el
  JSON (`orden_sucesores`) o en una constante del código para estudiar la poda.
- La profundidad adversarial está limitada a 8 para acotar el tiempo de cómputo.
- El campo `tiempo` no es determinista y se omite de los informes reproducibles.
- Las partidas usan un límite de turnos proporcional al mapa
  (`min(500, max(50, 4·filas·columnas))`) para evitar partidas infinitas.

---

## 16. Reporte del uso de IA

Se utilizó IA generativa como herramienta de apoyo en refactorización, redacción
de pruebas y documentación. La trazabilidad es explícita:

- **Registro en el código.** Los métodos relevantes llevan docstrings con
  `Purpose`, `Preconditions`, `Postconditions`, `Complexity`, `AI usage`,
  `AI intervention` y `Student validation`, declarando si la IA intervino y cómo
  se validó.
- **Validación de aportes.** Todo código generado fue leído, adaptado al contrato
  del proyecto y probado. Los resultados numéricos se reproducen con scripts y
  pruebas, no se transcriben a mano.
- **Ausencia de posiciones codificadas.** Un test escanea
  `backend/algorithms/*.py` para confirmar que no hay coordenadas ni dimensiones
  literales (`backend/tests/test_external_scenario.py`).
- **Consistencia documental.** Un test verifica que la documentación coincide con
  las constantes reales del código
  (`backend/tests/test_documentation_consistency.py`).

Cada estudiante es responsable del código entregado y de explicarlo, modificarlo
y defenderlo durante la sustentación.

---

## 17. Cómo reproducir los experimentos

```powershell
# Suite completa (107 pruebas)
python -m unittest discover -s backend/tests

# Informe consolidado de los Casos 1 a 10
python -m backend.scripts.generar_informe_casos
```

El informe queda en `examples/reportes/informe_casos_1_10.json`. Desde la
interfaz, el botón **"Descargar informe JSON"** genera el mismo contenido vía
`POST /api/report/full`. Los escenarios están en `examples/` y los casos
mínimos en `frontend/public/casos/`.
