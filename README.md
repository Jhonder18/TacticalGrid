# TacticalGrid

Plataforma académica para ejecutar, observar y medir algoritmos de inteligencia
artificial sobre un tablero cuadriculado 2D. Permite cargar escenarios JSON
externos, ejecutar búsquedas (BFS, DFS, UCS, A*, Beam Search), tomar decisiones
adversariales (Minimax y Alfa-Beta) y simular partidas automáticas.

## Integrantes

- Carlos Gómez ([Cgomez2107](https://github.com/Cgomez2107)) — planificación y desarrollo.
- Jhon Hander Patiño Londoño ([Jhonder18](https://github.com/Jhonder18)) — planificación y desarrollo.

## Requisitos

- Node.js 18+
- Python 3.10+

## Puesta en marcha

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Vite estará disponible en `http://localhost:5173`.

### Backend

En PowerShell, desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

La API estará disponible en `http://localhost:8000`. FastAPI incluye
documentación interactiva:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Especificación OpenAPI: `http://localhost:8000/openapi.json`

La comprobación de salud está disponible en `http://localhost:8000/api/health`.

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/api/health` | Estado del servicio |
| POST | `/api/scenario/validate` | Validar un escenario JSON |
| POST | `/api/search/run` | Ejecutar BFS, DFS, UCS, A* o Beam Search |
| POST | `/api/adversarial/run` | Ejecutar Minimax o Alfa-Beta |
| POST | `/api/adversarial/compare` | Comparar Minimax y Alfa-Beta |
| POST | `/api/report/full` | Informe consolidado de los Casos 1 a 10 |
| POST | `/api/game/turn` | Aplicar un turno de partida |
| POST | `/api/game/simulate` | Simular una partida completa |

Los endpoints reciben el archivo en el campo multipart `file`. El detalle de
parámetros, respuestas y errores está en
[docs/documento_tecnico.md](docs/documento_tecnico.md).

## Escenarios

Los escenarios de demostración están en [examples/](<./examples/>):

- `good/`: escenarios válidos (incluidos los Casos 1 a 10).
- `bad/`: escenarios inválidos, uno por regla de validación.
- `externo_*.json`: escenarios externos de búsqueda, adversarial y partida.

El contrato del formato JSON está en
[docs/documento_tecnico.md](docs/documento_tecnico.md#3-contrato-json).

## Pruebas

Backend:

```powershell
python -m unittest discover -s backend/tests
```

Frontend:

```powershell
cd frontend
npx tsc --noEmit
npx eslint --max-warnings=0 .
npx oxlint .
npx vite build
```

## Documentación

- [Documento técnico](docs/documento_tecnico.md): estructura, endpoints, contrato
  JSON, reglas, algoritmos, métricas y pruebas.
- [Manual de usuario](docs/manual_usuario.md): uso de la interfaz.
- [Heurísticas y utilidad](docs/heuristicas_y_utilidad.md): A* y función de
  utilidad.
- [Informe de resultados](docs/informe_resultados_casos.md): Casos 1 a 10.
- [Prueba manual de la interfaz](docs/prueba_manual_interfaz.md): evidencia (T-28).

## Estructura

```text
frontend/
  src/
    components/
    hooks/
    services/
    types/
backend/
  algorithms/    BFS, DFS, UCS, A*, Beam Search, Minimax, Alfa-Beta
  core/          Estado, sucesores, partida, utilidad, verificación e informes
  models/        Escenario, GameState y resultados
  scripts/       Generadores de reportes
  tests/         Suite de pruebas
docs/
examples/
```
