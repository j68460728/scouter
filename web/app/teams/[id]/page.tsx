"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, TrendingUp, BarChart3, Activity, Info } from "lucide-react";
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

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Activity className="h-8 w-8 animate-spin text-slate-600" />
      </div>
    );
  }
  if (error) return <p className="text-red-400">{error}</p>;
  if (!team) return <p className="text-slate-500">Team not found.</p>;

  const currentSeason = team.history.length > 0 ? team.history[0] : null;
  
  // Determinar estado de forma muy básica
  let status = "Equipo establecido";
  if (team.history.length > 1 && currentSeason) {
    const prev = team.history[1];
    if (prev.competition_code !== currentSeason.competition_code) {
      status = "Ascendido o transferido de competición";
    }
  } else if (team.history.length === 1) {
    status = "Primer registro en la base de datos";
  }

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in duration-500 space-y-8">
      <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-cyan-400 transition-colors">
        <ArrowLeft className="h-4 w-4" /> Volver al Dashboard
      </Link>

      <div className="flex flex-col gap-2">
        <h1 className="text-3xl md:text-5xl font-bold text-slate-200 tracking-tight">{team.name}</h1>
        {team.short_name && <p className="text-lg text-slate-400">{team.short_name}</p>}
      </div>

      {currentSeason && (
        <section>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-cyan-500" />
            Contexto Competitivo
          </h2>
          <div className="grid md:grid-cols-5 gap-4">
            <div className="md:col-span-1 rounded-xl border border-slate-800 bg-slate-900/50 p-5 flex flex-col">
              <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">Liga</span>
              <span className="font-mono text-lg font-bold text-slate-200 uppercase">{currentSeason.competition_code}</span>
            </div>
            <div className="md:col-span-1 rounded-xl border border-slate-800 bg-slate-900/50 p-5 flex flex-col">
              <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">Temporada</span>
              <span className="text-lg font-bold text-slate-300">{currentSeason.season_name}</span>
            </div>
            <div className="md:col-span-1 rounded-xl border border-slate-800 bg-slate-900/50 p-5 flex flex-col">
              <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">Posición</span>
              <span className="text-lg font-bold text-slate-200">{currentSeason.position ?? "-"}°</span>
            </div>
            <div className="md:col-span-1 rounded-xl border border-slate-800 bg-slate-900/50 p-5 flex flex-col">
              <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">PPG</span>
              <span className="font-mono text-lg font-bold text-cyan-400">{currentSeason.ppg?.toFixed(2) ?? "-"}</span>
            </div>
            <div className="md:col-span-1 rounded-xl border border-slate-800 bg-slate-900/50 p-5 flex flex-col">
              <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">GD</span>
              <span className={`font-mono text-lg font-bold ${currentSeason.goal_difference && currentSeason.goal_difference >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {currentSeason.goal_difference && currentSeason.goal_difference > 0 ? "+" : ""}{currentSeason.goal_difference ?? "-"}
              </span>
            </div>
            <div className="md:col-span-5 rounded-xl border border-slate-800/50 bg-slate-900/20 px-5 py-3 flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider text-slate-500">Estado</span>
              <span className="text-sm font-medium text-slate-300 flex items-center gap-2">
                <Info className="h-4 w-4 text-slate-500" /> {status}
              </span>
            </div>
          </div>
        </section>
      )}

      <section>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-cyan-500" />
          Historial de Temporadas
        </h2>

        {team.history.length === 0 ? (
          <p className="text-slate-500 italic text-sm border border-slate-800 rounded-xl p-6 text-center bg-slate-900/30">
            No hay datos históricos disponibles.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/30">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-900/50 text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3 font-medium">Liga</th>
                  <th className="px-4 py-3 font-medium">Temporada</th>
                  <th className="px-4 py-3 font-medium text-center">Posición</th>
                  <th className="px-4 py-3 font-medium text-center">Partidos</th>
                  <th className="px-4 py-3 font-medium text-center">Pts</th>
                  <th className="px-4 py-3 font-medium text-center">PPG</th>
                  <th className="px-4 py-3 font-medium text-center">GD</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {team.history.map((h, i) => (
                  <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3">
                      <span className={`rounded px-2.5 py-1 text-xs font-mono text-white ${COMP_COLORS[h.competition_code] || "bg-slate-700"}`}>
                        {h.competition_code}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-300 font-medium">{h.season_name}</td>
                    <td className="px-4 py-3 text-slate-400 text-center">{h.position ?? "-"}</td>
                    <td className="px-4 py-3 text-slate-500 text-center">{h.played ?? "-"}</td>
                    <td className="px-4 py-3 text-slate-300 text-center font-medium">{h.points ?? "-"}</td>
                    <td className="px-4 py-3 text-slate-400 text-center font-mono">{h.ppg?.toFixed(2) ?? "-"}</td>
                    <td className={`px-4 py-3 text-center font-mono font-medium ${h.goal_difference && h.goal_difference >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {h.goal_difference && h.goal_difference > 0 ? "+" : ""}{h.goal_difference ?? "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
