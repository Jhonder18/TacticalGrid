import json
from typing import Literal

from fastapi import FastAPI
from fastapi import File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from backend.algorithms import alpha_beta, a_star, beam_search, bfs, dfs, minimax, ucs
from backend.core.game import apply_action, get_game_status
from backend.core.game_policy import choose_turn_transition
from backend.models import (
    Accion,
    Escenario,
    GameState,
    ResultadoAdversarial,
    ResultadoBusqueda,
    ResultadoTurno,
    ResultadoSimulacion,
    EstadoPartidaResponse,
    PasoTurno,
    UnidadEstadoResponse,
)


def _turn_limit(scenario: Escenario) -> int:
    return min(500, max(50, 4 * scenario.mapa.filas * scenario.mapa.columnas))


def _turn_result(result, algoritmo: str, heuristica: str) -> ResultadoTurno:
    def state_response(state: GameState) -> EstadoPartidaResponse:
        return EstadoPartidaResponse(
            unidades=[
                UnidadEstadoResponse(
                    id=unit.id,
                    bando=unit.bando,
                    posicion={"fila": unit.posicion[0], "columna": unit.posicion[1]},
                )
                for unit in state.unidades
            ],
            portador_recurso=state.portador_recurso,
            posicion_recurso=(
                None if state.posicion_recurso is None
                else {
                    "fila": state.posicion_recurso[0],
                    "columna": state.posicion_recurso[1],
                }
            ),
            turno=state.turno,
        )

    return ResultadoTurno(
        algoritmo=algoritmo,
        heuristica=heuristica,
        estado=state_response(result.estado),
        accion=result.accion,
        costo=result.costo,
        estado_partida=result.estado_partida,
        turno_siguiente=result.turno_siguiente,
        pasos=[
            PasoTurno(
                accion=step.action,
                estado=state_response(step.state),
                costo=step.cost,
            )
            for step in result.pasos
        ],
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

    return _turn_result(result, algoritmo, heuristica)


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
        state = GameState.from_scenario(scenario)
        limit = _turn_limit(scenario)
        history = []
        status = get_game_status(state, scenario)
        visited_states = {state}
        final_reason = None
        for _ in range(limit):
            if status != "en curso":
                break
            transition = choose_turn_transition(state, scenario, algoritmo, heuristica, k)
            result = apply_action(state, scenario, transition.action)
            history.append(_turn_result(result, algoritmo, heuristica))
            state = result.estado
            status = result.estado_partida
            if status == "en curso" and state in visited_states:
                status = "empate"
                final_reason = (
                    "Se detectó un bucle: el estado completo de la partida "
                    "se repitió, por lo que la partida queda en empate."
                )
                break
            visited_states.add(state)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo simular la partida: {error}",
        ) from error

    if status == "en curso" and len(history) >= limit:
        status = "empate"
        final_reason = (
            "La partida alcanzó el límite máximo de turnos sin un ganador, "
            "por lo que queda en empate."
        )

    return ResultadoSimulacion(
        algoritmo=algoritmo,
        heuristica=heuristica,
        limite_turnos=limit,
        turnos_ejecutados=len(history),
        estado_final=status,
        motivo_final=final_reason,
        historial=history,
    )


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
