# Informe de resultados: Casos 1 a 10

Documento de sustentación con las tablas de **resultados esperados** y
**resultados obtenidos** para cada caso reproducible del proyecto.

Los valores obtenidos se generan con:

```powershell
python -m backend.scripts.generar_informe_casos
```

y quedan en `examples/reportes/informe_casos_1_10.json`. El informe omite el
campo `tiempo` porque no es determinista; el tiempo se observa en vivo desde la
interfaz (capturas de la sección "03 / DASHBOARD DE RESULTADOS").

Todas las cifras de este documento provienen de ese informe reproducible.

---

## Caso 1: BFS frente a DFS

Escenario `caso_1_bfs_dfs.json`. Finalidad: comparar una búsqueda por amplitud
con una búsqueda por profundidad sobre el mismo mapa.

**Resultado esperado.** Ambos encuentran una ruta. BFS explora por niveles y
halla una ruta con el menor número de movimientos, pero genera muchos estados.
DFS baja por una rama y puede hallar una ruta más larga y más costosa, a cambio
de generar muchos menos estados.

| Algoritmo | Parámetros | Éxito | Costo | Longitud | Nodos generados | Nodos expandidos | Frontera |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BFS | — | Sí | 55 | 34 | 665 | 644 | 38 |
| DFS | — | Sí | 67 | 40 | 76 | 41 | 35 |

**Resultado obtenido.** Coincide con lo esperado: BFS logra menor longitud (34)
y menor costo (55), mientras DFS gasta menos nodos (76 frente a 665) pero
entrega una ruta más larga (40) y más costosa (67).

---

## Caso 2: BFS frente a UCS

Escenario `caso_2_bfs_ucs.json`. Finalidad: mostrar que el camino más corto en
movimientos no siempre es el más barato.

**Resultado esperado.** BFS minimiza el número de movimientos, pero puede
atravesar casillas caras. UCS prioriza el costo acumulado y encuentra una ruta
de menor costo aunque tenga más movimientos.

| Algoritmo | Parámetros | Éxito | Costo | Longitud | Nodos generados | Nodos expandidos | Frontera |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BFS | — | Sí | 46 | 6 | 34 | 23 | 11 |
| UCS | — | Sí | 8 | 8 | 65 | 42 | 23 |

**Resultado obtenido.** Coincide: BFS logra la ruta más corta (6 movimientos) a
costo 46, mientras UCS acepta 8 movimientos para bajar el costo a 8. UCS genera
más nodos (65) porque explora según costo.

---

## Caso 3: desvío por obstáculos con A*

Escenario `caso_3_obstaculo_astar.json`. Finalidad: comprobar que la ruta rodea
los muros en lugar de atravesarlos.

**Resultado esperado.** A* con Manhattan encuentra una ruta válida, cuyo camino
no incluye ninguna casilla no transitable y termina en el objetivo.

| Algoritmo | Parámetros | Éxito | Costo | Longitud | Nodos generados | Nodos expandidos | Frontera |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A* | h: MANHATTAN | Sí | 14 | 14 | 35 | 22 | 13 |

**Resultado obtenido.** Coincide: A* llega al objetivo con costo 14 en 14
movimientos, rodeando los obstáculos. La ruta puede revisarse en
`examples/reportes/informe_casos_1_10.json` (campo `camino`).

---

## Caso 4: Manhattan frente a Euclídea (propia)

Escenario `caso_4_heuristicas.json`. Finalidad: comparar las dos heurísticas de
A* sobre el mismo mapa.

**Resultado esperado.** Ambas heurísticas son admisibles, por lo que A* entrega
la **misma ruta y el mismo costo** con las dos. La diferencia aparece en el
**orden de exploración**, reflejado en los nodos generados/expandidos; pueden
coincidir o diferir según el mapa.

| Algoritmo | Parámetros | Éxito | Costo | Longitud | Nodos generados | Nodos expandidos | Frontera |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A* | h: MANHATTAN | Sí | 55 | 34 | 606 | 531 | 65 |
| A* | h: Euclídea (propia) | Sí | 55 | 34 | 621 | 563 | 60 |

**Resultado obtenido.** Coincide: mismo costo (55) y misma longitud (34). La
heurística Euclídea explora algo más de estados (621/563) que Manhattan
(606/531), lo que demuestra que la fórmula cambia el orden de exploración aunque
la decisión final sea la misma.

