"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { 
  Server, Database, Activity, Target, ShieldCheck, 
  RotateCw, Play, PlayCircle, Clock, CheckCircle2, RefreshCw 
} from "lucide-react";
import {
  getSystemStatus,
  getBenchmark,
  getMatches,
  postSync,
  postEvaluate,
  SystemStatus,
  BenchmarkResponse,
  MatchSummary
} from "@/lib/api";

export default function Dashboard() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkResponse | null>(null);
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [loading, setLoading] = useState(true);

  // Sync Progress State
  const [syncing, setSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState(0);
  const [evaluating, setEvaluating] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const st = await getSystemStatus();
      setStatus(st);
      if (st.engine?.version) {
        const [bm, mt] = await Promise.all([
          getBenchmark().catch(() => null), // Catch benchmark error if it fails
          getMatches({ selected: true, limit: 12 }),
        ]);
        setBenchmark(bm);
        setMatches(mt);
      }
    } catch (e) {
      // Allow error boundary to catch initial fetch errors
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncProgress(0);
    
    // Simulate progress while syncing (approx 2 minutes)
    const interval = setInterval(() => {
      setSyncProgress(p => {
        if (p >= 95) return p;
        return p + Math.random() * 2;
      });
    }, 1000);

    try {
      await postSync();
      setSyncProgress(100);
      setTimeout(() => setSyncing(false), 500);
      await loadAll();
    } catch (e) {
      clearInterval(interval);
      setSyncing(false);
      alert("Error sincronizando: " + (e as Error).message);
    } finally {
      clearInterval(interval);
    }
  };

  const handleEvaluate = async () => {
    setEvaluating(true);
    try {
      await postEvaluate();
      await loadAll();
    } catch (e) {
      alert("Error evaluando: " + (e as Error).message);
    } finally {
      setEvaluating(false);
    }
  };

  if (loading && !status) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-slate-500">
          <RefreshCw className="h-8 w-8 animate-spin" />
          <p className="text-sm font-medium">Conectando con Engine v2...</p>
        </div>
      </div>
    );
  }

  const isOnline = status?.status === "ok";
  const acc = benchmark?.totals.accuracy ? (benchmark.totals.accuracy * 100).toFixed(1) : "--";
  const cov = benchmark?.totals.coverage ? (benchmark.totals.coverage * 100).toFixed(1) : "--";

  const formatDate = (raw: string) => {
    return new Date(raw).toLocaleString("es-ES", {
      day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"
    });
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* 1. ESTADO DEL SISTEMA & ACCIONES */}
      <section className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        
        {/* Status Card */}
        <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-400">API</h3>
            {isOnline ? (
              <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
                </span>
                Online
              </span>
            ) : (
              <span className="text-xs font-semibold text-red-400">Offline</span>
            )}
          </div>
          <div className="mt-auto space-y-3 text-sm">
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-500">Motor</span>
              <span className="font-mono text-cyan-400">{status?.engine?.version || "Ninguno"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Última Sync</span>
              <span className="text-slate-300">
                {status?.data?.last_sync ? formatDate(status.data.last_sync) : "Nunca"}
              </span>
            </div>
          </div>
        </div>

        {/* Database Card */}
        <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-slate-400">
            <Database className="h-4 w-4" />
            <h3 className="text-sm font-medium">Base de Datos</h3>
          </div>
          <div className="mt-auto space-y-3 text-sm">
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-500">Partidos</span>
              <span className="font-medium text-slate-200">{status?.data?.matches || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Equipos</span>
              <span className="font-medium text-slate-200">{status?.data?.teams || 0}</span>
            </div>
          </div>
        </div>

        {/* Benchmark Card */}
        <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-slate-400">
            <Target className="h-4 w-4" />
            <h3 className="text-sm font-medium">Benchmark Global</h3>
          </div>
          <div className="mt-auto space-y-3 text-sm">
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-500">Accuracy</span>
              <span className="font-semibold text-emerald-400">{acc}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Coverage</span>
              <span className="font-medium text-amber-400">{cov}%</span>
            </div>
          </div>
        </div>

        {/* Actions Card */}
        <div className="flex flex-col justify-end gap-3 rounded-xl border border-slate-800 bg-slate-900/30 p-5 shadow-sm">
          <button
            onClick={handleSync}
            disabled={syncing || evaluating}
            className="group flex items-center justify-center gap-2 rounded-lg bg-slate-800 py-2.5 text-sm font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-50 transition-colors"
          >
            <RotateCw className={`h-4 w-4 ${syncing ? "animate-spin text-cyan-400" : "text-slate-400 group-hover:text-white"}`} />
            {syncing ? "Sincronizando..." : "Sincronizar"}
          </button>
          <button
            onClick={handleEvaluate}
            disabled={syncing || evaluating}
            className="group flex items-center justify-center gap-2 rounded-lg bg-cyan-900/30 py-2.5 text-sm font-medium text-cyan-400 hover:bg-cyan-900/50 hover:text-cyan-300 disabled:opacity-50 transition-colors border border-cyan-800/50"
          >
            <Play className={`h-4 w-4 ${evaluating ? "animate-pulse" : ""}`} />
            {evaluating ? "Evaluando..." : "Evaluar Partidos"}
          </button>
          <Link
            href="/benchmark"
            className="flex items-center justify-center gap-2 rounded-lg border border-slate-800 py-2 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          >
            <ShieldCheck className="h-4 w-4" />
            Ver Benchmark
          </Link>
          <Link
            href="/diagnostic"
            className="flex items-center justify-center gap-2 rounded-lg border border-slate-800 py-2 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          >
            <Server className="h-4 w-4" />
            Diagnóstico
          </Link>
        </div>
      </section>

      {/* Sync Progress Alert */}
      {syncing && (
        <div className="rounded-xl border border-cyan-900/50 bg-cyan-950/20 p-5 shadow-inner">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-cyan-400 flex items-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin" /> 
              Sincronizando fuentes externas...
            </h4>
            <span className="text-xs font-mono text-cyan-500">{Math.round(syncProgress)}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
            <div 
              className="h-full bg-cyan-500 transition-all duration-300 ease-out" 
              style={{ width: `${syncProgress}%` }} 
            />
          </div>
          <p className="mt-2 text-xs text-slate-500 flex justify-between">
            <span>Actualizando fixtures y standings</span>
            <span>Tiempo est. ~2 mins</span>
          </p>
        </div>
      )}

      {/* 2. PROXIMOS PARTIDOS SELECCIONADOS */}
      <section>
        <div className="mb-6 flex items-center justify-between border-b border-slate-800 pb-4">
          <h2 className="text-lg font-bold text-slate-200">Próximos Partidos Seleccionados</h2>
          <span className="rounded bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-400">
            {matches.length} partidos
          </span>
        </div>

        {matches.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 py-16 text-center">
            <Activity className="mb-4 h-8 w-8 text-slate-600" />
            <p className="text-sm text-slate-400">No hay partidos seleccionados por el motor.</p>
            <p className="text-xs text-slate-500 mt-1">Ejecuta "Evaluar Partidos" para analizar fixtures pendientes.</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {matches.map((m) => (
              <Link
                key={m.id}
                href={`/matches/${m.id}`}
                className="group flex flex-col rounded-xl border border-slate-800 bg-slate-900/40 p-5 hover:border-cyan-800 hover:bg-slate-900/80 transition-all"
              >
                <div className="mb-4 flex items-center justify-between text-xs text-slate-500">
                  <span className="rounded bg-slate-800 px-2 py-0.5 font-mono uppercase tracking-wider text-slate-400">
                    {m.competition_code}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3 w-3" />
                    {new Date(m.utc_date).toLocaleString("es-ES", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                  </div>
                </div>

                <div className="flex flex-col gap-2 mb-4">
                  <div className={`flex items-center justify-between ${m.favorite_team_name === m.home_team_name ? "font-semibold text-slate-200" : "text-slate-400"}`}>
                    <span>{m.home_team_name}</span>
                    {m.favorite_team_name === m.home_team_name && <CheckCircle2 className="h-4 w-4 text-cyan-500" />}
                  </div>
                  <div className={`flex items-center justify-between ${m.favorite_team_name === m.away_team_name ? "font-semibold text-slate-200" : "text-slate-400"}`}>
                    <span>{m.away_team_name}</span>
                    {m.favorite_team_name === m.away_team_name && <CheckCircle2 className="h-4 w-4 text-cyan-500" />}
                  </div>
                </div>

                <div className="mt-auto flex items-center justify-between border-t border-slate-800/50 pt-4">
                  <div className="flex flex-col">
                    <span className="text-[10px] uppercase tracking-wider text-slate-500">Strength Diff</span>
                    <span className="font-mono text-sm font-medium text-cyan-400">+{m.difference?.toFixed(1)}</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs font-medium text-slate-500 group-hover:text-cyan-400 transition-colors">
                    Ver Detalle <PlayCircle className="h-4 w-4 ml-1" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
