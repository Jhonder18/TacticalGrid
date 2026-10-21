# Documento técnico: TacticalGrid

Documento de sustentación del proyecto. Describe la estructura del sistema, la
API, el contrato JSON, las reglas de partida, los algoritmos, las métricas y la
forma de ejecutar las pruebas. Las referencias `archivo:línea` apuntan al código
real.

Documentos relacionados:

- `docs/informe_tecnico.md`: documento consolidado de entrega (reúne modelado,
  estados, reglas, costos, heurísticas, utilidad, metodología experimental,
  resultados, complejidad, limitaciones y uso de IA).
- `docs/heuristicas_y_utilidad.md`: heurísticas de A* y función de utilidad.
- `docs/informe_resultados_casos.md`: resultados esperados y obtenidos (Casos 1 a 10).
- `docs/manual_usuario.md`: guía de uso de la interfaz.
- `docs/prueba_manual_interfaz.md`: evidencia de la prueba manual (T-28).

---

## 1. Estructura del proyecto

```text
TacticalGrid/
├── backend/
│   ├── main.py                 # Aplicación FastAPI y endpoints
│   ├── algorithms/
│   │   ├── blind_search.py     # BFS, DFS, UCS, A*, Beam Search
│   │   ├── adversarial.py      # Minimax y Alfa-Beta
│   │   └── heuristics.py       # Manhattan, Euclídea y costo mínimo
│   ├── api/                    # Reservado para routers (vacío por ahora)
│   ├── core/
│   │   ├── game.py             # apply_action, get_game_status
│   │   ├── game_policy.py      # Selección de transición para partidas
│   │   ├── game_simulation.py  # simular_partida y utilidades de turno
│   │   ├── successors.py       # Generación de sucesores legales
│   │   ├── route_verification.py # Verificación de rutas y costos
│   │   ├── adversarial_comparison.py # Comparación Minimax vs Alfa-Beta
│   │   ├── adversarial_report.py     # Reporte adversarial
│   │   ├── informe.py          # Informe consolidado Casos 1 a 10
│   │   └── utility.py          # evaluate_utility
│   ├── models/
│   │   ├── scenario.py         # Escenario y validación
│   │   ├── game_state.py       # GameState
│   │   └── results.py          # Modelos de respuesta
│   ├── scripts/                # Generadores de reportes
│   └── tests/                  # Suite de pruebas (unittest)
├── frontend/
│   └── src/
│       ├── App.tsx             # Componente principal y flujo de la interfaz
│       ├── components/         # Grid, ResultsDashboard, AdversarialTree, ...
│       ├── services/api.ts     # Cliente HTTP
│       ├── hooks/              # Hooks auxiliares
│       └── types/types.ts      # Tipos TypeScript
├── docs/                       # Documentación
└── examples/                   # Escenarios JSON (good/, bad/, externo_*)
```

Los módulos `backend/api/` y `frontend/src/hooks/` están reservados; la lógica
activa vive en los archivos listados.

## 2. Endpoints disponibles

Definidos en `backend/main.py`:

| Método | Ruta | Parámetros | Respuesta | Códigos |
| --- | --- | --- | --- | --- |
| GET | `/api/health` | — | `{"status": "ok"}` | 200 |
| POST | `/api/scenario/validate` | `file` (multipart) | `{"valido": true, "mensaje": ...}` | 200 / 400 |
| POST | `/api/search/run` | `file`, `algoritmo`, `heuristica`, `k` | `ResultadoBusqueda` | 200 / 400 |
| POST | `/api/adversarial/run` | `file`, `algoritmo`, `profundidad` | `ResultadoAdversarial` | 200 / 400 |
| POST | `/api/adversarial/compare` | `file`, `profundidad` | `ResultadoComparacionAdversarial` | 200 / 400 |
| POST | `/api/report/full` | — | Informe consolidado Casos 1 a 10 | 200 / 400 |
| POST | `/api/game/turn` | `file`, `algoritmo`, `heuristica`, `k` | `ResultadoTurno` | 200 / 400 |
| POST | `/api/game/simulate` | `file`, `algoritmo`, `heuristica`, `k` | `ResultadoSimulacion` | 200 / 400 |

Notas:

- `algoritmo` de búsqueda: `BFS`, `DFS`, `UCS`, `A_ESTRELLA`, `BEAM_SEARCH`
  (`backend/main.py:75`).
- `heuristica`: `MANHATTAN` o `EUCLIDEA` (`backend/main.py:76`).
- `algoritmo` adversarial: `MINIMAX` o `ALFA_BETA` (`backend/main.py:107`).
- `profundidad`: entero entre 1 y 8 (`backend/main.py:108`).
- El archivo se valida antes de ejecutar; si es inválido se devuelve 400 sin
  aplicar cambios (ver `_load_scenario` en `backend/main.py:241`).

