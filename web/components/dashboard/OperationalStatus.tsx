import React from "react";
import { Server, Clock, Activity, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { SystemStatus } from "@/lib/api";

interface OperationalStatusProps {
  status: SystemStatus | null;
  connectionError: boolean;
}

export function OperationalStatus({ status, connectionError }: OperationalStatusProps) {
  if (connectionError) {
    return (
      <div className="rounded-xl border border-red-900 bg-red-950/20 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          Estado del Sistema
        </h2>
        <p className="text-sm text-slate-300">
          Servidor de Scouter Inaccesible (API Offline). Asegúrate de que el contenedor de Docker esté iniciado ejecutando <code className="bg-red-950/50 px-1.5 py-0.5 rounded text-red-300">docker compose up scouter</code> en la consola.
        </p>
      </div>
    );
  }

  if (!status) return null;
  const isOk = status.status === "ready" || status.status === "ok";

  const structuralWeightPct = status.engine?.structural_weight
    ? (status.engine.structural_weight * 100).toFixed(1)
    : "85.7";
  const contextWeightPct = status.engine?.context_weight
    ? (status.engine.context_weight * 100).toFixed(1)
    : "14.3";

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 shadow-sm space-y-4">
      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
        <Server className="h-4 w-4 text-cyan-500" />
        Estado Operativo del Sistema
      </h2>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-slate-500 uppercase font-semibold">Conexión API</span>
          <span className="text-sm font-bold flex items-center gap-1.5 text-emerald-400">
            <CheckCircle2 className="h-4 w-4" />
            Online
          </span>
        </div>
        
        <div className="flex flex-col gap-1">
          <span className="text-xs text-slate-500 uppercase font-semibold">Motor Analítico</span>
          <span className="text-sm font-medium text-slate-300 flex items-center gap-1.5">
            <Activity className="h-4 w-4 text-cyan-500" />
            {status.engine?.version ? `${status.engine.version}` : "Sin Motor"}
          </span>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-xs text-slate-500 uppercase font-semibold">Pesos del Modelo</span>
          <span className="text-sm font-medium text-slate-300 flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-slate-500" />
            Est. {structuralWeightPct}% / Cont. {contextWeightPct}%
          </span>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-xs text-slate-500 uppercase font-semibold">Umbral Mínimo</span>
          <span className="text-sm font-medium text-slate-300">
            Diferencia ≥ {status.engine?.min_difference ?? 20}
          </span>
        </div>
      </div>
    </div>
  );
}
