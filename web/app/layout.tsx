"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import "./globals.css";
import { getSystemStatus, postSync, postEvaluate, SystemStatus } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/benchmark", label: "Benchmark" },
];

function StatusBar() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [evaluating, setEvaluating] = useState(false);

  const fetchStatus = () => getSystemStatus().then(setStatus).catch(() => {});

  useEffect(() => { fetchStatus(); const id = setInterval(fetchStatus, 30000); return () => clearInterval(id); }, []);

  const handleSync = async () => {
    setSyncing(true);
    try { await postSync(); await postEvaluate(); await fetchStatus(); } catch {}
    setSyncing(false);
  };

  const lastSync = status?.data?.last_sync;
  const formatted = lastSync
    ? new Date(lastSync).toLocaleString("es-ES", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/dashboard" className="text-lg font-bold text-cyan-400 tracking-tight">
          Scouter
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} className="text-slate-400 hover:text-white transition-colors">
              {n.label}
            </Link>
          ))}
          <span className="h-4 w-px bg-slate-700" />
          {formatted && <span className="text-xs text-slate-500">Sync: {formatted}</span>}
          {status?.engine?.version && (
            <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-cyan-400 font-mono">
              {status.engine.version}
            </span>
          )}
          <button
            onClick={handleSync}
            disabled={syncing}
            className="rounded bg-cyan-600 px-3 py-1 text-xs font-medium text-white hover:bg-cyan-500 disabled:opacity-50 transition-colors"
          >
            {syncing ? "Syncing…" : "Sync"}
          </button>
        </nav>
      </div>
    </header>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="dark">
      <body className="min-h-screen flex flex-col">
        <StatusBar />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
