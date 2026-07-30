"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getTeam, TeamDetail } from "@/lib/api";

const COMP_COLORS: Record<string, string> = {
  PL: "bg-purple-600", BL1: "bg-red-600", PD: "bg-yellow-600",
  SA: "bg-blue-600", FL1: "bg-emerald-600",
};

export default function TeamPage() {
  const params = useParams();
  const id = Number(params.id);
  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTeam(id)
      .then(setTeam)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-slate-500">Loading…</p>;
  if (error) return <p className="text-red-400">{error}</p>;
  if (!team) return <p className="text-slate-500">Team not found.</p>;

  return (
    <div className="max-w-2xl">
      <Link href="/dashboard" className="mb-4 inline-block text-sm text-cyan-400 hover:underline">← Dashboard</Link>

      <h1 className="text-2xl font-bold mb-1">{team.name}</h1>
      {team.short_name && <p className="text-sm text-slate-400 mb-6">{team.short_name}</p>}

      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Season History</h2>

      {team.history.length === 0 && <p className="text-slate-500 italic text-sm">No historical data.</p>}

      <div className="space-y-2">
        {team.history.map((h, i) => (
          <div key={i} className="flex items-center gap-4 rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 text-sm">
            <span className={`rounded px-2 py-0.5 text-xs font-mono text-white ${COMP_COLORS[h.competition_code] || "bg-slate-700"}`}>
              {h.competition_code}
            </span>
            <span className="w-24 text-slate-300">{h.season_name}</span>
            {h.position != null && <span className="text-slate-400">Pos {h.position}</span>}
            {h.played != null && <span className="text-slate-500">P{h.played}</span>}
            {h.points != null && <span className="text-slate-400 font-medium">{h.points} pts</span>}
            {h.ppg != null && <span className="text-slate-500">{h.ppg.toFixed(2)} ppg</span>}
            {h.goal_difference != null && (
              <span className={h.goal_difference >= 0 ? "text-green-400" : "text-red-400"}>
                {h.goal_difference >= 0 ? "+" : ""}{h.goal_difference}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
