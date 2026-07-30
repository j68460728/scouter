"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Trophy, Activity, CheckCircle2, AlertCircle, Info } from "lucide-react";
import { getMatch, MatchDetail, getSystemStatus } from "@/lib/api";

function Bar({ label, value, max, colorClass }: { label: string; value: number; max: number; colorClass: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="flex items-center gap-4 text-sm">
      <span className="w-24 text-slate-400 font-medium">{label}</span>
      <div className="flex-1 h-3 rounded-full bg-slate-800/50 overflow-hidden shadow-inner">
        <div className={`h-full rounded-full transition-all duration-1000 ease-out ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-12 text-right font-mono text-slate-300 font-medium">{value.toFixed(1)}</span>
    </div>
  );
}

function formatDateTime(raw: string) {
  return new Date(raw).toLocaleString("es-ES", {
    weekday: "long", day: "2-digit", month: "long", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export default function MatchPage() {
  const params = useParams();
  const id = Number(params.id);
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [minThreshold, setMinThreshold] = useState<number>(20); // default
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getMatch(id),
      getSystemStatus().catch(() => null)
    ])
    .then(([m, sys]) => {
      setMatch(m);
      if (sys?.engine?.min_difference) setMinThreshold(sys.engine.min_difference);
    })
    .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Activity className="h-8 w-8 animate-spin text-slate-600" />
      </div>
    );
  }

  if (!match) return <p className="text-slate-500">Match not found.</p>;

  const ev = match.evaluation;

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in duration-500 space-y-8">
      <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-cyan-400 transition-colors">
        <ArrowLeft className="h-4 w-4" /> Volver al Dashboard
      </Link>

      {/* HEADER: EL ENFRENTAMIENTO */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-8 shadow-sm">
        <div className="flex flex-col items-center justify-center text-center">
          <div className="mb-4 flex items-center gap-3">
            <span className="rounded bg-slate-800 px-3 py-1 text-xs font-mono text-slate-400 uppercase tracking-widest shadow-inner">
              {match.competition_code} • {match.season_name}
            </span>
            {match.matchday && <span className="text-xs font-medium text-slate-500">Jornada {match.matchday}</span>}
          </div>
          
          <div className="flex items-center justify-center gap-8 md:gap-16 w-full">
            <div className="flex-1 text-right">
              <h1 className="text-2xl md:text-4xl font-bold text-slate-200 tracking-tight">
                {match.home_team.name}
              </h1>
            </div>
            
            <div className="flex flex-col items-center px-4">
              <span className="text-sm font-bold text-slate-600 uppercase tracking-widest mb-1">vs</span>
              {match.status === "FINISHED" ? (
                <div className="rounded-lg bg-slate-800 px-4 py-2 text-2xl font-bold text-white shadow-inner border border-slate-700/50">
                  {match.home_score} - {match.away_score}
                </div>
              ) : (
                <span className="text-sm text-slate-500">{formatDateTime(match.utc_date)}</span>
              )}
            </div>

            <div className="flex-1 text-left">
              <h1 className="text-2xl md:text-4xl font-bold text-slate-200 tracking-tight">
                {match.away_team.name}
              </h1>
            </div>
          </div>
        </div>
      </div>

      {!ev && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 py-16 text-center text-slate-500">
          <Info className="mb-4 h-8 w-8" />
          <p>No hay evaluación disponible para este partido.</p>
        </div>
      )}

      {ev && (
        <>
          {/* DECISIÓN PRINCIPAL */}
          <div className="grid md:grid-cols-4 gap-4">
            <div className="md:col-span-1 flex flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-6">
              <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">Favorito</span>
              <span className="text-lg font-bold text-cyan-400 flex items-center gap-2">
                <Trophy className="h-4 w-4" /> {ev.favorite_team_name}
              </span>
            </div>
            <div className="md:col-span-1 flex flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-6">
              <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">Diferencia</span>
              <span className="text-lg font-mono font-bold text-slate-200">+{ev.difference.toFixed(1)}</span>
            </div>
            <div className="md:col-span-1 flex flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-6">
              <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">Threshold</span>
              <span className="text-lg font-mono font-bold text-slate-500">{minThreshold.toFixed(1)}</span>
            </div>
            <div className={`md:col-span-1 flex flex-col rounded-xl border p-6 ${ev.selected ? 'border-emerald-900/50 bg-emerald-950/20' : 'border-slate-800 bg-slate-900/50'}`}>
              <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">Seleccionado</span>
              <span className={`text-lg font-bold flex items-center gap-2 ${ev.selected ? 'text-emerald-400' : 'text-slate-400'}`}>
                {ev.selected ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                {ev.selected ? "Sí" : "No"}
              </span>
            </div>
          </div>

          {/* DESGLOSE DE FUERZA */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* HOME TEAM */}
            <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/30 p-6 shadow-sm">
              <div className="mb-6 flex items-center justify-between border-b border-slate-800/50 pb-4">
                <h3 className="text-lg font-semibold text-slate-200">{match.home_team.name}</h3>
                <span className="font-mono text-xl font-bold text-cyan-400">{ev.strength_home.total.toFixed(1)}</span>
              </div>
              <div className="space-y-4">
                <Bar label="Structural" value={ev.strength_home.structural} max={85.7} colorClass="bg-indigo-500" />
                <Bar label="Context" value={ev.strength_home.context} max={14.3} colorClass="bg-emerald-500" />
              </div>
            </div>

            {/* AWAY TEAM */}
            <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/30 p-6 shadow-sm">
              <div className="mb-6 flex items-center justify-between border-b border-slate-800/50 pb-4">
                <h3 className="text-lg font-semibold text-slate-200">{match.away_team.name}</h3>
                <span className="font-mono text-xl font-bold text-cyan-400">{ev.strength_away.total.toFixed(1)}</span>
              </div>
              <div className="space-y-4">
                <Bar label="Structural" value={ev.strength_away.structural} max={85.7} colorClass="bg-indigo-500" />
                <Bar label="Context" value={ev.strength_away.context} max={14.3} colorClass="bg-emerald-500" />
              </div>
            </div>
          </div>

          {/* EXPLICACIÓN MATEMÁTICA */}
          <div className="rounded-xl border border-cyan-900/30 bg-cyan-950/10 p-6 shadow-sm">
            <h3 className="mb-4 text-sm font-semibold text-cyan-500 uppercase tracking-widest flex items-center gap-2">
              <Info className="h-4 w-4" />
              Explicación de la Diferencia
            </h3>
            
            <div className="space-y-3 font-mono text-sm">
              <div className="flex items-center justify-between rounded bg-slate-900/50 px-4 py-2 border border-slate-800">
                <span className="text-slate-400">Ventaja Structural</span>
                <span className="text-indigo-400 font-bold">
                  {Math.abs(ev.strength_home.structural - ev.strength_away.structural).toFixed(1)}
                </span>
              </div>
              <div className="flex items-center justify-between rounded bg-slate-900/50 px-4 py-2 border border-slate-800">
                <span className="text-slate-400">Ventaja Contextual</span>
                <span className="text-emerald-400 font-bold">
                  {Math.abs(ev.strength_home.context - ev.strength_away.context).toFixed(1)}
                </span>
              </div>
              <div className="flex items-center justify-between rounded bg-cyan-900/20 px-4 py-3 border border-cyan-800/30 mt-4">
                <span className="text-cyan-400 font-bold">Diferencia Total</span>
                <span className="text-cyan-400 text-lg font-bold">
                  {ev.difference.toFixed(1)}
                </span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
