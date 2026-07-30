from fastapi import APIRouter, Depends

from data.store import ScouterDB
from api.dependencies import get_db
from api.schemas import CompetitionSummary, SeasonSummary

router = APIRouter(prefix="/api", tags=["competitions"])


@router.get("/competitions", response_model=list[CompetitionSummary])
def list_competitions(db: ScouterDB = Depends(get_db)):
    rows = db.conn.execute(
        "SELECT code, name, country FROM competitions ORDER BY code"
    ).fetchall()
    return [CompetitionSummary(**dict(r)) for r in rows]


@router.get("/seasons", response_model=list[SeasonSummary])
def list_seasons(db: ScouterDB = Depends(get_db)):
    rows = db.conn.execute(
        "SELECT name, year_start, year_end FROM seasons ORDER BY year_start"
    ).fetchall()
    return [SeasonSummary(**dict(r)) for r in rows]