## 3. Contrato JSON

El modelo `Escenario` está en `backend/models/scenario.py:49`. Campos
obligatorios:

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `version` | string | Versión del formato |
| `mapa.filas`, `mapa.columnas` | int > 0 | Dimensiones del tablero |
| `tipos_terreno` | dict | Catálogo: `costo` (> 0 para transitables) y `transitable` |
| `terreno` | matriz de string | Debe coincidir con `mapa` |
| `bases.A`, `bases.B` | coordenada | Bases de cada bando (posiciones distintas) |
| `recurso` | coordenada | Posición inicial del recurso |
| `unidades` | lista | `id` único, `bando` (A/B), `tipo` (descriptivo), `fila`, `columna` |
| `turno` | "A" o "B" | Bando que mueve primero |
| `juego.portador_recurso` | string o null | `id` del portador, o null |
| `juego.profundidad_maxima_minimax` | int 1..8 | Profundidad adversarial |
| `prueba` | objeto o null | Modo y datos de la prueba |
| `orden_sucesores` | lista opcional | Extensión propia (orden de vecinos) |

Modos (`prueba.modo`):

- `busqueda`: requiere `prueba.unidad_inicio` y `prueba.objetivo`
  (`backend/models/scenario.py:148`).
- `partida`: parte de `turno`, `unidades`, `recurso` y `portador_recurso`.
- `adversarial`: mismo estado inicial que `partida`, con profundidad de
  `juego.profundidad_maxima_minimax`.

Validaciones principales (`backend/models/scenario.py:64`): dimensiones
positivas, matriz consistente, terrenos definidos, posiciones dentro del mapa,
bases/unidades/recurso fuera de obstáculos, ids únicos, portador coherente con
la posición del recurso y objetivo transitable. El catálogo de escenarios de
ejemplo está en `examples/README.md`.

## 4. Reglas del estado y de los sucesores

El estado interno es `GameState` (`backend/models/game_state.py`), no una simple
coordenada: incluye posiciones de todas las unidades, portador del recurso,
posición del recurso cuando está libre y turno activo.

### Acciones legales

`get_successors` (`backend/core/successors.py:33`) genera los movimientos del
turno actual:

- Solo mueve unidades del bando activo.
- Movimiento ortogonal (sin diagonales) en el orden `ARRIBA`, `DERECHA`,
  `ABAJO`, `IZQUIERDA` (configurable con `orden_sucesores`).
- El destino debe ser transitable, estar dentro del mapa y no estar ocupado.
- No se permite permanecer en la misma casilla.
- El costo de la transición es el costo del terreno de **destino**
  (`backend/core/successors.py:137`); BFS/DFS priorizan movimientos y UCS/A*
  el costo acumulado.

### Recolección, robo y escape

- Si una unidad pisa la casilla del recurso libre, lo recoge automáticamente
  (`backend/core/successors.py:148`).
- Una unidad roba solo si es del bando contrario al portador y termina su
  movimiento adyacente (Manhattan = 1) al portador
  (`backend/core/successors.py:222`).
- El ladrón realiza hasta **dos movimientos adicionales de escape** en el mismo
  turno, eligiendo alejarse de su base y del portador rival. La secuencia es:
  movimiento que activa el robo, robo automático, escape 1, escape 2.

### Bloqueo y retorno del recurso

Si tras el movimiento el portador no tiene ningún camino legal hasta su base, el
recurso vuelve a su posición original y queda libre
(`_restore_blocked_carrier` en `backend/core/game.py:72`).

### Estados terminales

`get_game_status` (`backend/core/game.py:117`):

- `victoria_A` / `victoria_B`: el portador está sobre su propia base
  (`backend/core/game.py:150`).
- `bloqueado`: el bando activo no tiene acciones legales.
- `en curso`: la partida continúa.

### Límite de turnos y empate

El límite global es `min(500, max(50, 4 · filas · columnas))`
(`turn_limit` en `backend/core/game_simulation.py:21`). Si se repite un estado
completo se declara bucle y empate; si se agota el límite, también empate
(`backend/core/game_simulation.py:163`).

## 5. Algoritmos

