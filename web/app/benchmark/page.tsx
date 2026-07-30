"use client";

import { useEffect, useState } from "react";
import {
  getBenchmark, getCompetitions, getSeasons,
  BenchmarkResponse, CompetitionSummary, SeasonSummary,
} from "@/lib/api";

function AccuracyBadge({ value }: { value: number }) {
  const color = value >= 0.7 ? "text-green-400" : value >= 0.5 ? "text-yellow-400" : "text-red-400";
  return <span className={`font-mono font-bold ${color}`}>{(value * 100).toFixed(1)}%</span>;
}

function StatCard({ label, value, sub }: { label: string; value: string | React.ReactNode; sub?: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
      <p className="mt-1 text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  );
}

export default function BenchmarkPage() {
  const [data, setData] = useState<BenchmarkResponse | null>(null);
  const [comps, setComps] = useState<CompetitionSummary[]>([]);
  const [seasons, setSeasons] = useState<SeasonSummary[]>([]);
  const [filterComp, setFilterComp] = useState("");
  const [filterSeason, setFilterSeason] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCompetitions(), getSeasons()])
      .then(([c, s]) => { setComps(c); setSeasons(s); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    getBenchmark({
      competition_code: filterComp || undefined,
      season_name: filterSeason || undefined,
    })
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filterComp, filterSeason]);

  const t = data?.totals;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Benchmark</h1>

      <div className="mb-6 flex gap-3">
        <select value={filterComp} onChange={(e) => setFilterComp(e.target.value)}
          className="rounded bg-slate-800 px-3 py-1.5 text-sm border border-slate-700">
          <option value="">All competitions</option>
          {comps.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
        </select>
        <select value={filterSeason} onChange={(e) => setFilterSeason(e.target.value)}
          className="rounded bg-slate-800 px-3 py-1.5 text-sm border border-slate-700">
          <option value="">All seasons</option>
          {seasons.map((s) => (
            <option key={s.name} value={s.name}>{s.name}</option>
          ))}
        </select>
      </div>

      {loading && <p className="text-slate-500">Loading…</p>}

      {!loading && t && (
        <>
          <div className="mb-8 grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Evaluated" value={t.evaluated.toLocaleString()} />
            <StatCard label="Selected" value={t.selected.toLocaleString()} sub={`${(t.coverage * 100).toFixed(1)}% coverage`} />
            <StatCard label="Correct" value={t.correct.toLocaleString()} />
            <StatCard label="Accuracy" value={<AccuracyBadge value={t.accuracy} /> as any} sub={`Baseline home: ${(t.baseline_home * 100).toFixed(1)}% · vs baseline: ${(t.vs_baseline >= 0 ? "+" : "")}${(t.vs_baseline * 100).toFixed(1)}%`} />
          </div>

          {data!.by_difference_range.length > 0 && (
            <section className="mb-8">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">By Difference Range</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-500 text-left">
                      <th className="py-2 pr-4">Range</th>
                      <th className="py-2 pr-4">Matches</th>
                      <th className="py-2 pr-4">Correct</th>
                      <th className="py-2 pr-4">Accuracy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data!.by_difference_range.map((r) => (
                      <tr key={r.range} className="border-b border-slate-800/50 hover:bg-slate-900/50">
                        <td className="py-2 pr-4 font-mono text-slate-300">Δ {r.range}</td>
                        <td className="py-2 pr-4 text-slate-400">{r.matches}</td>
                        <td className="py-2 pr-4 text-slate-400">{r.correct}</td>
                        <td className="py-2 pr-4"><AccuracyBadge value={r.accuracy} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {data!.by_competition.length > 0 && (
            <section className="mb-8">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">By Competition</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-500 text-left">
                      <th className="py-2 pr-4">Competition</th>
                      <th className="py-2 pr-4">Matches</th>
                      <th className="py-2 pr-4">Correct</th>
                      <th className="py-2 pr-4">Accuracy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data!.by_competition.map((c) => (
                      <tr key={c.competition_code} className="border-b border-slate-800/50 hover:bg-slate-900/50">
                        <td className="py-2 pr-4 font-mono text-slate-300">{c.competition_code}</td>
                        <td className="py-2 pr-4 text-slate-400">{c.matches}</td>
                        <td className="py-2 pr-4 text-slate-400">{c.correct}</td>
                        <td className="py-2 pr-4"><AccuracyBadge value={c.accuracy} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {data!.by_season.length > 0 && (
            <section className="mb-8">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">By Season</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-500 text-left">
                      <th className="py-2 pr-4">Season</th>
                      <th className="py-2 pr-4">Matches</th>
                      <th className="py-2 pr-4">Correct</th>
                      <th className="py-2 pr-4">Accuracy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data!.by_season.map((s) => (
                      <tr key={s.season_name} className="border-b border-slate-800/50 hover:bg-slate-900/50">
                        <td className="py-2 pr-4 text-slate-300">{s.season_name}</td>
                        <td className="py-2 pr-4 text-slate-400">{s.matches}</td>
                        <td className="py-2 pr-4 text-slate-400">{s.correct}</td>
                        <td className="py-2 pr-4"><AccuracyBadge value={s.accuracy} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
