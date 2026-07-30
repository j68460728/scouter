import React from "react";
import Link from "next/link";
import { MatchSummary } from "@/lib/api";
import { Trophy, Calendar, ChevronRight } from "lucide-react";

interface MatchCardProps {
  match: MatchSummary;
}

export function MatchCard({ match }: MatchCardProps) {
  const date = new Date(match.utc_date).toLocaleString("es-ES", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  });

  return (
    <div className="flex flex-col rounded-xl border border-cyan-900/40 bg-slate-900/60 shadow-lg hover:border-cyan-700/60 hover:bg-slate-900/80 transition-all overflow-hidden">
      
      {/* HEADER: Liga y Fecha */}
      <div className="flex items-center justify-between border-b border-slate-800/80 bg-slate-950/50 px-4 py-3">
        <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-mono font-bold text-slate-300 uppercase tracking-wider">
          {match.competition_code}
        </span>
        <span className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
          <Calendar className="h-3.5 w-3.5" />
          {date}
        </span>
      </div>

      {/* BODY: Equipos y Favorito */}
      <div className="p-5 flex flex-col gap-4 relative">
        <div className="flex items-center justify-between w-full">
          <div className="flex flex-col w-2/5 text-right">
            {match.home_team_id ? (
              <Link href={`/teams/${match.home_team_id}`} className={`hover:underline hover:text-cyan-300 transition-colors text-base font-bold tracking-tight ${match.favorite_team_name === match.home_team_name ? 'text-cyan-400 font-extrabold' : 'text-slate-200'}`}>
                {match.home_team_name}
              </Link>
            ) : (
              <span className={`text-base font-bold tracking-tight ${match.favorite_team_name === match.home_team_name ? 'text-cyan-400' : 'text-slate-200'}`}>
                {match.home_team_name}
              </span>
            )}
          </div>
          
          <div className="flex flex-col items-center justify-center w-1/5 px-2">
            <span className="text-xs font-bold text-slate-600 uppercase tracking-widest">vs</span>
          </div>
          
          <div className="flex flex-col w-2/5 text-left">
            {match.away_team_id ? (
              <Link href={`/teams/${match.away_team_id}`} className={`hover:underline hover:text-cyan-300 transition-colors text-base font-bold tracking-tight ${match.favorite_team_name === match.away_team_name ? 'text-cyan-400 font-extrabold' : 'text-slate-200'}`}>
                {match.away_team_name}
              </Link>
            ) : (
              <span className={`text-base font-bold tracking-tight ${match.favorite_team_name === match.away_team_name ? 'text-cyan-400' : 'text-slate-200'}`}>
                {match.away_team_name}
              </span>
            )}
          </div>
        </div>

        {/* DECISION Y EXPLAINABILITY */}
        {match.favorite_team_name && match.difference !== undefined && (
          <div className="mt-2 rounded-lg border border-slate-800 bg-slate-950/30 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Trophy className="h-4 w-4 text-cyan-500" />
                <span>Favorito: <strong className="text-cyan-400">{match.favorite_team_name}</strong></span>
              </div>
              <div className="font-mono text-sm font-bold text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded">
                Δ +{match.difference.toFixed(1)}
              </div>
            </div>
            
            <div className="border-t border-slate-800/50 pt-3 mt-3">
              <p className="text-xs text-slate-500">
                Estado del partido: <span className="font-semibold text-slate-400 uppercase text-[10px]">{match.status}</span>
              </p>
            </div>
          </div>
        )}
      </div>

      {/* FOOTER: Acción */}
      <Link href={`/matches/${match.id}`} className="mt-auto flex items-center justify-center gap-2 border-t border-slate-800 bg-cyan-950/20 px-4 py-3 text-sm font-semibold text-cyan-500 hover:bg-cyan-900/30 hover:text-cyan-400 transition-colors">
        Ver análisis completo <ChevronRight className="h-4 w-4" />
      </Link>

    </div>
  );
}
