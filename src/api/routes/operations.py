from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from data.store import ScouterDB
from data.evaluator import EvaluationRunner
from data.ingestion import sync_all
from api.dependencies import get_db
from api.schemas import SyncResponse, EvaluateResponse

router = APIRouter(prefix="/api", tags=["operations"])


@router.post("/sync", response_model=SyncResponse)
def sync(db: ScouterDB = Depends(get_db)):
    result = sync_all(db_path=db._db_path)
    db.set_metadata("last_sync", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    db2 = ScouterDB(db._db_path)
    db2.close()
    return SyncResponse(
        status="ok",
        leagues=result,
    )


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(db: ScouterDB = Depends(get_db)):
    runner = EvaluationRunner(db)
    n = runner.evaluate_all_pending()
    return EvaluateResponse(status="ok", evaluated=n)
