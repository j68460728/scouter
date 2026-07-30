from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    db: str
    engine_version: Optional[str] = None


class TeamSummary(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None


class CompetitionSummary(BaseModel):
    code: str
    name: str
    country: Optional[str] = None


class SeasonSummary(BaseModel):
    name: str
    year_start: int
    year_end: int


class StandingRow(BaseModel):
    team_id: int
    team_name: str
    position: int
    played: int
    points: int
    goal_difference: int
    ppg: float


class StrengthDetail(BaseModel):
    total: float
    structural: float
    context: float


class MatchEvaluation(BaseModel):
    engine_version: str
    evaluated_at: str
    strength_home: StrengthDetail
    strength_away: StrengthDetail
    difference: float
    favorite_team_id: int
    favorite_team_name: str
    selected: bool
    correct: Optional[bool] = None
    actual_winner_name: Optional[str] = None


class MatchDetail(BaseModel):
    id: int
    competition_code: str
    season_name: str
    matchday: Optional[int] = None
    stage: Optional[str] = None
    status: str
    utc_date: str
    home_team: TeamSummary
    away_team: TeamSummary
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    winner: Optional[str] = None
    evaluation: Optional[MatchEvaluation] = None


class MatchSummary(BaseModel):
    id: int
    competition_code: str
    utc_date: str
    status: str
    home_team_name: str
    away_team_name: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    difference: Optional[float] = None
    favorite_team_name: Optional[str] = None
    selected: Optional[bool] = None


class TeamHistoryRow(BaseModel):
    season_name: str
    competition_code: str
    position: Optional[int] = None
    played: Optional[int] = None
    points: Optional[int] = None
    goal_difference: Optional[int] = None
    ppg: Optional[float] = None


class TeamDetail(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    history: list[TeamHistoryRow] = []


class EngineVersionInfo(BaseModel):
    id: int
    version: str
    config_hash: str
    structural_weight: float
    context_weight: float
    min_difference: int
    description: Optional[str] = None
    created_at: str


class BenchmarkRow(BaseModel):
    match_id: int
    competition_code: str
    utc_date: str
    home_team_name: str
    away_team_name: str
    favorite_team_name: str
    difference: float
    selected: bool
    actual_winner_name: Optional[str] = None
    correct: Optional[bool] = None


class SyncResponse(BaseModel):
    status: str
    leagues: dict[str, dict[str, int]]


class EvaluateResponse(BaseModel):
    status: str
    evaluated: int


class EngineStatus(BaseModel):
    version: Optional[str] = None
    structural_weight: Optional[float] = None
    context_weight: Optional[float] = None
    min_difference: Optional[int] = None


class DataStatus(BaseModel):
    last_sync: Optional[str] = None
    matches: int
    teams: int
    competitions: int
    pending_matches: int
    current_season: Optional[str] = None


class SystemStatusResponse(BaseModel):
    engine: Optional[EngineStatus] = None
    data: DataStatus
    status: str


class BenchmarkRange(BaseModel):
    range: str
    matches: int
    correct: int
    accuracy: float


class BenchmarkBreakdown(BaseModel):
    competition_code: str
    matches: int
    correct: int
    accuracy: float


class BenchmarkSeason(BaseModel):
    season_name: str
    matches: int
    correct: int
    accuracy: float


class BenchmarkTotals(BaseModel):
    evaluated: int
    selected: int
    coverage: float
    correct: int
    accuracy: float
    baseline_home: float
    vs_baseline: float


class BenchmarkResponse(BaseModel):
    totals: BenchmarkTotals
    by_difference_range: list[BenchmarkRange]
    by_competition: list[BenchmarkBreakdown]
    by_season: list[BenchmarkSeason]
