from datetime import datetime, timezone

from fastapi import APIRouter, Depends, BackgroundTasks

from data.store import ScouterDB
from data.evaluator import EvaluationRunner
from data.ingestion import sync_all
from api.dependencies import get_db
from api.schemas import SyncResponse, EvaluateResponse

router = APIRouter(prefix="/api", tags=["operations"])

def run_sync_background(db_path: str):
    try:
        sync_all(db_path=db_path)
        db = ScouterDB(db_path)
        db.set_metadata("last_sync", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        db.close()
    except Exception as e:
        print(f"Error en sync background: {e}")

@router.post("/sync", response_model=SyncResponse)
def sync(background_tasks: BackgroundTasks, db: ScouterDB = Depends(get_db)):
    background_tasks.add_task(run_sync_background, db._db_path)
    return SyncResponse(
        status="ok",
        leagues={},
    )


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(db: ScouterDB = Depends(get_db)):
    runner = EvaluationRunner(db)
    n = runner.evaluate_all_pending()
    return EvaluateResponse(status="ok", evaluated=n)
