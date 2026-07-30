"use client";

import { useEffect } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  const isFetchError = error.message.toLowerCase().includes("fetch") || error.message.toLowerCase().includes("network");

  return (
    <div className="flex min-h-screen items-center justify-center p-4 text-slate-200">
      <div className="w-full max-w-md rounded-xl border border-red-900/50 bg-red-950/20 p-6 backdrop-blur-sm">
        <div className="mb-4 flex items-center gap-3 text-red-400">
          <AlertCircle className="h-6 w-6" />
          <h2 className="text-lg font-semibold">
            {isFetchError ? "Backend no disponible" : "Error en la aplicación"}
          </h2>
        </div>

        <p className="mb-6 text-sm text-slate-400">
          {isFetchError
            ? "No fue posible conectar con la API de Scouter."
            : error.message}
        </p>

        {isFetchError && (
          <div className="mb-6 space-y-4 rounded-lg bg-black/40 p-4 text-sm font-mono">
            <div>
              <span className="text-slate-500">URL configurada</span>
              <p className="mt-1 text-slate-300">{process.env.NEXT_PUBLIC_API_URL || "http://api:8000"}</p>
            </div>
            <div>
              <span className="text-slate-500">Estado</span>
              <p className="mt-1 text-red-400">Sin respuesta (Timeout / Refused)</p>
            </div>
            <div>
              <span className="text-slate-500">Posibles causas</span>
              <ul className="mt-2 list-inside list-disc space-y-1 text-slate-300">
                <li>API detenida o reiniciando</li>
                <li>Contenedor Docker no iniciado</li>
                <li>Puerto incorrecto en la variable de entorno</li>
              </ul>
            </div>
          </div>
        )}

        <button
          onClick={() => reset()}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-800 px-4 py-2.5 text-sm font-medium text-slate-200 hover:bg-slate-700 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Reintentar conexión
        </button>
      </div>
    </div>
  );
}
