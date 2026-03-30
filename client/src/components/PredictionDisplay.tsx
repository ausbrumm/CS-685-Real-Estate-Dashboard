"use client";

import { Region } from "@/lib/types";
import React, { useState } from "react";
import { GenericLineChart } from "@/components/LineChart";

interface AccuracySummary {
  correct: number;
  wrong: number;
  total: number;
  accuracy: number;
  mse: number;
  rmse: number;
}

interface ErrorBandPoint {
  date: string;
  predicted: number;
  upper: number;
  lower: number;
}

interface PredictionResult {
  date: string | null;
  predictions: Record<string, { direction: string; price: number }>;
}

interface PredictionData {
  region_id: number;
  region_name: string;
  patterns: string[];
  groups: (string | number | null)[][];
  changes: (string | number | null)[][];
  frequencies: Record<string, Record<string, number>>;
  original_data: (string | number)[][];
  results: PredictionResult[];
  accuracy_summary: AccuracySummary;
  error_band: ErrorBandPoint[];
  status: string;
}

interface PredictionProps {
  regions: Region[];
}

// Shape that GenericLineChart expects
interface ChartPoint {
  date: string;
  actual: number | null;
  predicted: number | null;
  upper: number | null;
  lower: number | null;
}

/** Normalize any date string to YYYY-MM-DD so lookups always match */
function normalizeDate(raw: string): string {
  return raw.trim().slice(0, 10);
}

function buildChartData(data: PredictionData, targetMonth: number): ChartPoint[] {
  const monthFilter = targetMonth >= 0 ? targetMonth + 1 : -1;

  // Build predicted price lookup from results
  const predictedMap = new Map<string, number>();
  for (const result of data.results) {
    if (!result.date || Object.keys(result.predictions).length === 0) continue;
    const dateKey = normalizeDate(result.date);
    if (monthFilter > 0) {
      const resultMonth = parseInt(dateKey.slice(5, 7), 10);
      if (resultMonth !== monthFilter) continue;
    }
    const preds = Object.values(result.predictions);
    const prices = preds.filter((p) => p.price != null).map((p) => p.price);
    if (prices.length > 0) {
      const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
      predictedMap.set(dateKey, avg);
    }
  }

  // Build error band lookup
  const bandMap = new Map<string, { upper: number; lower: number }>();
  if (data.error_band) {
    for (const eb of data.error_band) {
      const dateKey = normalizeDate(String(eb.date));
      if (monthFilter > 0) {
        const m = parseInt(dateKey.slice(5, 7), 10);
        if (m !== monthFilter) continue;
      }
      bandMap.set(dateKey, { upper: eb.upper, lower: eb.lower });
    }
  }

  const actualEntries = data.original_data.map((row) => ({
    date: normalizeDate(String(row[0])),
    price: Number(row[1]),
  }));

  const startIdx = Math.max(0, actualEntries.length - 84);
  const windowEntries = actualEntries.slice(startIdx);

  const merged: ChartPoint[] = windowEntries.map((entry) => ({
    date: entry.date,
    actual: entry.price,
    predicted: predictedMap.get(entry.date) ?? null,
    upper: bandMap.get(entry.date)?.upper ?? null,
    lower: bandMap.get(entry.date)?.lower ?? null,
  }));

  const actualDateSet = new Set(windowEntries.map((e) => e.date));
  for (const [date, price] of predictedMap) {
    if (!actualDateSet.has(date) && date >= windowEntries[0]?.date) {
      merged.push({
        date,
        actual: null,
        predicted: price,
        upper: bandMap.get(date)?.upper ?? null,
        lower: bandMap.get(date)?.lower ?? null,
      });
    }
  }

  merged.sort((a, b) => a.date.localeCompare(b.date));
  return merged;
}

