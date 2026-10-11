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

La API estará disponible en `http://localhost:8000` y su comprobación de salud
en `http://localhost:8000/api/health`.

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
