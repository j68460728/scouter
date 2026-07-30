const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:15901";

async function fetchJSON<T>(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const { timeoutMs = 15000, ...fetchInit } = init || {};
  
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...fetchInit?.headers },
      signal: controller.signal,
      ...fetchInit,
    });
    
    clearTimeout(id);
    
    if (!res.ok) {
      let msg = res.statusText;
      try {
        const data = await res.json();
        if (data.detail) msg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      } catch (e) {
        // Not JSON
      }
      throw new Error(`API Error (${res.status}): ${msg}`);
    }
    
    return await res.json();
  } catch (err: any) {
    clearTimeout(id);
    if (err.name === "AbortError") {
      throw new Error("La petición tardó demasiado y fue cancelada (Timeout).");
    }
    if (err.message === "Failed to fetch") {
      throw new Error("No se pudo conectar con el servidor (API Offline o inaccesible).");
    }
    throw err;
  }
}

// ── types matching FastAPI schemas ──────────────────────────────────

export interface EngineStatus {
  version: string | null;
  structural_weight: number | null;
  context_weight: number | null;
  min_difference: number | null;
}

export interface DataStatus {
  last_sync: string | null;
  matches: number;
  teams: number;
  competitions: number;
  pending_matches: number;
  current_season: string | null;
}

export interface SystemStatus {
  engine: EngineStatus | null;
  data: DataStatus;
  status: string;
}

export interface StrengthDetail {
  total: number;
  structural: number;
  context: number;
}

export interface MatchEvaluation {
  engine_version: string;
  evaluated_at: string;
  strength_home: StrengthDetail;
  strength_away: StrengthDetail;
  difference: number;
  favorite_team_id: number;
  favorite_team_name: string;
  selected: boolean;
  correct: boolean | null;
  actual_winner_name: string | null;
}

export interface TeamSummary {
  id: number;
  name: string;
  short_name?: string;
}

export interface MatchSummary {
  id: number;
  competition_code: string;
  utc_date: string;
  status: string;
  home_team_name: string;
  away_team_name: string;
  home_team_id?: number;
  away_team_id?: number;
  home_score?: number;
  away_score?: number;
  difference?: number;
  favorite_team_name?: string;
  selected?: boolean;
}

export interface MatchDetail {
  id: number;
  competition_code: string;
  season_name: string;
  matchday?: number;
  stage?: string;
  status: string;
  utc_date: string;
  home_team: TeamSummary;
  away_team: TeamSummary;
  home_score?: number;
  away_score?: number;
  winner?: string;
  evaluation?: MatchEvaluation;
}

export interface CompetitionSummary {
  code: string;
  name: string;
  country?: string;
}

export interface SeasonSummary {
  name: string;
  year_start: number;
  year_end: number;
}

export interface EngineVersionInfo {
  id: number;
  version: string;
  config_hash: string;
  structural_weight: number;
  context_weight: number;
  min_difference: number;
  description?: string;
  created_at: string;
}

export interface TeamHistoryRow {
  season_name: string;
  competition_code: string;
  position?: number;
  played?: number;
  points?: number;
  goal_difference?: number;
  ppg?: number;
}

export interface TeamDetail {
  id: number;
  name: string;
  short_name?: string;
  history: TeamHistoryRow[];
}

export interface BenchmarkTotals {
  evaluated: number;
  selected: number;
  coverage: number;
  correct: number;
  accuracy: number;
  baseline_home: number;
  vs_baseline: number;
}

export interface BenchmarkRange {
  range: string;
  matches: number;
  correct: number;
  accuracy: number;
}

export interface BenchmarkBreakdown {
  competition_code: string;
  matches: number;
  correct: number;
  accuracy: number;
}

export interface BenchmarkSeason {
  season_name: string;
  matches: number;
  correct: number;
  accuracy: number;
}

export interface BenchmarkResponse {
  totals: BenchmarkTotals;
  by_difference_range: BenchmarkRange[];
  by_competition: BenchmarkBreakdown[];
  by_season: BenchmarkSeason[];
}

export interface SyncResponse {
  status: string;
  leagues: Record<string, Record<string, number>>;
}

export interface EvaluateResponse {
  status: string;
  evaluated: number;
}

// ── query params helper ─────────────────────────────────────────────

function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const entries = Object.entries(params).filter(
    ([_, v]) => v !== undefined && v !== null && v !== ""
  );
  if (!entries.length) return "";
  return "?" + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString();
}

// ── API calls ───────────────────────────────────────────────────────

export async function getSystemStatus(): Promise<SystemStatus> {
  return fetchJSON("/api/system/status");
}

export async function getBenchmark(
  params?: { competition_code?: string; season_name?: string; engine_version?: string }
): Promise<BenchmarkResponse> {
  return fetchJSON(`/api/system/benchmark${qs(params ?? {})}`);
}

export async function getMatches(
  params?: {
    competition_code?: string; season_name?: string; status?: string;
    selected?: boolean; from_date?: string; to_date?: string;
    limit?: number; offset?: number;
  }
): Promise<MatchSummary[]> {
  return fetchJSON(`/api/matches${qs(params ?? {})}`);
}

export async function getMatch(id: number): Promise<MatchDetail> {
  return fetchJSON(`/api/matches/${id}`);
}

export async function getTeam(id: number): Promise<TeamDetail> {
  return fetchJSON(`/api/teams/${id}`);
}

export async function getTeamHistory(id: number): Promise<TeamHistoryRow[]> {
  return fetchJSON(`/api/teams/${id}/history`);
}

export async function getCompetitions(): Promise<CompetitionSummary[]> {
  return fetchJSON("/api/competitions");
}

export async function getSeasons(): Promise<SeasonSummary[]> {
  return fetchJSON("/api/seasons");
}

export async function getActiveEngine(): Promise<EngineVersionInfo> {
  return fetchJSON("/api/engine");
}

export async function getEngineVersions(): Promise<EngineVersionInfo[]> {
  return fetchJSON("/api/engine/versions");
}

export async function postSync(): Promise<SyncResponse> {
  return fetchJSON("/api/sync", { method: "POST" });
}

export async function postEvaluate(): Promise<EvaluateResponse> {
  return fetchJSON("/api/evaluate", { method: "POST" });
}