> Punto clave para la sustentación: mismo camino y costo **no** significa misma
> fórmula. Una heurística cambia el orden de exploración, no está obligada a
> producir rutas distintas en todos los mapas.

---

## Caso 5: Beam Search con k = 1, 2, 4 y 8

Escenario `caso_5_beam.json`. Finalidad: medir el efecto del ancho de memoria.

**Resultado esperado.** Con `k` pequeño la búsqueda es barata pero puede perder
la solución; al aumentar `k` explora más estados, con mayor probabilidad de
encontrar la ruta y también mayor costo computacional.

| Parámetros | Éxito | Costo | Longitud | Nodos generados | Nodos expandidos | Frontera |
| --- | --- | --- | --- | --- | --- | --- |
| k: 1 | No | 0 | 0 | 7 | 6 | 1 |
| k: 2 | Sí | 10 | 10 | 30 | 19 | 2 |
| k: 4 | Sí | 10 | 10 | 47 | 34 | 4 |
| k: 8 | Sí | 10 | 10 | 79 | 57 | 8 |

**Resultado obtenido.** Coincide: con `k = 1` Beam Search falla (frontera de
tamaño 1, no encuentra la ruta). Con `k >= 2` encuentra la solución de costo 10,
y los nodos generados crecen con `k` (30, 47, 79).

---

## Caso 6: diferencia de portador

Escenarios `caso_6_portador_a.json` (A1 lleva el recurso) y
`caso_6_portador_b.json` (B1 lo lleva). Mismo mapa, distinto portador: **es un
estado distinto**.

**Resultado esperado.** Ambos bandos consideran el estado del portador, por lo
que la decisión táctica puede diferir según quién transporte el recurso. Minimax
y Alfa-Beta deben coincidir en acción y valor.

| Escenario | Prof. | Misma acción | Mismo valor | Nodos Minimax | Nodos Alfa-Beta | Reducción |
| --- | --- | --- | --- | --- | --- | --- |
| Portador A (A1) | 3 | Sí | Sí | 399 | 88 | 77.94% |
| Portador B (B1) | 3 | Sí | Sí | 513 | 164 | 68.03% |

**Resultado obtenido.** Coincide. Con A1 portando, la acción óptima es
`A2 (9,10)→(9,11)` (valor 0.22). Con B1 portando, la acción óptima es
`A2 (9,10)→(8,10)` (valor 0.2472): cambia la decisión y la carga de nodos, lo que
evidencia que el portador forma parte del estado.

---

## Caso 7: intercepción del portador

Escenario `caso_7_intercepcion.json`. Finalidad: comprobar que el bando A
intercepta al portador rival en lugar de perseguir el recurso suelto.

**Resultado esperado.** A1 reduce su distancia al portador rival con el
movimiento elegido. Minimax y Alfa-Beta coinciden en acción y valor.

| Algoritmo | Prof. | Acción | Valor | Nodos generados | Nodos podados |
| --- | --- | --- | --- | --- | --- |
| Minimax | 3 | A1 (10,10)→(10,11) | -0.2267 | 1150 | 0 |
| Alfa-Beta | 3 | A1 (10,10)→(10,11) | -0.2267 | 202 | 184 |

**Resultado obtenido.** Coincide: la acción `A1 (10,10)→(10,11)` acerca a A1 al
portador rival. Alfa-Beta obtiene el mismo resultado podando el 82.43% de los
nodos.

---

## Caso 8: Minimax frente a Alfa-Beta

Escenario `caso_8_poda.json`. Finalidad: demostrar la poda.

**Resultado esperado.** Igual acción e igual valor que Minimax, pero Alfa-Beta
genera muchos menos nodos al podar ramas.

| Algoritmo | Prof. | Acción | Valor | Nodos generados | Nodos evaluados | Nodos podados |
| --- | --- | --- | --- | --- | --- | --- |
| Minimax | 4 | A1 (9,9)→(9,10) | 0.2976 | 9247 | 8284 | 0 |
| Alfa-Beta | 4 | A1 (9,9)→(9,10) | 0.2976 | 697 | 489 | 1409 |

**Resultado obtenido.** Coincide: misma acción (`A1 (9,9)→(9,10)`) y mismo valor
(0.2976). Alfa-Beta reduce los nodos un **92.46%** (de 9247 a 697).

