from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from data.store import ScouterDB
from data.evaluator import EvaluationRunner
from data.ingestion import sync_all as do_sync
from api.dependencies import get_db
from api.schemas import HealthResponse

from api.routes import matches, teams, competitions, engine, operations, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Scouter Engine API",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(matches.router)
app.include_router(teams.router)
app.include_router(competitions.router)
app.include_router(engine.router)
app.include_router(operations.router)
app.include_router(system.router)


@app.get("/api/health", response_model=HealthResponse)
def health(db: ScouterDB = Depends(get_db)):
    ev = db.conn.execute(
        "SELECT version FROM engine_versions ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return HealthResponse(
        status="ok",
        db="connected",
        engine_version=ev["version"] if ev else None,
    )