export default function PredictionDisplay({ regions }: PredictionProps) {
  const [regionId, setRegionId] = useState(
    regions[0]?.region_id.toString() || "",
  );
  const [data, setData] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [startMonth, setStartMonth] = useState(-1);

  const monthNames = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December",
  ];

  const handleFetch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regionId) return;
    setLoading(true);
    try {
      const res = await fetch(
        // replace with environment variable
        `http://127.0.0.1:8000/predict/${regionId}`,
      );
      const json = await res.json();
      setData(json);
      console.log(json)
    } catch (err) {
      console.error("Failed to fetch data", err);
    } finally {
      setLoading(false);
    }
  };

  const chartData = data ? buildChartData(data, startMonth) : [];

  // Find the last occurrence of the selected month in the data (prediction target)
  const predictionTarget = data
    ? (() => {
        if (startMonth < 0) {
          // All months — show last date in data
          const dates = data.original_data.map((row) => normalizeDate(String(row[0])));
          return dates.length > 0 ? dates[dates.length - 1] : null;
        }
        const monthFilter = startMonth + 1; // 1-indexed
        const matching = data.original_data
          .map((row) => normalizeDate(String(row[0])))
          .filter((d) => parseInt(d.slice(5, 7), 10) === monthFilter);
        return matching.length > 0 ? matching[matching.length - 1] : null;
      })()
    : null;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-10">
      <header className="border-b pb-4">
        <h1 className="text-3xl font-bold tracking-tight">
          Predictions Dashboard
        </h1>
        <p className="text-slate-500">Select a metro area and prediction month</p>
      </header>

      <form
        onSubmit={handleFetch}
        autoComplete="off"
        className="grid grid-cols-1 md:grid-cols-4 gap-6 bg-slate-50 dark:bg-slate-900/50 p-6 rounded-xl border border-slate-200 dark:border-slate-800"
      >
        <div className="flex flex-col gap-2 md:col-span-2">
          <label className="text-xs font-bold uppercase text-slate-500">
            Target Region
          </label>
          <select
            value={regionId}
            onChange={(e) => setRegionId(e.target.value)}
            className="w-full h-10 px-3 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
          >
            <option value="" disabled>
              Select a Metro Area...
            </option>
            {regions.map((r) => (
              <option key={r.region_id} value={r.region_id}>
                {r.region_name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold uppercase text-slate-500">
            Prediction Month
          </label>
          <select
            value={startMonth}
            onChange={(e) => setStartMonth(parseInt(e.target.value))}
            className="w-full h-10 px-3 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          >
            <option value={-1}>All Months</option>
            {monthNames.map((month, index) => (
              <option key={month} value={index}>
                {month}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={loading || !regionId}
            className="w-full bg-blue-600 text-white h-10 rounded-md font-semibold hover:bg-blue-700 disabled:bg-slate-400 transition-colors shadow-sm"
          >
            {loading ? "Calculating..." : "Generate Forecast"}
          </button>
        </div>
      </form>

      {data && (
        <div className="space-y-8">
          {/* Accuracy summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            {[
              { label: "Filter", value: startMonth >= 0 ? monthNames[startMonth] : "All Months", color: "text-blue-600" },
              { label: "Prediction Target", value: predictionTarget ?? "N/A", color: "text-blue-600" },
              { label: "Correct", value: data.accuracy_summary.correct, color: "text-emerald-600" },
              { label: "Wrong", value: data.accuracy_summary.wrong, color: "text-rose-500" },
              { label: "Total", value: data.accuracy_summary.total, color: "text-slate-700 dark:text-slate-200" },
              {
                label: "Accuracy",
                value: `${(data.accuracy_summary.accuracy * 100).toFixed(1)}%`,
                color: data.accuracy_summary.accuracy >= 0.5 ? "text-emerald-600" : "text-rose-500",
              },
              { label: "MSE", value: data.accuracy_summary.mse.toFixed(0), color: "text-amber-500" },
              { label: "RMSE", value: `$${data.accuracy_summary.rmse.toFixed(0)}`, color: "text-amber-500" },     
            ].map(({ label, value, color }) => (
              <div
                key={label}
                className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex flex-col gap-1 shadow-sm"
              >
                <span className="text-xs font-bold uppercase text-slate-400">{label}</span>
                <span className={`text-2xl font-bold font-mono ${color}`}>{value}</span>
              </div>
            ))}
          </div>

          {/* Line chart */}
          <div className="border rounded-lg overflow-hidden bg-white dark:bg-slate-950 shadow-sm p-6">
            <h3 className="font-bold text-sm uppercase text-slate-500 mb-2">
              Price History &amp; Predictions — {data.region_name} ({startMonth >= 0 ? monthNames[startMonth] : "All Months"})
            </h3>
           <GenericLineChart<ChartPoint>
              items={chartData}
              labelKey="date"
              configs={[
                { key: "actual", label: "Actual Price", color: "#5FC3D6" },
                { key: "predicted", label: "Predicted Price", color: "#F97316", dashed: true },
                { key: "upper", label: "Upper Bound (+RMSE)", color: "#F9731640", dashed: true },
                { key: "lower", label: "Lower Bound (-RMSE)", color: "#F9731640", dashed: true },
              ]}
              height="400px"
            />
          </div>

          {/* Changes table */}
          <div className="border rounded-lg overflow-hidden bg-white dark:bg-slate-950 shadow-sm">
            <div className="bg-slate-50 dark:bg-slate-900 h-10">
              <h3 className="px-5 py-2 font-bold text-sm uppercase text-slate-500">
                Changes
              </h3>
            </div>
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-center">
                <thead className="sticky top-0 bg-slate-100 dark:bg-slate-800 z-10">
                  <tr>
                    <th className="p-4 text-xs font-bold text-slate-500">Date</th>
                    <th className="p-4 text-xs font-bold text-slate-500">Difference</th>
                    <th className="p-4 text-xs font-bold text-slate-500 text-right">Direction</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {data.changes.map((row, idx) => (
                    <tr
                      key={idx}
                      className="hover:bg-slate-50 dark:hover:bg-slate-900/50"
                    >
                      <td className="p-4 font-semibold text-slate-700 dark:text-slate-300">
                        {String(row[0])}
                      </td>
                      <td className="p-4 font-mono text-slate-700 dark:text-slate-300">
                        {typeof row[1] === "number" ? row[1].toFixed(2) : String(row[1])}
                      </td>
                      <td className="p-4 text-right">
                        <span
                          className={`inline-flex items-center justify-center w-10 text-[10px] py-1 rounded-full font-bold ${
                            row[2] === "U"
                              ? "bg-emerald-100 text-emerald-700"
                              : "bg-rose-100 text-rose-700"
                          }`}
                        >
                          {row[2] === "U" ? "Up" : "Down"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Frequencies table */}
          <div className="border rounded-lg overflow-hidden bg-white dark:bg-slate-950 shadow-sm">
            <div className="bg-slate-50 dark:bg-slate-900 h-10">
              <h3 className="px-5 py-2 font-bold text-sm uppercase text-slate-500">
                Frequencies
              </h3>
            </div>
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-center">
                <thead className="sticky top-0 bg-slate-100 dark:bg-slate-800 z-10">
                  <tr>
                    <th className="p-4 text-xs font-bold text-slate-500">Group</th>
                    <th className="p-4 text-xs font-bold text-slate-500">Pattern</th>
                    <th className="p-4 text-xs font-bold text-slate-500 text-right">Count</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {Object.entries(data.frequencies).flatMap(([group, patternCounts]) =>
                    Object.entries(patternCounts).map(([pattern, count]) => (
                      <tr
                        key={`${group}-${pattern}`}
                        className="hover:bg-slate-50 dark:hover:bg-slate-900/50"
                      >
                        <td className="p-4 font-semibold text-slate-700 dark:text-slate-300">
                          {group}
                        </td>
                        <td className="p-4 font-mono text-blue-500 tracking-[0.3em] uppercase">
                          {pattern}
                        </td>
                        <td className="p-4 font-mono text-slate-700 dark:text-slate-300 text-right">
                          {count}
                        </td>
                      </tr>
                    )),
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}