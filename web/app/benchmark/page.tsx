"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, AlertCircle, Activity, ShieldCheck, Target, ChevronRight, Info } from "lucide-react";
import Link from "next/link";
import {
  getBenchmark, getCompetitions, getSeasons, getSystemStatus,
  BenchmarkResponse, CompetitionSummary, SeasonSummary, SystemStatus
} from "@/lib/api";

function ProgressBar({ value, label, colorClass }: { value: number; label: string; colorClass: string }) {
  const pct = Math.max(0, Math.min(value * 100, 100));
  return (
    <div className="flex flex-col gap-1 w-full">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400 font-medium">{label}</span>
        <span className="font-mono text-slate-300 font-bold">{pct.toFixed(1)}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-slate-800/50 overflow-hidden shadow-inner">
        <div className={`h-full rounded-full transition-all duration-1000 ease-out ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function BenchmarkPage() {
  const [data, setData] = useState<BenchmarkResponse | null>(null);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [comps, setComps] = useState<CompetitionSummary[]>([]);
  const [seasons, setSeasons] = useState<SeasonSummary[]>([]);
  
  const [filterComp, setFilterComp] = useState("");
  const [filterSeason, setFilterSeason] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCompetitions(), getSeasons(), getSystemStatus().catch(() => null)])
      .then(([c, s, st]) => { setComps(c); setSeasons(s); setStatus(st); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    getBenchmark({
      competition_code: filterComp || undefined,
      season_name: filterSeason || undefined,
    })
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filterComp, filterSeason]);

  if (loading && !data) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Activity className="h-8 w-8 animate-spin text-slate-600" />
      </div>
    );
  }

  const t = data?.totals;

  // Si Accuracy > 65% consideramos validado.
  const isValidated = t && t.accuracy > 0.65;

  return (
    <div className="max-w-5xl mx-auto animate-in fade-in duration-500 space-y-8">
      <div className="flex items-center justify-between">
        <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-cyan-400 transition-colors">
          <ArrowLeft className="h-4 w-4" /> Volver al Dashboard
        </Link>
        <div className="flex items-center gap-2">
          <select value={filterSeason} onChange={(e) => setFilterSeason(e.target.value)}
            className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm border border-slate-800 text-slate-300 focus:border-cyan-500 outline-none">
            <option value="">Dataset: Todas las Temp.</option>
            {seasons.map((s) => (
              <option key={s.name} value={s.name}>{s.name}</option>
            ))}
          </select>
          <select value={filterComp} onChange={(e) => setFilterComp(e.target.value)}
            className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm border border-slate-800 text-slate-300 focus:border-cyan-500 outline-none">
            <option value="">Ligas: Todas</option>
            {comps.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
          </select>
        </div>
      </div>

      {t ? (
        <>
          {/* HEADER DEL BENCHMARK */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-sm overflow-hidden relative">
            <div className="absolute top-0 right-0 p-8 opacity-5">
              <ShieldCheck className="w-64 h-64" />
            </div>
            
            <div className="relative z-10 grid md:grid-cols-2 gap-8">
              <div className="flex flex-col justify-center space-y-6">
                <div>
                  <h1 className="text-3xl font-bold text-slate-200 flex items-center gap-3 tracking-tight">
                    <Target className="h-8 w-8 text-cyan-500" />
                    Validación del Modelo
                  </h1>
                  <p className="text-slate-400 mt-2 text-sm">
                    Resultados históricos "Out of Sample" evaluados con la configuración actual del motor.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col">
                    <span className="text-xs uppercase tracking-wider text-slate-500">Motor</span>
                    <span className="font-mono font-medium text-cyan-400">{status?.engine?.version || "Scouter v2"}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs uppercase tracking-wider text-slate-500">Dataset</span>
                    <span className="font-medium text-slate-300">{filterSeason || "Histórico Total"}</span>
                  </div>
                  <div className="flex flex-col col-span-2">
                    <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">Estado de la Validación</span>
                    <div className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 w-fit ${isValidated ? 'border-emerald-900/50 bg-emerald-950/30 text-emerald-400' : 'border-amber-900/50 bg-amber-950/30 text-amber-400'}`}>
                      {isValidated ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                      <span className="font-semibold text-sm">{isValidated ? 'Modelo Validado' : 'Requiere Revisión'}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex flex-col justify-center space-y-6 bg-slate-950/50 p-6 rounded-xl border border-slate-800/50">
                <ProgressBar value={t.accuracy} label="Accuracy (Precisión)" colorClass={t.accuracy >= 0.65 ? 'bg-emerald-500' : 'bg-amber-500'} />
                <ProgressBar value={t.coverage} label="Coverage (Cobertura)" colorClass="bg-cyan-500" />
                <ProgressBar value={t.baseline_home} label="Baseline (Victoria Local)" colorClass="bg-slate-500" />
              </div>
            </div>

            {!isValidated && (
              <div className="relative z-10 mt-6 flex items-start gap-3 rounded-lg border border-cyan-800/50 bg-cyan-950/30 p-4 text-sm text-cyan-200">
                <Info className="h-5 w-5 text-cyan-400 shrink-0 mt-0.5" />
                <p>
                  <strong>¿Por qué el modelo requiere revisión?</strong> La precisión observada ({ (t.accuracy * 100).toFixed(1) }%) es inferior al umbral oficial del 65%. 
                  Esto ocurre frecuentemente al evaluar la base de datos "en vivo" debido a la muestra incompleta de la temporada actual. 
                  Para replicar el <span className="font-mono text-cyan-400">68.9%</span> del benchmark oficial, se requiere cargar el dataset histórico (CSV) 
                  de backtesting que contiene 2 temporadas completas y 5 ligas OOS (Out of Sample).
                </p>
              </div>
            )}
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* BY RANGE */}
            {data!.by_difference_range.length > 0 && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-6">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-6 flex items-center gap-2">
                  <ChevronRight className="h-4 w-4 text-cyan-500" /> Rendimiento por Umbral (Δ)
                </h2>
                <div className="space-y-5">
                  {data!.by_difference_range.map((r) => (
                    <div key={r.range} className="flex flex-col gap-2">
                      <div className="flex justify-between items-center text-sm">
                        <span className="font-mono text-slate-300">Δ {r.range}</span>
                        <span className="text-xs text-slate-500">{r.correct} / {r.matches} aciertos</span>
                      </div>
                      <ProgressBar value={r.accuracy} label="" colorClass={r.accuracy >= 0.65 ? 'bg-emerald-500' : 'bg-cyan-600'} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* BY COMPETITION */}
            {data!.by_competition.length > 0 && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-6">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-6 flex items-center gap-2">
                  <ChevronRight className="h-4 w-4 text-cyan-500" /> Rendimiento por Liga
                </h2>
                <div className="space-y-5">
                  {data!.by_competition.map((c) => (
                    <div key={c.competition_code} className="flex flex-col gap-2">
                      <div className="flex justify-between items-center text-sm">
                        <span className="font-mono font-medium text-slate-300 uppercase">{c.competition_code}</span>
                        <span className="text-xs text-slate-500">{c.matches} seleccionados</span>
                      </div>
                      <ProgressBar value={c.accuracy} label="" colorClass={c.accuracy >= 0.65 ? 'bg-emerald-500' : 'bg-amber-500'} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 py-16 text-center text-slate-500">
          <Activity className="mb-4 h-8 w-8" />
          <p>No hay datos de benchmark disponibles para estos filtros.</p>
        </div>
      )}
    </div>
  );
}
