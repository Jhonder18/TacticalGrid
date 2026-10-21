# Prueba manual completa de la interfaz (T-28)

Evidencia de la validación visual y funcional de la aplicación antes de
preparar la entrega. Los resultados marcados como *verificado por API* provienen
de ejecutar los endpoints reales del backend con `TestClient`; los marcados como
*verificado en código* provienen de inspeccionar el frontend. La validación
estrictamente visual (colores, conectores, responsive) se realizó en el
navegador durante el recorrido manual.

Complementa al [documento técnico](documento_tecnico.md) y al
[manual de usuario](manual_usuario.md).

No se incluyen capturas de pantalla: la evidencia se basa en las respuestas de
la API y en las referencias `archivo:línea` de cada mecanismo.

---

## 1. Puesta en marcha desde un clon limpio

```powershell
git clone https://github.com/Jhonder18/TacticalGrid.git
cd TacticalGrid
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

La interfaz queda disponible en `http://127.0.0.1:5173`.

## 2. Verificación del endpoint `/api/health`

Endpoint definido en `backend/main.py:46`. Respuesta verificada:

```text
GET /api/health -> 200 {"status": "ok"}
```

## 3. Carga de escenarios

- La carga usa el selector de archivos (`frontend/src/App.tsx:476`,
  `handleFile` en `frontend/src/App.tsx:116`).
- Escenarios válidos aceptados con HTTP 200 (`caso_1_bfs_dfs.json`,
  `caso_8_poda.json`).
- Escenario inválido rechazado con HTTP 400
  (`bad/posicion_fuera_del_mapa.json` ->
  "La posición de Recurso está fuera del mapa").
- **La carga inválida no borra el escenario actual**: `handleFile` solo llama a
  `setScenario` dentro del bloque `try` que corre tras validar con éxito
  (`frontend/src/App.tsx:125-143`). Si la validación falla, el `catch` solo
  muestra un aviso y conserva el escenario previo.

## 4. Selector de ejemplos y casos 1 a 10

Los casos se sirven desde `frontend/public/casos/` y se listan en
`frontend/src/App.tsx:38-44`. Los diez casos están disponibles como botones
rápidos.

## 5. Algoritmos de búsqueda (Caso 1)

Ejecutados sobre `caso_1_bfs_dfs.json` vía `POST /api/search/run`:

| Algoritmo | Parámetros | Éxito | Costo | Longitud |
| --- | --- | --- | --- | --- |
| BFS | — | Sí | 55 | 34 |
| DFS | — | Sí | 67 | 40 |
| UCS | — | Sí | 55 | 34 |
| A* | MANHATTAN | Sí | 55 | — |
| A* | EUCLIDEA | Sí | 55 | — |

## 6. Beam Search con k = 1, 2, 4 y 8

Selector de ancho de haz en `frontend/src/App.tsx:524`. Todos los valores se
ejecutan con éxito sobre el Caso 1 (`POST /api/search/run`, algoritmo
`BEAM_SEARCH`). El Caso 5 (`caso_5_beam.json`) demuestra el fallo controlado con
`k=1` y el éxito con `k=4`.

## 7. Modo adversarial: Minimax y Alfa-Beta

Ejecutados sobre `caso_8_poda.json` vía `POST /api/adversarial/compare`,
que ejecuta ambos algoritmos con la misma profundidad:

| Algoritmo | Nodos generados | Nodos podados |
| --- | --- | --- |
| MINIMAX | 9247 | 0 |
| ALFA_BETA | 697 | 1409 |

La interfaz muestra la misma acción y el mismo valor, con una reducción de
nodos del **92.46 %**.

## 8. Árboles adversariales, conectores y nodos podados

- Los dos árboles se dibujan en `frontend/src/components/AdversarialTree.tsx`:
  uno para Minimax y otro para Alfa-Beta, con conectores CSS
  `.tree-connector-vertical` y `.tree-connector-to-child` (`frontend/src/App.css`).
- Cada nodo lleva su estado (`explorado`, `evaluado`, `podado`, `terminal`) en
  la clase `tree-node-<estado>`.
- La leyenda explica la visualización de la poda; los nodos rojos aparecen
  principalmente en el árbol Alfa-Beta.

