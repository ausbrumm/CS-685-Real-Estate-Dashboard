"use client";

import { Region } from "@/lib/types";
import React, { useState } from "react";

interface PredictionData {
  region_id: number;
  region_name: string;
  patterns: Record<string, string>;
  probabilities: Record<string, number>;
  subsets: Record<string, string>;
  counts: Record<string, number>;
  status: string;
}

interface PredictionProps {
  regions: Region[];
}

export default function PredictionDisplay({ regions }: PredictionProps) {
  const [regionId, setRegionId] = useState(
    regions[0]?.region_id.toString() || "",
  );
  const [data, setData] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [startMonth, setStartMonth] = useState(0);
  const endMonth = startMonth + 3;

  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const handleFetch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regionId) return;

    setLoading(true);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/predict/${regionId}?start_month=${startMonth}&end_month=${endMonth}`,
      );
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error("Failed to fetch data", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-10">
      <header className="border-b pb-4">
        <h1 className="text-3xl font-bold tracking-tight">
          Predictions Dashboard
        </h1>
        <p className="text-slate-500">Select a metro area</p>
      </header>

      <form
        onSubmit={handleFetch}
        className="grid grid-cols-1 md:grid-cols-4 gap-6 bg-slate-50 dark:bg-slate-900/50 p-6 rounded-xl border border-slate-200 dark:border-slate-800"
      >
        {/*Selector for region*/}
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
            Analysis Start Month
          </label>
          <select
            value={startMonth}
            onChange={(e) => setStartMonth(parseInt(e.target.value))}
            className="w-full h-10 px-3 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          >
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
          <div className="lg:col-span-3 border rounded-lg overflow-hidden bg-white dark:bg-slate-950 shadow-sm">
            <div className="bg-slate-50 dark:bg-slate-900 h-10">
              <h3 className="px-5 py-2 font-bold text-sm uppercase text-slate-500 align-">
                Counts
              </h3>
            </div>
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-center">
                <thead className="sticky top-0 bg-slate-100 dark:bg-slate-800 z-10">
                  <tr>
                    <th className="p-4 text-xs font-bold text-slate-500">
                      Fiscal Year
                    </th>
                    <th className="p-4 text-xs font-bold text-slate-500">
                      Percentage
                    </th>
                    <th className="p-4 text-xs font-bold text-slate-500 text-right">
                      Count
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y-1 divide-slate-100 dark:divide-slate-800">
                  {Object.entries(data.probabilities).map(
                    ([pattern, probability]) => (
                      <tr
                        key={pattern}
                        className="hover:bg-slate-50 dark:hover:bg-slate-900/50"
                      >
                        <td className="p-4 font-semibold text-slate-700 dark:text-slate-300">
                          {pattern}
                        </td>
                        <td className="p-4 font-mono text-blue-500 uppercase">
                          {new Intl.NumberFormat("en-US", {
                            style: "percent",
                            maximumFractionDigits: 2,
                          }).format(probability)}
                        </td>
                        <td className="p-4 font-mono text-blue-500 uppercase">
                          {data.counts[pattern]}
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="lg:col-span-3 border rounded-lg overflow-hidden bg-white dark:bg-slate-950 shadow-sm mt-20">
            <div className="bg-slate-50 dark:bg-slate-900 h-10">
              <h3 className="px-5 py-2 font-bold text-sm uppercase text-slate-500 align-">
                Patterns
              </h3>
            </div>
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-center">
                <thead className="sticky top-0 bg-slate-100 dark:bg-slate-800 z-10">
                  <tr>
                    <th className="p-4 text-xs font-bold text-slate-500">
                      Fiscal Year
                    </th>
                    <th className="p-4 text-xs font-bold text-slate-500">
                      Pattern Sequence
                    </th>
                    <th className="p-4 text-xs font-bold text-slate-500 text-right">
                      Prediction
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y-1 divide-slate-100 dark:divide-slate-800">
                  {Object.entries(data.subsets)
                    .reverse()
                    .map(([year, trend]) => (
                      <tr
                        key={year}
                        className="hover:bg-slate-50 dark:hover:bg-slate-900/50"
                      >
                        <td className="p-4 font-semibold text-slate-700 dark:text-slate-300">
                          {year}
                        </td>
                        <td className="p-4 font-mono text-blue-500 tracking-[0.3em] uppercase">
                          {trend}
                        </td>
                        <td className="p-4 text-right">
                          <span
                            className={`inline-flex items-center justify-center w-14 text-[10px] py-1 rounded-full font-bold ${trend.includes("U") ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}
                          >
                            {trend.split("U").length > trend.split("D").length
                              ? "Up"
                              : "Down"}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
