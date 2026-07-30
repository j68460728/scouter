from fastapi import APIRouter, Depends, Query
from typing import Optional

from data.store import ScouterDB
from api.dependencies import get_db
from api.schemas import MatchSummary, MatchDetail, TeamSummary, MatchEvaluation, StrengthDetail

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=list[MatchSummary])
def list_matches(
    competition_code: Optional[str] = Query(None),
    season_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    selected: Optional[bool] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: ScouterDB = Depends(get_db),
):
    rows = db.get_matches(
        competition_code=competition_code,
        season_name=season_name,
        status=status,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )
    if selected is not None:
        ev_ids = {
            r["match_id"]
            for r in db.get_evaluations(selected_only=selected)
        }
        rows = [r for r in rows if r["id"] in ev_ids]

    result = []
    for r in rows:
        evs = db.get_evaluations(match_id=r["id"])
        ev = evs[0] if evs else None
        result.append(MatchSummary(
            id=r["id"],
            competition_code=r.get("competition_code", ""),
            utc_date=r["utc_date"],
            status=r["status"],
            home_team_name=r["home_team_name"],
            away_team_name=r["away_team_name"],
            home_score=r.get("home_score"),
            away_score=r.get("away_score"),
            difference=ev["difference"] if ev else None,
            favorite_team_name=ev["favorite_team_name"] if ev else None,
            selected=ev["selected"] if ev else None,
        ))
    return result


@router.get("/{match_id}", response_model=MatchDetail)
def get_match(match_id: int, db: ScouterDB = Depends(get_db)):
    m = db.get_match(match_id)
    if not m:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Match not found")

    evs = db.get_evaluations(match_id=match_id)
    ev = evs[0] if evs else None

    evaluation = None
    if ev:
        evaluation = MatchEvaluation(
            engine_version=ev["engine_version"],
            evaluated_at=ev["evaluated_at"],
            strength_home=StrengthDetail(
                total=ev["strength_home_total"],
                structural=ev["strength_home_structural"],
                context=ev["strength_home_context"],
            ),
            strength_away=StrengthDetail(
                total=ev["strength_away_total"],
                structural=ev["strength_away_structural"],
                context=ev["strength_away_context"],
            ),
            difference=ev["difference"],
            favorite_team_id=ev["favorite_team_id"],
            favorite_team_name=ev["favorite_team_name"],
            selected=bool(ev["selected"]),
            correct=ev["correct"],
            actual_winner_name=ev.get("actual_winner_name"),
        )

    return MatchDetail(
        id=m["id"],
        competition_code=m.get("competition_code", ""),
        season_name=m.get("season_name", ""),
        matchday=m.get("matchday"),
        stage=m.get("stage"),
        status=m["status"],
        utc_date=m["utc_date"],
        home_team=TeamSummary(id=m["home_team_id"], name=m["home_team_name"]),
        away_team=TeamSummary(id=m["away_team_id"], name=m["away_team_name"]),
        home_score=m.get("home_score"),
        away_score=m.get("away_score"),
        winner=m.get("winner"),
        evaluation=evaluation,
    )
