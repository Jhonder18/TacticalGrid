import json
from typing import Literal

from fastapi import FastAPI
from fastapi import File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from backend.algorithms import alpha_beta, a_star, beam_search, bfs, dfs, minimax, ucs
from backend.core.adversarial_comparison import comparar_adversarial
from backend.core.game import apply_action, get_game_status
from backend.core.game_policy import choose_turn_transition
from backend.core.game_simulation import simular_partida, turn_result
from backend.core.informe import generar_informe
from backend.models import (
    Accion,
    Escenario,
    GameState,
    ResultadoAdversarial,
    ResultadoBusqueda,
    ResultadoComparacionAdversarial,
    ResultadoTurno,
    ResultadoSimulacion,
)


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
    description="Valida el escenario y ejecuta BFS, DFS, UCS, A* o Beam Search.",
    response_model=ResultadoBusqueda,
)
async def run_search(
    file: UploadFile = File(...),
    algoritmo: Literal["BFS", "DFS", "UCS", "A_ESTRELLA", "BEAM_SEARCH"] = Form(...),
    heuristica: Literal["MANHATTAN", "EUCLIDEA"] = Form("MANHATTAN"),
    k: int = Form(1, gt=0),
) -> ResultadoBusqueda:
    scenario = await _load_scenario(file)

    try:
        if algoritmo == "BFS":
            return bfs(scenario)
        if algoritmo == "DFS":
            return dfs(scenario)
        if algoritmo == "UCS":
            return ucs(scenario)
        if algoritmo == "BEAM_SEARCH":
            return beam_search(scenario, k)
        return a_star(scenario, heuristica)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo ejecutar la búsqueda: {error}",
        ) from error


@app.post(
    "/api/adversarial/run",
    tags=["Adversarial"],
    summary="Evaluar el turno actual con búsqueda adversarial",
    description="Ejecuta Minimax o Alfa-Beta sobre el estado inicial del escenario.",
    response_model=ResultadoAdversarial,
)
async def run_adversarial(
    file: UploadFile = File(...),
    algoritmo: Literal["MINIMAX", "ALFA_BETA"] = Form("ALFA_BETA"),
    profundidad: int | None = Form(None, gt=0, le=8),
) -> ResultadoAdversarial:
    scenario = await _load_scenario(file)
    if profundidad is not None:
        scenario = scenario.model_copy(
            deep=True,
            update={
                "juego": scenario.juego.model_copy(
                    update={"profundidad_maxima_minimax": profundidad}
                )
            },
        )

    try:
        if algoritmo == "MINIMAX":
            return minimax(scenario)
        return alpha_beta(scenario)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo evaluar el turno: {error}",
        ) from error


@app.post(
    "/api/adversarial/compare",
    tags=["Adversarial"],
    summary="Comparar Minimax y Alfa-Beta sobre el mismo escenario",
    description="Ejecuta ambos algoritmos con la misma profundidad y resume coincidencias y ahorro de nodos.",
    response_model=ResultadoComparacionAdversarial,
)
async def compare_adversarial(
    file: UploadFile = File(...),
    profundidad: int | None = Form(None, gt=0, le=8),
) -> ResultadoComparacionAdversarial:
    scenario = await _load_scenario(file)
    if profundidad is not None:
        scenario = scenario.model_copy(
            deep=True,
            update={
                "juego": scenario.juego.model_copy(
                    update={"profundidad_maxima_minimax": profundidad}
                )
            },
        )

    try:
        return comparar_adversarial(scenario)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo comparar los algoritmos: {error}",
        ) from error


@app.post(
    "/api/report/full",
    tags=["Report"],
    summary="Generar el informe consolidado de los Casos 1 a 10",
    description="Ejecuta todos los casos del proyecto y devuelve las tablas reproducibles para la sustentación.",
)
def run_full_report() -> dict:
    try:
        return generar_informe()
    except (ValueError, ValidationError) as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo generar el informe: {error}",
        ) from error


@app.post(
    "/api/game/turn",
    tags=["Game"],
    summary="Decidir y aplicar un turno automático",
    description="Valida un escenario, decide la acción con el algoritmo seleccionado y devuelve el estado siguiente.",
    response_model=ResultadoTurno,
)
async def run_game_turn(
    file: UploadFile = File(...),
    algoritmo: Literal["BFS", "DFS", "UCS", "A_ESTRELLA", "BEAM_SEARCH"] = Form("BFS"),
    heuristica: Literal["MANHATTAN", "EUCLIDEA"] = Form("MANHATTAN"),
    k: int = Form(4, gt=0),
) -> ResultadoTurno:
    scenario = await _load_scenario(file)
    try:
        state = GameState.from_scenario(scenario)
        status = get_game_status(state, scenario)
        if status != "en curso":
            raise ValueError(f"La partida está {status}")
        transition = choose_turn_transition(
            state,
            scenario,
            algoritmo,
            heuristica,
            k,
        )
        result = apply_action(
            state,
            scenario,
            transition.action,
        )
    except (ValueError, ValidationError) as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo decidir el turno: {error}",
        ) from error

    return turn_result(result, algoritmo, heuristica)


@app.post(
    "/api/game/simulate",
    tags=["Game"],
    summary="Simular una partida completa",
    response_model=ResultadoSimulacion,
)
async def simulate_game(
    file: UploadFile = File(...),
    algoritmo: Literal["BFS", "DFS", "UCS", "A_ESTRELLA", "BEAM_SEARCH"] = Form("BFS"),
    heuristica: Literal["MANHATTAN", "EUCLIDEA"] = Form("MANHATTAN"),
    k: int = Form(4, gt=0),
) -> ResultadoSimulacion:
    scenario = await _load_scenario(file)
    try:
        return simular_partida(scenario, algoritmo, heuristica, k)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo simular la partida: {error}",
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
