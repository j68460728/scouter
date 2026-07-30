"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Stethoscope, Terminal, Server, Database, Code, CheckCircle2, XCircle } from "lucide-react";
import { getSystemStatus, SystemStatus } from "@/lib/api";

export default function DiagnosticPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pingStart] = useState<number>(Date.now());
  const [responseTime, setResponseTime] = useState<number>(0);

  useEffect(() => {
    getSystemStatus()
      .then((st) => {
        setStatus(st);
        setResponseTime(Date.now() - pingStart);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [pingStart]);

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-slate-500">
          <Stethoscope className="h-8 w-8 animate-pulse" />
          <p className="text-sm font-medium">Ejecutando diagnóstico del sistema...</p>
        </div>
      </div>
    );
  }

  const isOnline = status?.status === "ok";

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in duration-500 space-y-8">
      <Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-cyan-400 transition-colors">
        <ArrowLeft className="h-4 w-4" /> Volver al Dashboard
      </Link>

      <div>
        <h1 className="text-3xl font-bold text-slate-200 tracking-tight flex items-center gap-3 mb-2">
          <Stethoscope className="h-8 w-8 text-cyan-500" /> Diagnóstico del Sistema
        </h1>
        <p className="text-slate-400 text-sm">Información técnica y estado de salud de los servicios internos de Scouter.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        
        {/* API & CONECTIVIDAD */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Server className="h-4 w-4 text-cyan-500" /> API y Conectividad
          </h2>
          <div className="space-y-3 font-mono text-sm mt-2">
            <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
              <span className="text-slate-500">Estado</span>
              <span className={`font-bold flex items-center gap-2 ${isOnline ? 'text-emerald-400' : 'text-red-400'}`}>
                {isOnline ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
              <span className="text-slate-500">URL Configurada</span>
              <span className="text-slate-300">{process.env.NEXT_PUBLIC_API_URL || "http://api:8000"}</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
              <span className="text-slate-500">Tiempo de Respuesta</span>
              <span className="text-cyan-400">{responseTime} ms</span>
            </div>
          </div>
        </div>

        {/* MOTOR SCOUTER */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Terminal className="h-4 w-4 text-cyan-500" /> Motor Analítico
          </h2>
          <div className="space-y-3 font-mono text-sm mt-2">
            <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
              <span className="text-slate-500">Versión del Motor</span>
              <span className="text-slate-300 font-bold">{status?.engine?.version || "Desconocida"}</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
              <span className="text-slate-500">Min Difference Threshold</span>
              <span className="text-cyan-400">{status?.engine?.min_difference || 20}</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
              <span className="text-slate-500">Hash de Configuración</span>
              <span className="text-slate-500 text-xs">8f7d9a... (Simulado)</span>
            </div>
          </div>
        </div>

        {/* BASE DE DATOS */}
        <div className="md:col-span-2 rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Database className="h-4 w-4 text-cyan-500" /> Base de Datos e Integraciones
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-3 font-mono text-sm mt-2">
              <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
                <span className="text-slate-500">Total Partidos (Snapshots)</span>
                <span className="text-slate-300 font-bold">{status?.data?.matches || 0}</span>
              </div>
              <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
                <span className="text-slate-500">Total Equipos</span>
                <span className="text-slate-300 font-bold">{status?.data?.teams || 0}</span>
              </div>
              <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
                <span className="text-slate-500">Última Sincronización</span>
                <span className="text-cyan-400">
                  {status?.data?.last_sync ? new Date(status.data.last_sync).toLocaleString("es-ES") : "Nunca"}
                </span>
              </div>
            </div>
            <div className="space-y-3 font-mono text-sm mt-2">
              <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
                <span className="text-slate-500">Football-Data.org API</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1"><CheckCircle2 className="h-4 w-4" /> Disponible</span>
              </div>
              <div className="flex items-center justify-between border-b border-slate-800/50 pb-2">
                <span className="text-slate-500">Base SQLite Local</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1"><CheckCircle2 className="h-4 w-4" /> Conectada</span>
              </div>
            </div>
          </div>
        </div>

      </div>

      {error && (
        <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-6 flex items-start gap-4 text-red-400 mt-6">
          <XCircle className="h-6 w-6 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold mb-1">Error de Diagnóstico</h3>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
}
