from fastapi import APIRouter, Depends, Query
from typing import Optional

from data.store import ScouterDB
from api.dependencies import get_db
from api.schemas import SystemStatusResponse, BenchmarkResponse

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status", response_model=SystemStatusResponse)
def system_status(db: ScouterDB = Depends(get_db)):
    return db.get_system_status()


@router.get("/benchmark", response_model=BenchmarkResponse)
def benchmark(
    competition_code: Optional[str] = Query(None),
    season_name: Optional[str] = Query(None),
    engine_version: Optional[str] = Query(None),
    db: ScouterDB = Depends(get_db),
):
    return db.get_benchmark(
        competition_code=competition_code,
        season_name=season_name,
        engine_version=engine_version,
    )
