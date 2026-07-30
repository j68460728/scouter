"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { 
  getSystemStatus, 
  getMatches, 
  postSync, 
  postEvaluate, 
  getBenchmark,
  SystemStatus, 
  MatchSummary,
  BenchmarkResponse 
} from "@/lib/api";
import { OperationalStatus } from "@/components/dashboard/OperationalStatus";
import { MatchCard } from "@/components/dashboard/MatchCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { useToast } from "@/components/ui/Toast";
import { Calendar, SearchX, RefreshCw, Play, Database, TrendingUp, AlertTriangle } from "lucide-react";

const getLocalDateString = (date: Date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export default function Dashboard() {
  const { toast } = useToast();
  
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [benchmark, setBenchmark] = useState<BenchmarkResponse | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [connectionError, setConnectionError] = useState(false);
  
  const [timeWindow, setTimeWindow] = useState<string>("7d");
  const [customStartDate, setCustomStartDate] = useState<string>(() => getLocalDateString(new Date()));
  const [customEndDate, setCustomEndDate] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return getLocalDateString(d);
  });
  
  const [syncing, setSyncing] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const loadData = useCallback(async () => {
    try {
      const st = await getSystemStatus();
      setStatus(st);
      setConnectionError(false);
      
      let from_date: string | undefined = undefined;
      let to_date: string | undefined = undefined;

      if (timeWindow === "custom") {
        if (customStartDate) {
          from_date = new Date(customStartDate + "T00:00:00Z").toISOString();
        }
        if (customEndDate) {
          to_date = new Date(customEndDate + "T23:59:59Z").toISOString();
        }
      } else if (timeWindow !== "all") {
        const days = parseInt(timeWindow);
        const from = new Date();
        const to = new Date();
        to.setDate(to.getDate() + days);
        from_date = from.toISOString();
        to_date = to.toISOString();
      }

      if (st.status === "ready" || st.status === "ok") {
        const [mt, bench] = await Promise.all([
          getMatches({ selected: true, limit: 100, from_date, to_date }),
          getBenchmark().catch(() => null)
        ]);
        setMatches(mt);
        setBenchmark(bench);
      } else {
        setMatches([]);
      }
    } catch (e: any) {
      setConnectionError(true);
      toast(
        "Error de conexión",
        e.message || "No se pudo conectar con el servidor analítico.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  }, [timeWindow, customStartDate, customEndDate, toast]);

  useEffect(() => {
    loadData();
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [loadData]);

  // Polling for sync status change
  const startPollingSync = (previousSyncTime: string | null) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    let attempts = 0;
    
    pollIntervalRef.current = setInterval(async () => {
      attempts++;
      try {
        const st = await getSystemStatus();
        setStatus(st);
        
        // If last_sync updated or pending matches changed
        if (st.data?.last_sync !== previousSyncTime) {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setSyncing(false);
          toast(
            "Datos Actualizados",
            "La sincronización ha finalizado correctamente. Nuevos partidos listos para evaluar.",
            "success"
          );
          loadData();
        } else if (attempts >= 15) {
          // Timeout after ~75 seconds
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setSyncing(false);
          toast(
            "Sincronización extendida",
            "La sincronización sigue en curso en segundo plano en el servidor.",
            "info"
          );
          loadData();
        }
      } catch (e) {
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        setSyncing(false);
      }
    }, 5000);
  };

  const handleSync = async () => {
    if (syncing) return;
    setSyncing(true);
    const oldSync = status?.data?.last_sync || null;
    
    try {
      await postSync();
      toast(
        "Sincronización Iniciada",
        "Buscando nuevos partidos y posiciones en segundo plano...",
        "info"
      );
      // Start checking if it finished
      startPollingSync(oldSync);
    } catch (e: any) {
      setSyncing(false);
      toast(
        "Error de sincronización",
        e.message || "No se pudo iniciar el proceso de actualización.",
        "error"
      );
    }
  };

  const handleEvaluate = async () => {
    if (evaluating) return;
    setEvaluating(true);
    try {
      const res = await postEvaluate();
      toast(
        "Evaluación Completada",
        `Se han analizado ${res.evaluated} partidos con el motor analítico.`,
        "success"
      );
      await loadData();
    } catch (e: any) {
      toast(
        "Error de evaluación",
        e.message || "Ocurrió un error al ejecutar la evaluación.",
        "error"
      );
    } finally {
      setEvaluating(false);
    }
  };

  if (loading && !status) {
    return <LoadingState message="Conectando con Scouter Engine..." />;
  }

  // Smart Empty States
  const renderEmptyState = () => {
    if (connectionError) {
      return (
        <EmptyState 
          icon={<AlertTriangle className="h-8 w-8 text-red-500" />}
          title="Servidor analítico inaccesible"
          description="No se pudo establecer conexión con el backend de Scouter. Comprueba que el contenedor Docker esté encendido."
          action={
            <button 
              onClick={() => { setLoading(true); loadData(); }} 
              className="rounded-lg bg-slate-900 border border-slate-800 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors cursor-pointer"
            >
              Reintentar conexión
            </button>
          }
        />
      );
    }

    if (!status?.engine?.version) {
      return (
        <EmptyState 
          icon={<AlertTriangle className="h-8 w-8 text-amber-500" />}
          title="Motor analítico no configurado"
          description="No hay ninguna versión de motor registrada en la base de datos local SQLite. El motor analítico no puede procesar partidos."
          action={
            <button 
              onClick={() => { setLoading(true); loadData(); }} 
              className="rounded-lg bg-slate-900 border border-slate-800 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors cursor-pointer"
            >
              Verificar Estado
            </button>
          }
        />
      );
    }

    if (status.data?.matches === 0) {
      return (
        <EmptyState 
          icon={<Database className="h-8 w-8 text-cyan-500" />}
          title="Base de datos sin registros"
          description="La base de datos está vacía. Es necesario descargar los datos iniciales de partidos y calendarios desde football-data.org."
          action={
            <button 
              onClick={handleSync}
              disabled={syncing}
              className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-500 disabled:opacity-50 transition-colors cursor-pointer"
            >
              {syncing ? "Sincronizando..." : "Actualizar Datos"}
            </button>
          }
        />
      );
    }

    if (matches.length === 0) {
      if (status.data?.pending_matches > 0) {
        return (
          <EmptyState 
            icon={<Play className="h-8 w-8 text-amber-500" />}
            title="Partidos pendientes de evaluar"
            description={`Hay ${status.data.pending_matches} partidos nuevos en base de datos que aún no han sido analizados por el motor analítico.`}
            action={
              <button 
                onClick={handleEvaluate}
                disabled={evaluating}
                className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-500 disabled:opacity-50 transition-colors cursor-pointer"
              >
                {evaluating ? "Evaluando..." : "Evaluar Partidos"}
              </button>
            }
          />
        );
      }

      return (
        <EmptyState 
          icon={<SearchX className="h-8 w-8 text-slate-500" />}
          title="Sin oportunidades competitivas"
          description={`El motor analítico evaluó los partidos disponibles, pero ninguno superó el umbral competitivo de diferencia (diferencia ≥ ${status.engine?.min_difference ?? 20}) en el período de tiempo seleccionado.`}
          action={
            <button 
              onClick={() => setTimeWindow("all")} 
              className="rounded-lg bg-slate-900 border border-slate-800 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors cursor-pointer"
            >
              Ver todo el histórico (Histórico)
            </button>
          }
        />
      );
    }

    return null;
  };

  const hasPending = status?.data?.pending_matches && status.data.pending_matches > 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* 1. ESTADO OPERATIVO DEL SISTEMA */}
      <section>
        <OperationalStatus status={status} connectionError={connectionError} />
      </section>

      {/* 2. ACCIONES DISPONIBLES */}
      {!connectionError && status && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/20 p-5 shadow-sm space-y-4">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Acciones disponibles
          </h2>
          
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleSync}
                disabled={syncing || evaluating}
                className="flex items-center gap-2 rounded-lg bg-slate-900 border border-slate-800 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 disabled:opacity-50 transition-all cursor-pointer"
              >
                <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin text-cyan-500' : 'text-slate-500'}`} />
                {syncing ? "Sincronizando..." : "Actualizar Datos"}
              </button>

              <button
                onClick={handleEvaluate}
                disabled={!hasPending || evaluating || syncing}
                className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-500 disabled:opacity-40 disabled:hover:bg-cyan-600 disabled:cursor-not-allowed transition-all cursor-pointer"
              >
                <Play className={`h-4 w-4 ${evaluating ? 'animate-spin' : ''}`} />
                {evaluating ? "Evaluando..." : "Evaluar Partidos"}
              </button>
            </div>

            {hasPending && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-400 border border-amber-500/20 animate-pulse">
                <AlertTriangle className="h-3.5 w-3.5" />
                {status.data.pending_matches} partidos listos para evaluar
              </span>
            )}
          </div>
        </section>
      )}

      {/* 3. SELECTOR DEL RANGO TEMPORAL */}
      {!connectionError && status?.engine?.version && (
        <section>
          <div className="mb-6 flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div className="flex flex-col">
              <h2 className="text-lg font-bold text-slate-200">Oportunidades Recomendadas</h2>
              <p className="text-xs text-slate-500 mt-1">
                Partidos con desequilibrio competitivo (diferencia ≥ {status.engine.min_difference})
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-slate-500" />
                <select
                  value={timeWindow}
                  onChange={(e) => setTimeWindow(e.target.value)}
                  className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold border border-slate-800 text-slate-300 focus:border-cyan-500 outline-none transition-colors cursor-pointer"
                >
                  <option value="3d">Próximos 3 días</option>
                  <option value="7d">Próximos 7 días</option>
                  <option value="14d">Próximos 14 días</option>
                  <option value="30d">Próximos 30 días</option>
                  <option value="60d">Próximos 60 días</option>
                  <option value="custom">Rango Personalizado</option>
                  <option value="all">Histórico (Todos)</option>
                </select>
              </div>

              {timeWindow === "custom" && (
                <div className="flex items-center gap-2 animate-in slide-in-from-right-3 duration-300">
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                    className="rounded-lg bg-slate-900 px-2 py-1 text-xs border border-slate-800 text-slate-300 focus:border-cyan-500 outline-none cursor-pointer"
                  />
                  <span className="text-xs text-slate-500">hasta</span>
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    className="rounded-lg bg-slate-900 px-2 py-1 text-xs border border-slate-800 text-slate-300 focus:border-cyan-500 outline-none cursor-pointer"
                  />
                </div>
              )}
            </div>
          </div>

          {/* 4. FEED DE RECOMENDACIONES */}
          {matches.length === 0 ? (
            renderEmptyState()
          ) : (
            <div className="grid gap-6 md:grid-cols-2">
              {matches.map((m) => (
                <MatchCard key={m.id} match={m} />
              ))}
            </div>
          )}
        </section>
      )}

      {/* fallback if engine not loaded or general connection error */}
      {(connectionError || !status?.engine?.version) && renderEmptyState()}

      {/* 5. INFORMACIÓN SECUNDARIA */}
      {!connectionError && status && (
        <section className="border-t border-slate-900 pt-8 mt-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-4 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase">
                <Database className="h-4 w-4 text-slate-600" />
                Volumen de Almacenamiento
              </div>
              <div className="grid grid-cols-3 gap-2 pt-1">
                <div>
                  <div className="text-lg font-bold text-slate-300">{status.data?.matches || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase">Partidos</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-slate-300">{status.data?.teams || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase">Equipos</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-slate-300">{status.data?.competitions || 0}</div>
                  <div className="text-[10px] text-slate-500 uppercase">Ligas</div>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-4 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase">
                <TrendingUp className="h-4 w-4 text-slate-600" />
                Rendimiento Histórico
              </div>
              <div>
                {benchmark ? (
                  <div className="space-y-1">
                    <div className="text-lg font-bold text-slate-300">
                      {(benchmark.totals.accuracy * 100).toFixed(1)}% precisión
                    </div>
                    <div className="text-[10px] text-slate-500">
                      En {benchmark.totals.selected} de {benchmark.totals.evaluated} partidos recomendados (Azar local: {(benchmark.totals.baseline_home * 100).toFixed(1)}%)
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-slate-500 italic pt-2">
                    Benchmark no disponible
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-4 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase">
                <RefreshCw className="h-4 w-4 text-slate-600" />
                Última Actualización
              </div>
              <div className="space-y-1">
                <div className="text-sm font-medium text-slate-300">
                  {status.data?.last_sync ? new Date(status.data.last_sync).toLocaleString("es-ES", { dateStyle: "medium", timeStyle: "short" }) : "Nunca"}
                </div>
                <div className="text-[10px] text-slate-500">
                  Fecha del último ciclo de ingesta completado
                </div>
              </div>
            </div>

          </div>
        </section>
      )}

    </div>
  );
}
