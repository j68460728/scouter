"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getMatch, MatchDetail } from "@/lib/api";

function Bar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-24 text-right text-slate-400">{label}</span>
      <div className="flex-1 h-3 rounded-full bg-slate-800 overflow-hidden">
        <div className="h-full rounded-full bg-cyan-500 transition-all" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-12 text-right font-mono text-slate-300">{value.toFixed(1)}</span>
    </div>
  );
}

function StrengthCard({ title, data }: { title: string; data: { total: number; structural: number; context: number } }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-400 uppercase tracking-wider">{title}</h3>
      <Bar label="Total" value={data.total} max={100} />
      <Bar label="Structural" value={data.structural} max={85.7} />
      <Bar label="Context" value={data.context} max={14.3} />
    </div>
  );
}

function formatDateTime(raw: string) {
  const d = new Date(raw);
  return d.toLocaleString("es-ES", {
    weekday: "long", day: "2-digit", month: "long", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export default function MatchPage() {
  const params = useParams();
  const id = Number(params.id);
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMatch(id)
      .then(setMatch)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-slate-500">Loading…</p>;
  if (error) return <p className="text-red-400">{error}</p>;
  if (!match) return <p className="text-slate-500">Match not found.</p>;

  const ev = match.evaluation;

  return (
    <div className="max-w-2xl">
      <Link href="/dashboard" className="mb-4 inline-block text-sm text-cyan-400 hover:underline">← Dashboard</Link>

      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-mono text-slate-400 uppercase">{match.competition_code}</span>
          <span className="text-xs text-slate-500">{match.season_name}</span>
          {match.matchday && <span className="text-xs text-slate-500">MD {match.matchday}</span>}
        </div>
        <h1 className="text-2xl font-bold">
          {match.home_team.name} vs {match.away_team.name}
        </h1>
        <p className="mt-1 text-sm text-slate-400">{formatDateTime(match.utc_date)}</p>
      </div>

      {match.status === "FINISHED" && (
        <div className="mb-6 rounded-lg border border-slate-700 bg-slate-900 p-4 text-center">
          <span className="text-3xl font-bold">
            {match.home_score ?? "?"} – {match.away_score ?? "?"}
          </span>
          {match.winner && (
            <p className="mt-1 text-sm text-slate-400">
              Winner: {match.winner === "HOME_TEAM" ? match.home_team.name : match.winner === "AWAY_TEAM" ? match.away_team.name : "Draw"}
            </p>
          )}
        </div>
      )}

      {ev && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <StrengthCard title={match.home_team.name} data={ev.strength_home} />
            <StrengthCard title={match.away_team.name} data={ev.strength_away} />
          </div>

          <div className="rounded-lg border border-cyan-800 bg-cyan-950/30 p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Difference</span>
              <span className="text-xl font-bold text-cyan-400">{ev.difference.toFixed(1)}</span>
            </div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-sm text-slate-400">Favorite</span>
              <Link href={`/teams/${ev.favorite_team_id}`} className="text-sm font-medium text-cyan-400 hover:underline">
                {ev.favorite_team_name}
              </Link>
            </div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-sm text-slate-400">Selected</span>
              <span className={`text-sm font-medium ${ev.selected ? "text-green-400" : "text-slate-500"}`}>
                {ev.selected ? "Yes" : "No"}
              </span>
            </div>
            {ev.correct !== null && (
              <div className="flex items-center justify-between mt-2">
                <span className="text-sm text-slate-400">Prediction correct</span>
                <span className={`text-sm font-medium ${ev.correct ? "text-green-400" : "text-red-400"}`}>
                  {ev.correct ? "Yes" : "No"}
                </span>
              </div>
            )}
            <div className="mt-3 text-xs text-slate-600">
              Engine: {ev.engine_version} · {new Date(ev.evaluated_at).toLocaleString("es-ES")}
            </div>
          </div>
        </div>
      )}

      {!ev && <p className="text-slate-500 italic">No evaluation available for this match.</p>}
    </div>
  );
}
