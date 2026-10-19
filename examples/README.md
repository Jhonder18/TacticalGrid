# Escenarios de prueba

Estos archivos sirven para demostrar la validación de escenarios desde la
interfaz o con la API `POST /api/scenario/validate`.

## Escenarios válidos

Los archivos de `good/` deben ser aceptados con HTTP 200:

- `escenario_busqueda.json`: prueba de navegación con A*.
- `escenario_partida.json`: estado inicial para una partida automática. El
  backend decide la unidad y el movimiento de ambos bandos y expone la
  secuencia completa mediante `POST /api/game/simulate`; la interfaz solo
  recorre el historial.
- `escenario_robo_bandera.json`: B comienza cerca de A1, que ya porta el
  recurso. Permite observar el robo automático por adyacencia y los dos
  movimientos extra de escape del ladrón.
- `escenario_bandera_bloqueada.json`: A1 recoge el recurso y B1 ocupa la
  única salida del corredor. Después del movimiento de B, el backend detecta
  que el portador no tiene camino legal a su base y devuelve el recurso a su
  posición original.
- `escenario_adversarial.json`: estado preparado para Minimax y alfa-beta.
- `escenario_volcanico.json`: mapa de ceniza, lava y cráteres.
- `escenario_acuatico.json`: mapa de agua, orillas, puentes y rocas.
- `escenario_desertico.json`: mapa de arena, dunas, oasis y acantilados.
- `escenario_beam_trampa.json`: Beam Search con una ruta aparentemente
  prometedora que puede ser podada con `k=1`.
- `escenario_costos_contraste.json`: compara una ruta corta y costosa con una
  ruta más larga y económica para BFS frente a UCS.
- `escenario_obstaculos_heuristica.json`: obstáculos y costos variados para
  comparar DFS, UCS y las heurísticas de A*.
- `caso_1_bfs_dfs.json`: Caso 1, diseñado para observar diferencias de
  exploración entre BFS y DFS.
- `caso_2_bfs_ucs.json`: Caso 2, ruta corta de BFS frente a ruta económica de
  UCS.
- `caso_3_obstaculo_astar.json`: Caso 3, obstáculo grande que obliga a A* a
  desviarse.
- `caso_4_heuristicas.json`: Caso 4, escenario estándar para comparar
  Manhattan y Euclidiana.
- `caso_5_beam.json`: Caso 5, Beam Search falla con `k=1` y encuentra ruta
  con `k=4`.
- `caso_6_portador_a.json` y `caso_6_portador_b.json`: Caso 6, mismo mapa con
  estados compuestos diferentes según el bando que porta el recurso.
- `caso_7_intercepcion.json`: Caso 7, el movimiento recomendado bloquea la
  aproximación del rival en lugar de dirigirse directamente al recurso.
- `caso_8_poda.json`: Caso 8, Minimax y Alfa-Beta devuelven la misma decisión,
  mientras Alfa-Beta genera menos nodos.
- `caso_9_orden_poda.json`: Caso 9, un orden de sucesores favorable conserva
  la decisión y reduce los nodos generados por Alfa-Beta.
- `caso_10_profundidades.json`: Caso 10, escenario para ejecutar con
  profundidad 2, 3 y 5 y comparar la carga del árbol.

Los casos adversariales se pueden cargar desde los botones rápidos de la
interfaz. El Caso 6 tiene una segunda variante (`caso_6_portador_b.json`) para
comparar explícitamente el portador contrario. En el Caso 10 se cambia la
profundidad desde el selector antes de pulsar `Evaluar turno`.

Los diez casos demostrativos propios usan mapas de 20 x 20 y al menos tres
unidades por bando, de acuerdo con las reglas mínimas del proyecto. En el Caso
7, `B1` ya transporta el recurso y `A1` actúa como interceptor: Minimax debe
acercar `A1` al portador para bloquear su avance, en lugar de perseguir un
recurso que ya no está en la zona neutral.

`orden_sucesores` es una extensión propia del equipo. El documento permite
agregar campos adicionales al JSON siempre que no cambien el significado de
los campos obligatorios. Si se omite, se conserva el orden predeterminado
`ARRIBA`, `DERECHA`, `ABAJO`, `IZQUIERDA`.

## Escenarios inválidos

Los archivos de `bad/` deben ser rechazados con HTTP 400. El nombre indica la
regla que se está demostrando:

- `dimensiones_inconsistentes.json`
- `terreno_desconocido.json`
- `posicion_fuera_del_mapa.json`
- `unidad_sobre_obstaculo.json`
- `base_sobre_obstaculo.json`
- `recurso_sobre_obstaculo.json`
- `portador_desincronizado.json`

Los ejemplos originales usan un mapa de 20 x 20. Los ejemplos temáticos
adicionales usan mapas de 10 x 10 para mostrar que la matriz y los terrenos
pueden variar mientras respeten el contrato y la validación.
