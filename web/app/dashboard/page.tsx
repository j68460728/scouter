"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  getMatches, getCompetitions,
  MatchSummary, CompetitionSummary,
} from "@/lib/api";

export default function Dashboard() {
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [comps, setComps] = useState<CompetitionSummary[]>([]);
  const [filterComp, setFilterComp] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, c] = await Promise.all([
        getMatches({ selected: true, limit: 100 }),
        getCompetitions(),
      ]);
      setMatches(m);
      setComps(c);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = filterComp
    ? matches.filter((m) => m.competition_code === filterComp)
    : matches;

  const formatDate = (raw: string) => {
    const d = new Date(raw);
    return d.toLocaleDateString("es-ES", { weekday: "short", day: "2-digit", month: "short" });
  };

  const formatTime = (raw: string) => {
    const d = new Date(raw);
    return d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
  };

  if (loading) return <p className="text-slate-500">Loading…</p>;
  if (error) return <p className="text-red-400">{error}</p>;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Selected Matches</h1>
        <select
          value={filterComp}
          onChange={(e) => setFilterComp(e.target.value)}
          className="rounded bg-slate-800 px-3 py-1.5 text-sm text-slate-200 border border-slate-700"
        >
          <option value="">All competitions</option>
          {comps.map((c) => (
            <option key={c.code} value={c.code}>{c.name}</option>
          ))}
        </select>
      </div>

      {filtered.length === 0 && (
        <p className="text-slate-500 text-center py-12">No selected matches found. Sync data and evaluate.</p>
      )}

      <div className="grid gap-3">
        {filtered.map((m) => (
          <Link
            key={m.id}
            href={`/matches/${m.id}`}
            className="group flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900 px-5 py-4 hover:border-cyan-700 transition-colors"
          >
            <div className="flex items-center gap-4 min-w-0">
              <span className="w-10 shrink-0 rounded bg-slate-800 px-2 py-1 text-center text-xs font-mono text-slate-400 uppercase">
                {m.competition_code}
              </span>
              <div className="truncate">
                <span className="font-semibold">{m.home_team_name}</span>
                <span className="mx-2 text-slate-600">vs</span>
                <span className="font-semibold">{m.away_team_name}</span>
              </div>
              <span className="hidden sm:block text-xs text-slate-500">{formatDate(m.utc_date)}</span>
            </div>
            <div className="flex items-center gap-4 shrink-0">
              <span className="text-xs text-slate-500">{formatTime(m.utc_date)}</span>
              <span className="text-xs text-slate-500">Δ {m.difference?.toFixed(1)}</span>
              {m.favorite_team_name && (
                <span className="text-xs text-cyan-400 font-medium">{m.favorite_team_name}</span>
              )}
              <span className="text-slate-600 group-hover:text-cyan-400 transition-colors">→</span>
            </div>
          </Link>
        ))}
      </div>

      <p className="mt-4 text-xs text-slate-600">
        {filtered.length} match{filtered.length !== 1 ? "es" : ""} selected
        {filterComp ? ` in ${filterComp}` : ""}
      </p>
    </div>
  );
}