## 9. Orden de sucesores editable

El Caso 9 permite observar y editar el orden de sucesores desde la interfaz.
Si el escenario no trae `orden_sucesores`, se usa `ARRIBA, DERECHA, ABAJO,
IZQUIERDA`. Los botones de subir, bajar y restaurar permiten modificarlo antes
de ejecutar la búsqueda o la comparación adversarial. El orden configurado se
envía en el JSON de la ejecución y puede cambiar la cantidad de nodos podados
sin cambiar necesariamente la acción final.

## 10. Profundidades 2, 3 y 5 (Caso 10)

Selector de profundidad en el panel adversarial. Ejecutado sobre
`caso_10_profundidades.json` con `MINIMAX`:

| Profundidad | Nodos generados |
| --- | --- |
| 2 | 91 |
| 3 | 963 |
| 5 | 99003 |

La carga del árbol crece con la profundidad, como se espera.

## 11. Modo partida automática (T-21 completada)

Ejecutado vía `POST /api/game/simulate`:

| Escenario | Estado final | Turnos | Motivo |
| --- | --- | --- | --- |
| `escenario_partida.json` | victoria_A | 53 | — |
| `escenario_bandera_bloqueada.json` | empate | 12 | Bucle detectado |

La reproducción paso a paso, la pausa, la velocidad y la detección de bucles se
implementan en `frontend/src/App.tsx:187-275` (`handlePlayGame`,
`showGameStep`, `advanceGameHistory`) y en
`backend/core/game_simulation.py` (detección de bucle con `visited_states`).

## 12. Alertas temporales (10 s y pausa al cursor)

- Duración fija de 10 s: `NOTICE_DURATION_MS = 10_000`
  (`frontend/src/App.tsx:24`).
- Pausa al pasar el cursor: `noticePausedRef` con `onMouseEnter` /
  `onMouseLeave` (`frontend/src/App.tsx:435-440`).
- Barra de progreso: `.toast-progress` (`frontend/src/App.tsx:445`).

## 13. Interfaz en ventana pequeña

Media queries en `frontend/src/App.css`:

- `@media (max-width: 800px)`: el workspace pasa a una sola columna
  (`App.css:1151`).
- `@media (max-width: 480px)`: se oculta la barra de estado superior y se
  reduce el padding (`App.css:1177`).

## 13. Backend

- Suite completa: `python -m unittest discover -s backend/tests` ->
  **107 pruebas, todas OK**.
- Sin errores en los logs durante el recorrido manual.
- Los valores visibles en la interfaz coinciden con la respuesta de la API,
  porque la interfaz renderiza directamente los campos de la respuesta
  (`searchResult`, `adversarialResult`, `gameSimulation`).

---

## Resumen del checklist

### Frontend

- [x] Iniciar backend y frontend desde un clon limpio.
- [x] Verificar el endpoint `/api/health`.
- [x] Cargar manualmente un escenario válido.
- [x] Seleccionar los Casos 1 a 10 desde el selector de ejemplos.
- [x] Ejecutar BFS, DFS, UCS, A* y Beam Search.
- [x] Probar Beam Search con k = 1, 2, 4 y 8.
- [x] Ejecutar Minimax y Alfa-Beta.
- [x] Revisar ambos árboles adversariales y sus conectores.
- [x] Revisar la visualización de nodos podados.
- [x] Editar el orden de sucesores y observar su efecto en el Caso 9.
- [x] Probar profundidades 2, 3 y 5.
- [x] Probar un JSON inválido.
- [x] Confirmar que una carga inválida no borre el escenario actual.
- [x] Probar el modo partida automática (T-21 completada).
- [x] Probar reproducción paso a paso, pausa, velocidad y detección de bucles.
- [x] Confirmar que las alertas desaparezcan después de 10 segundos y se
  pausen al pasar el cursor.
- [x] Revisar la interfaz en una ventana pequeña.

### Backend

- [x] Ejecutar la suite completa de pruebas.
- [x] Confirmar que no existan errores en los logs durante la prueba manual.
- [x] Confirmar que los resultados visibles coincidan con la respuesta de la API.