| Algoritmo | Archivo | Idea | Frontera |
| --- | --- | --- | --- |
| BFS | `backend/algorithms/blind_search.py:26` | Amplitud por niveles | Cola FIFO |
| DFS | `backend/algorithms/blind_search.py:48` | Profundidad por ramas | Pila LIFO |
| UCS | `backend/algorithms/blind_search.py:172` | Costo acumulado mínimo | Cola de prioridad |
| A* | `backend/algorithms/blind_search.py:263` | `f(n)=g(n)+h(n)` | Cola de prioridad |
| Beam Search | `backend/algorithms/blind_search.py:70` | Haz de ancho `k` | Solo los `k` mejores |
| Minimax | `backend/algorithms/adversarial.py:28` | Valor MAX/MIN por profundidad | Árbol de decisión |
| Alfa-Beta | `backend/algorithms/adversarial.py:32` | Minimax con poda α/β | Árbol podado |

Las heurísticas (Manhattan y Euclídea propia) y la función de utilidad se
detallan en `docs/heuristicas_y_utilidad.md`. La profundidad adversarial máxima
es 8 (`backend/algorithms/adversarial.py:225`).

## 6. Métricas retornadas

### Búsqueda (`ResultadoBusqueda`, `backend/models/results.py:15`)

`algoritmo`, `exito`, `camino`, `costo`, `longitud_camino`,
`estados_generados`, `estados_expandidos`, `maximo_frontera`, `tiempo` y `k`
(solo Beam Search).

### Adversarial (`ResultadoAdversarial`, `backend/models/results.py:38`)

`algoritmo`, `nodos_generados`, `nodos_evaluados`, `nodos_podados`,
`profundidad_alcanzada`, `tiempo`, `accion_seleccionada`, `valor_obtenido` y
`arbol` (árbol explorado como `NodoArbolAdversarial`).

### Comparación (`ResultadoComparacionAdversarial`, `backend/models/results.py:50`)

`profundidad`, `minimax`, `alpha_beta`, `misma_accion`, `mismo_valor` y
`reduccion_nodos_porcentaje`.

## 7. POST /api/game/simulate

Ejecuta una partida automática completa hasta un estado terminal. Pasos
internos (`simular_partida`, `backend/core/game_simulation.py:122`):

1. Construye el `GameState` inicial desde el escenario.
2. Calcula el `turn_limit` del mapa.
3. En cada turno, `choose_turn_transition`
   (`backend/core/game_policy.py:43`) elige una transición legal usando el
   algoritmo y la heurística indicados.
4. `apply_action` (`backend/core/game.py:29`) aplica la transición y devuelve el
   `ResultadoTurno` con su historial de pasos (`pasos`).
5. El turno se agrega al `historial` y se recalcula el estado terminal.
6. Se detectan bucles comparando el estado completo con los visitados.

Respuesta (`ResultadoSimulacion`, `backend/models/results.py:89`): `algoritmo`,
`heuristica`, `limite_turnos`, `turnos_ejecutados`, `estado_final`,
`motivo_final` e `historial`. El `motivo_final` explica un empate por límite o
por bucle; es `null` cuando la partida termina por victoria o bloqueo.

## 8. Cómo ejecutar las pruebas

### Backend

```powershell
python -m unittest discover -s backend/tests
```

La suite valida escenarios, algoritmos, verificación de rutas, adversarios,
documentación e informes (107 pruebas).

### Frontend

```powershell
cd frontend
npx tsc --noEmit
npx eslint --max-warnings=0 .
npx oxlint .
npx vite build
```

### Generadores de reportes

```powershell
python -m backend.scripts.generar_informe_casos
```

Escribe `examples/reportes/informe_casos_1_10.json`.

## 9. Uso de IA

El proyecto se desarrolló con asistencia de IA para tareas de refactorización,
redacción de pruebas y documentación. En todos los casos el resultado se revisó
y validó:

- El código generado se leyó antes de integrarlo y se ajustó al contrato del
  proyecto.
- Los algoritmos no contienen posiciones ni dimensiones codificadas; un test lo
  verifica escaneando `backend/algorithms/*.py`
  (`backend/tests/test_external_scenario.py`).
- Los resultados numéricos se reproducen con los scripts y las pruebas, no se
  transcriben a mano.
- Los métodos relevantes llevan docstrings con `Purpose`, `Preconditions`,
  `Postconditions`, `Complexity`, `AI usage`, `AI intervention` y
  `Student validation`.

## 10. Trazabilidad documentación → código

| Documento | Sección | Código |
| --- | --- | --- |
| Documento técnico | Endpoints | `backend/main.py` |
| Documento técnico | Contrato JSON | `backend/models/scenario.py:49` |
| Documento técnico | Sucesores y reglas | `backend/core/successors.py:33` |
| Documento técnico | Estados terminales | `backend/core/game.py:117` |
| Documento técnico | Simulación de partida | `backend/core/game_simulation.py:122` |
| Heurísticas y utilidad | Heurísticas A* | `backend/algorithms/heuristics.py` |
| Heurísticas y utilidad | Utilidad | `backend/core/utility.py:16` |
