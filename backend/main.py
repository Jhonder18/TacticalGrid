from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET"],
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
