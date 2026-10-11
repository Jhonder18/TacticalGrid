from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="TacticalGrid API",
    description="API para experimentar con algoritmos de inteligencia artificial sobre un tablero 2D.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
