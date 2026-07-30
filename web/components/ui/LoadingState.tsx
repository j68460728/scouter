import React from "react";
import { Activity } from "lucide-react";

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Cargando..." }: LoadingStateProps) {
  return (
    <div className="flex h-[50vh] items-center justify-center">
      <div className="flex flex-col items-center gap-4 text-slate-500">
        <Activity className="h-8 w-8 animate-spin" />
        <p className="text-sm font-medium">{message}</p>
      </div>
    </div>
  );
}
