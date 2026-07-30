"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";

export type ToastType = "success" | "error" | "info";

interface ToastMessage {
  id: string;
  title: string;
  message?: string;
  type: ToastType;
}

interface ToastContextValue {
  toast: (title: string, message?: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used within a ToastProvider");
  return context;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const toast = useCallback((title: string, message?: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`flex items-start gap-3 w-80 rounded-lg p-4 shadow-xl border animate-in slide-in-from-right-8 fade-in duration-300 ${
              t.type === "error"
                ? "bg-red-950 border-red-900/50 text-red-200"
                : t.type === "success"
                ? "bg-emerald-950 border-emerald-900/50 text-emerald-200"
                : "bg-slate-900 border-slate-800 text-slate-200"
            }`}
          >
            {t.type === "error" && <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />}
            {t.type === "success" && <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" />}
            {t.type === "info" && <Info className="h-5 w-5 shrink-0 text-cyan-500" />}
            
            <div className="flex-1">
              <h4 className="text-sm font-semibold">{t.title}</h4>
              {t.message && <p className="text-xs opacity-90 mt-1">{t.message}</p>}
            </div>
            
            <button onClick={() => removeToast(t.id)} className="opacity-50 hover:opacity-100 transition-opacity">
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
