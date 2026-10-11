# TacticalGrid

Plataforma académica para ejecutar, observar y medir algoritmos de inteligencia
artificial sobre un tablero cuadriculado 2D.

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
New-Item -ItemType Directory -Force backend | Out-Null
py -3 -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

La API estará disponible en `http://localhost:8000`. FastAPI incluye documentación
interactiva automáticamente:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Especificación OpenAPI: `http://localhost:8000/openapi.json`

La comprobación de salud está disponible en `http://localhost:8000/api/health`.

Para validar un escenario JSON sin aplicarlo al estado actual, usa:

```text
POST http://localhost:8000/api/scenario/validate
```

El endpoint recibe el archivo en el campo multipart `file`, devuelve `200` para
escenarios válidos y `400` con la regla incumplida cuando el escenario es
rechazado.

Los escenarios de demostración están en [examples/](<./examples/>). Para probar
automáticamente todos los casos válidos e inválidos:

```powershell
.\backend\venv\Scripts\python.exe -m unittest discover -s backend\tests -v
```

## Estructura

```text
frontend/
  src/
    components/
    hooks/
    services/
    types/
backend/
  api/
  algorithms/
  core/
  models/
```
