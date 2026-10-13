import json
from typing import Literal

from fastapi import FastAPI
from fastapi import File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from backend.algorithms import bfs, dfs
from backend.models import Escenario, ResultadoBusqueda


app = FastAPI(
    title="TacticalGrid API",
    description="API para experimentar con algoritmos de inteligencia artificial sobre un tablero 2D.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get(
    "/api/health",
    tags=["Health"],
    summary="Comprobar disponibilidad de la API",
    description="Devuelve el estado actual del servicio backend.",
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/scenario/validate",
    tags=["Scenario"],
    summary="Validar un escenario JSON",
    description="Valida la estructura y las reglas del escenario sin aplicarlo al estado actual.",
)
async def validate_scenario(file: UploadFile = File(...)) -> dict[str, bool | str]:
    await _load_scenario(file)
    return {"valido": True, "mensaje": "El escenario es válido."}


@app.post(
    "/api/search/run",
    tags=["Search"],
    summary="Ejecutar una búsqueda sobre un escenario",
    description="Valida el escenario y ejecuta BFS o DFS usando su configuración de prueba.",
    response_model=ResultadoBusqueda,
)
async def run_search(
    file: UploadFile = File(...),
    algoritmo: Literal["BFS", "DFS"] = Form(...),
) -> ResultadoBusqueda:
    scenario = await _load_scenario(file)

    try:
        if algoritmo == "BFS":
            return bfs(scenario)
        return dfs(scenario)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo ejecutar la búsqueda: {error}",
        ) from error


async def _load_scenario(file: UploadFile) -> Escenario:
    if file.filename is None or not file.filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe tener extensión .json",
        )

    try:
        payload = json.loads(await file.read())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo no contiene un JSON válido: {error.msg if hasattr(error, 'msg') else str(error)}",
        ) from error

    try:
        return Escenario.model_validate(payload)
    except ValidationError as error:
        messages = "; ".join(
            f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}"
            for issue in error.errors()
        )
        raise HTTPException(
            status_code=400,
            detail=f"El escenario fue rechazado: {messages}",
        ) from error
