"use client";

import Link from "next/link";
import "./globals.css";
import { Activity } from "lucide-react";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-200 antialiased selection:bg-cyan-500/30">
        <header className="sticky top-0 z-10 border-b border-slate-900 bg-slate-950/80 backdrop-blur-md">
          <div className="mx-auto flex h-14 max-w-6xl items-center px-4">
            <Link href="/dashboard" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors">
              <Activity className="h-5 w-5" />
              <span className="font-bold tracking-tight">Scouter Engine</span>
            </Link>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
