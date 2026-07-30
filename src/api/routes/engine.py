from fastapi import APIRouter, Depends

from data.store import ScouterDB
from api.dependencies import get_db
from api.schemas import EngineVersionInfo

router = APIRouter(prefix="/api/engine", tags=["engine"])


@router.get("", response_model=EngineVersionInfo)
def get_active_engine(db: ScouterDB = Depends(get_db)):
    row = db.conn.execute(
        "SELECT * FROM engine_versions ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No engine version registered")
    return EngineVersionInfo(**dict(row))


@router.get("/versions", response_model=list[EngineVersionInfo])
def list_engine_versions(db: ScouterDB = Depends(get_db)):
    rows = db.conn.execute(
        "SELECT * FROM engine_versions ORDER BY id"
    ).fetchall()
    return [EngineVersionInfo(**dict(r)) for r in rows]
