import Link from "next/link";
import { Activity } from "lucide-react";

export function TopNav() {
  return (
    <header className="sticky top-0 z-10 border-b border-slate-900 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link href="/dashboard" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors">
          <Activity className="h-5 w-5" />
          <span className="font-bold tracking-tight">Scouter Engine</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm font-medium">
          <Link href="/dashboard" className="text-cyan-400 transition-colors">Recomendaciones</Link>
        </nav>
      </div>
    </header>
  );
}