---

## Caso 9: efecto del orden de sucesores

Escenario `caso_9_orden_poda.json` (define `orden_sucesores`). Finalidad:
comprobar que un buen orden de expansión aumenta la poda sin cambiar la
decisión.

**Resultado esperado.** El orden alterado no cambia la acción ni el valor, pero
permite a Alfa-Beta podar más y generar menos nodos.

| Variante | Acción | Valor | Nodos Alfa-Beta | Nodos podados |
| --- | --- | --- | --- | --- |
| Orden propio (`orden_sucesores`) | A1 (9,9)→(9,10) | 0.299 | 174 | 126 |
| Orden por defecto | A1 (9,9)→(9,10) | 0.299 | 174 | 126 |

**Resultado obtenido.** Coincide en acción y valor. `orden_sucesores` es una
**extensión propia del JSON** (no exigida por el enunciado): permite reproducir
la poda óptima colocando primero los mejores movimientos.

---

## Caso 10: carga de profundidades 2, 3 y 5

Escenario `caso_10_profundidades.json`. Finalidad: medir cómo crece la carga con
la profundidad en ambos algoritmos.

**Resultado esperado.** A mayor profundidad, más nodos generados en los dos
algoritmos. Alfa-Beta crece mucho más despacio gracias a la poda, manteniendo la
misma decisión.

| Prof. | Algoritmo | Nodos generados | Nodos evaluados | Nodos podados | Reducción Alfa-Beta |
| --- | --- | --- | --- | --- | --- |
| 2 | Minimax | 91 | 80 | 0 | — |
| 2 | Alfa-Beta | 37 | 26 | 54 | 59.34% |
| 3 | Minimax | 963 | 872 | 0 | — |
| 3 | Alfa-Beta | 208 | 171 | 152 | 78.40% |
| 5 | Minimax | 99003 | 89756 | 0 | — |
| 5 | Alfa-Beta | 3561 | 2828 | 3967 | 96.40% |

**Resultado obtenido.** Coincide: Minimax pasa de 91 a 99003 nodos entre
profundidad 2 y 5, mientras Alfa-Beta pasa de 37 a 3561. La acción y el valor se
mantienen (`A1 (9,9)→(9,10)`) y el ahorro de Alfa-Beta crece con la profundidad.

---

## Simulación automática de partidas y estados terminales

**Resultado esperado.** Las partidas terminan en un estado terminal descrito por
el backend: `victoria_A`, `victoria_B`, `bloqueado` o `empate`. El bando que
lleva el recurso a su propia base gana; si se repite el estado completo (bucle)
o se agota el límite de turnos, la partida queda en `empate`.

| Escenario | Algoritmo | Estado final | Turnos | Motivo |
| --- | --- | --- | --- | --- |
| `escenario_partida` | BFS | victoria_A | 53 | — |
| `escenario_robo_bandera` | BFS | victoria_A | 10 | — |
| `escenario_bandera_bloqueada` | BFS | empate | 12 | Bucle: se repitió el estado completo. |

**Resultado obtenido.**

- **Partida estándar**: gana el bando A (victoria_A) tras 53 turnos.
- **Robo de bandera**: el bando B ya carga el recurso al inicio; A lo intercepta
  y gana en 10 turnos (victoria_A).
- **Bandera bloqueada**: las defensas impiden que el portador progrese de forma
  útil y la partida entra en `empate` por repetición de estado a los 12 turnos.

---

## Cómo reproducir las capturas

1. Arranca backend y frontend (ver `README.md`).
2. Carga cada caso con los **botones rápidos** (Casos 1 a 10).
3. Ejecuta la búsqueda o la evaluación adversarial y captura la sección
   "03 / DASHBOARD DE RESULTADOS" (método, parámetros, éxito, camino, costo,
   nodos y tiempo) o el árbol adversarial.
4. Para las partidas, carga `escenario_partida`, `escenario_robo_bandera` o
   `escenario_bandera_bloqueada` y usa "Calcular partida completa".
5. Para evidencia automatizada, usa el botón **"Descargar informe JSON"** o el
   script `python -m backend.scripts.generar_informe_casos`.

El tiempo (`tiempo`) se observa en las capturas en vivo; el JSON reproducible lo
omite por no ser determinista.
