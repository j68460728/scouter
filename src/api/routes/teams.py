from fastapi import APIRouter, Depends, HTTPException

from data.store import ScouterDB
from api.dependencies import get_db
from api.schemas import TeamDetail, TeamHistoryRow

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("/{team_id}", response_model=TeamDetail)
def get_team(team_id: int, db: ScouterDB = Depends(get_db)):
    t = db.get_team(team_id)
    if not t:
        raise HTTPException(status_code=404, detail="Team not found")
    history_rows = db.get_team_history(team_id)
    return TeamDetail(
        id=t["id"],
        name=t["name"],
        short_name=t.get("short_name"),
        history=[TeamHistoryRow(**h) for h in history_rows],
    )


@router.get("/{team_id}/history", response_model=list[TeamHistoryRow])
def get_team_history(team_id: int, db: ScouterDB = Depends(get_db)):
    t = db.get_team(team_id)
    if not t:
        raise HTTPException(status_code=404, detail="Team not found")
    return [TeamHistoryRow(**h) for h in db.get_team_history(team_id)]
