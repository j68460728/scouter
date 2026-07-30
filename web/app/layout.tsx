"use client";

import "./globals.css";
import { ToastProvider } from "@/components/ui/Toast";
import { TopNav } from "@/components/layout/TopNav";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-200 antialiased selection:bg-cyan-500/30">
        <ToastProvider>
          <TopNav />
          <main className="mx-auto w-full max-w-6xl px-4 py-8">{children}</main>
        </ToastProvider>
      </body>
    </html>
  );
}
