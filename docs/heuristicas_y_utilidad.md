# Heurísticas y función de utilidad

Documento técnico de sustentación. Cada afirmación se respalda con la ubicación
real en el código para comprobar que la documentación coincide con la
implementación.

Complementa al [documento técnico](documento_tecnico.md), que describe la
estructura del proyecto, los endpoints, el contrato JSON, las reglas de estado y
los algoritmos.

Índice:

1. [A\*: fórmula f(n) = g(n) + h(n)](#1-a-fórmula-fn--gn--hn)
2. [Distancia Manhattan](#2-distancia-manhattan)
3. [Distancia Euclidiana (heurística propia)](#3-distancia-euclidiana-heurística-propia)
4. [Costo computacional de las heurísticas](#4-costo-computacional-de-las-heurísticas)
5. [Admisibilidad y limitaciones](#5-admisibilidad-y-limitaciones)
6. [Función `evaluate_utility` y sus pesos](#6-función-evaluate_utility-y-sus-pesos)
7. [Valores terminales de victoria y derrota](#7-valores-terminales-de-victoria-y-derrota)
8. [MAX, MIN y el límite de profundidad](#8-max-min-y-el-límite-de-profundidad)
9. [`orden_sucesores` como extensión propia del JSON](#9-orden_sucesores-como-extensión-propia-del-json)
10. [Tabla de trazabilidad documentación → código](#10-tabla-de-trazabilidad-documentación--código)

---

## 1. A\*: fórmula f(n) = g(n) + h(n)

A\* ordena la frontera por una prioridad que combina el costo ya recorrido con
una estimación del costo restante:

```text
f(n) = g(n) + h(n)
```

- `g(n)`: costo real acumulado desde el estado inicial hasta `n`.
- `h(n)`: estimación del costo que falta para llegar al objetivo.
- `f(n)`: prioridad total usada para decidir qué nodo expandir primero.

En el código, A\* empuja cada sucesor a la frontera con prioridad
`successor_cost + estimate(successor_position)`, donde `successor_cost` es
`g(n)` y `estimate(...)` es `h(n)`
(`backend/algorithms/blind_search.py:341` y
`backend/algorithms/blind_search.py:355`).

La frontera es un montículo (`heapq`) y A\* reutiliza los mismos sucesores y el
mismo contrato de métricas que UCS (`backend/algorithms/blind_search.py:318`).

---

## 2. Distancia Manhattan

`backend/algorithms/heuristics.py:9` (`manhattan_distance`).

Fórmula:

```text
h(n) = |fila_actual - fila_objetivo|
     + |columna_actual - columna_objetivo|
```

**Información que utiliza**

- La posición actual como una tupla `(fila, columna)`.
- La posición objetivo como una tupla `(fila, columna)`.

No consulta obstáculos, costos de terreno, otras unidades ni el tamaño del mapa.
Es una estimación puramente geométrica sobre movimiento ortogonal.

Cuando A\* la usa, la escala por el menor costo transitable del escenario para
seguir siendo una cota de costo (`backend/algorithms/blind_search.py:303`):

```text
h(n) = manhattan(actual, objetivo) × costo_mínimo_transitable
```

---

## 3. Distancia Euclidiana (heurística propia)

`backend/algorithms/heuristics.py:31` (`euclidean_distance`).

Fórmula:

```text
h(n) = sqrt((fila_actual - fila_objetivo)^2
          + (columna_actual - columna_objetivo)^2)
```

**Información que utiliza**

- La posición actual `(fila, columna)`.
- La posición objetivo `(fila, columna)`.

Igual que Manhattan, no usa obstáculos, costos ni el resto del estado. Es la
segunda estrategia heurística del proyecto y se expone en la interfaz como
"Euclídea (propia)".

Cuando A\* la usa, también se escala por el menor costo transitable
(`backend/algorithms/blind_search.py:305`):

```text
h(n) = euclidiana(actual, objetivo) × costo_mínimo_transitable
```

---

## 4. Costo computacional de las heurísticas

- Distancia Manhattan: **O(1)** en tiempo y espacio
  (`backend/algorithms/heuristics.py:18`).
- Distancia Euclidiana: **O(1)** en tiempo y espacio
  (`backend/algorithms/heuristics.py:40`).
- Costo mínimo transitable: **O(t)** en tiempo y **O(1)** en espacio, donde `t`
  es el número de tipos de terreno. Se calcula **una sola vez** al inicio de A\*
  (`backend/algorithms/heuristics.py:65` y
  `backend/algorithms/blind_search.py:300`).
- Estimación de cada estado durante la búsqueda: **O(1)**
  (`backend/algorithms/blind_search.py:277`).

---

## 5. Admisibilidad y limitaciones

Una heurística es **admisible** si nunca sobreestima el costo real restante
(`h(n) <= costo real restante`). Esa propiedad es la que garantiza que A\*
encuentre una ruta de costo óptimo.

**Manhattan.** Con movimiento ortogonal (sin diagonales), la distancia Manhattan
es exactamente el número mínimo de movimientos necesarios. Como cada movimiento
cuesta al menos `costo_mínimo_transitable`, multiplicar la distancia por ese
mínimo mantiene la cota inferior:

```text
manhattan(n, objetivo) × costo_mínimo_transitable
    <= costo real restante
```

Por eso es admisible bajo las reglas actuales.

**Euclidiana (propia).** La distancia Euclidiana es siempre menor o igual que la
distancia Manhattan, que a su vez es menor o igual que los movimientos reales
necesarios:

```text
euclidiana(n, objetivo) <= movimientos reales
```

Al multiplicar por el menor costo transitable:

```text
euclidiana(n, objetivo) × costo_mínimo_transitable
    <= costo real restante
```

Por eso la heurística propia también es admisible bajo las reglas actuales
(`HANDOFF_CLAUDE.md`, sección 13).

**Limitaciones**

- Ambas heurísticas ignoran obstáculos y bloques de terreno: en mapas con muros
  la estimación puede quedar muy por debajo del costo real, lo que las hace
  admisibles pero **menos informadas**.
- Al ignorar la ocupación de unidades, no modelan posibles rodeos.
- Manhattan y Euclidiana **pueden producir el mismo camino y el mismo costo** en
  varios mapas. Eso no significa que sean la misma fórmula: una heurística
  cambia el orden de exploración y no está obligada a producir una ruta distinta
  en todos los tableros.

---

## 6. Función `evaluate_utility` y sus pesos

`backend/core/utility.py:16` (`evaluate_utility`) evalúa un estado desde la
perspectiva del bando indicado (`player`, el MAX de la búsqueda adversarial). La
utilidad **positiva** favorece a `player` y la **negativa** favorece al rival.

La utilidad de un estado no terminal combina tres señales normalizadas, cada una
entre -1 y 1, con los pesos declarados en
`backend/core/utility.py:10`:

| Constante | Valor | Señal |
| --- | --- | --- |
| `WEIGHT_RESOURCE` | `0.30` | Proximidad relativa de cada bando al recurso. |
| `WEIGHT_PROGRESS` | `0.40` | Avance del portador hacia su propia base. |
| `WEIGHT_THREAT` | `0.30` | Presión de cada bando sobre el objetivo estratégico rival. |

Fórmula:

```text
utilidad = 0.30 × proximity
         + 0.40 × progress
         + 0.30 × threat
```

Detalles de implementación:

- Cada señal es una **diferencia relativa**: el aporte propio menos el del rival
  (`backend/core/utility.py:73`, `backend/core/utility.py:98` y
  `backend/core/utility.py:114`).
- Las distancias se transforman con `_inverse_distance(d) = 1 / (1 + d)`
  (`backend/core/utility.py:173`), de modo que estar más cerca del objetivo
  aporta una utilidad mayor.
- Todas las distancias usan **Manhattan** (`backend/core/utility.py:86`,
  `backend/core/utility.py:151`).
- Si un bando no tiene unidades, su distancia se trata como `10^6` para
  penalizarlo (`backend/core/utility.py:157`).

---

## 7. Valores terminales de victoria y derrota

`backend/core/utility.py:13`: `TERMINAL_WIN_UTILITY = 100_000.0`.

La utilidad terminal **domina cualquier heurística**. Desde la perspectiva de
`player` (`backend/core/utility.py:36`):

- Victoria de `player`: `+100000.0`.
- Derrota de `player`: `-100000.0`.

Un estado es terminal cuando el portador del recurso llegó a **su propia base**,
es decir, la posición del portador coincide con la base del bando del portador
(`backend/core/utility.py:50` y `backend/algorithms/adversarial.py:234`).

---

## 8. MAX, MIN y el límite de profundidad

`backend/algorithms/adversarial.py`.

- **MAX** es el bando que tiene el turno en el estado inicial del escenario
  (`backend/algorithms/adversarial.py:43`). La búsqueda maximiza su utilidad.
- **MIN** es el bando rival; la búsqueda minimiza la utilidad de MAX.
- Cada nodo se marca como `"MAX"` o `"MIN"` según si su turno coincide con el
  bando del MAX (`backend/algorithms/adversarial.py:219`).
- **Límite de profundidad**: `MAX_MINIMAX_DEPTH = 8`
  (`backend/algorithms/adversarial.py:16`). La profundidad efectiva viene del
  escenario (`juego.profundidad_maxima_minimax`) y se valida contra ese límite
  (`backend/algorithms/adversarial.py:225`).
- El descenso se detiene cuando se alcanza el límite de profundidad, cuando el
  estado es terminal o cuando no hay sucesores; en ese momento se evalúa la
  utilidad del nodo hoja (`backend/algorithms/adversarial.py:90` y
  `backend/algorithms/adversarial.py:138`).
- Alfa-Beta es una variante equivalente a Minimax que poda ramas cuando
  `beta <= alpha`, acelerando la evaluación sin cambiar la decisión óptima
  (`backend/algorithms/adversarial.py:174`).

---

## 9. `orden_sucesores` como extensión propia del JSON

`orden_sucesores` es un **campo propio del proyecto**, permitido por el esquema
del escenario pero **no exigido** por el enunciado original. Es opcional
(`backend/models/scenario.py:62`).

- Tipo: lista de direcciones, cada una `ARRIBA`, `DERECHA`, `ABAJO` o
  `IZQUIERDA`.
- No puede contener direcciones repetidas
  (`backend/models/scenario.py:126`).
- Si se omite, se usa el orden fijo por defecto **arriba, derecha, abajo,
  izquierda**, que hace reproducibles las búsquedas
  (`backend/core/successors.py:50` y `backend/core/successors.py:122`).
- En el frontend, el orden cargado se puede editar antes de ejecutar mediante
  los controles para subir, bajar y restaurar direcciones; el escenario
  configurado se envía al backend.
- El orden solo cambia en qué secuencia se generan los sucesores. Con Alfa-Beta,
  un buen orden (el mejor movimiento primero) aumenta la poda sin alterar la
  decisión final (`backend/core/successors.py:122`,
  caso `examples/good/caso_9_orden_poda.json`).

---

## 10. Tabla de trazabilidad documentación → código

| Punto documentado | Ubicación en el código |
| --- | --- |
| `f(n) = g(n) + h(n)` | `backend/algorithms/blind_search.py:355` |
| Distancia Manhattan | `backend/algorithms/heuristics.py:9` |
| Distancia Euclidiana | `backend/algorithms/heuristics.py:31` |
| Costo mínimo transitable O(t) | `backend/algorithms/heuristics.py:55` |
| Admisibilidad (escalado por costo) | `backend/algorithms/blind_search.py:300` |
| Pesos `0.30 / 0.40 / 0.30` | `backend/core/utility.py:10` |
| Fórmula de utilidad | `backend/core/utility.py:43` |
| `_inverse_distance` | `backend/core/utility.py:173` |
| Centinela `10^6` sin unidades | `backend/core/utility.py:157` |
| Terminal `±100000` | `backend/core/utility.py:13` |
| Condición de victoria | `backend/core/utility.py:50` |
| MAX = bando inicial | `backend/algorithms/adversarial.py:43` |
| Límite de profundidad `8` | `backend/algorithms/adversarial.py:16` |
| Poda `beta <= alpha` | `backend/algorithms/adversarial.py:174` |
| `orden_sucesores` (extensión propia) | `backend/models/scenario.py:62` |
| Orden por defecto | `backend/core/successors.py:50` |
