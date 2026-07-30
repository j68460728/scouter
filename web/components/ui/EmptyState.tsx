import React from "react";
import { Activity } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-900/20 py-16 text-center">
      <div className="mb-4 text-slate-600">
        {icon || <Activity className="h-8 w-8" />}
      </div>
      <h3 className="text-sm font-medium text-slate-300">{title}</h3>
      <p className="text-sm text-slate-400 mt-2 max-w-sm">
        {description}
      </p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
