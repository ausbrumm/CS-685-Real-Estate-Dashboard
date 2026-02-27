"use client";

import { Region } from "@/lib/types";
import React, { useState } from "react";
import { GenericLineChart } from "@/components/LineChart";

interface PredictionData {
  region_id: number;
  region_name: string;
  patterns: string[];
  groups: (string | number | null)[][];
  changes: (string | number | null)[][];
  frequencies: Record<string, Record<string, number>>;
  original_data: (string | number)[][];
  results: (string | number | null)[][][];
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
}

function buildChartData(data: PredictionData): ChartPoint[] {
  const actualMap = new Map<string, number>();
  for (const row of data.original_data) {
    actualMap.set(String(row[0]), Number(row[1]));
  }

  const predictedMap = new Map<string, number>();

  for (let i = 0; i < data.results.length; i++) {
    const row = data.results[i];
    for (let j = 3; j < row.length; j++) {
      const entry = row[j] as (string | number | null)[];
      if (!entry) continue;

      const magnitude = entry[1];
      const monthOffset = Number(entry[2]); // 0, 4, or 8
      console.log("Row:" + row[j]);

      const targetIdx =
        data.original_data.length -
        data.results.length +
        i +
        monthOffset / 4 -
        1;
      const dateKey = String(
        data.original_data[
          Math.min(targetIdx, data.original_data.length - 1)
        ]?.[0],
      );

      if (dateKey && magnitude !== null) {
        const actualMagnitude: number = actualMap.get(dateKey) ?? 0;
        predictedMap.set(dateKey, actualMagnitude + Number(magnitude));
      }
    }
  }

  const allDates = [
    ...new Set([...actualMap.keys(), ...predictedMap.keys()]),
  ].sort();
  return allDates
    .filter((date) => actualMap.has(date) && predictedMap.has(date))
    .map((date) => ({
      date,
      actual: actualMap.get(date)!,
      predicted: predictedMap.get(date)!,
    }));
}

export default function PredictionDisplay({ regions }: PredictionProps) {
  const [regionId, setRegionId] = useState(
    regions[0]?.region_id.toString() || "",
  );
  const [data, setData] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [startMonth, setStartMonth] = useState(0);

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
        `http://127.0.0.1:8000/predict/${regionId}?start_month=${startMonth}`,
      );
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error("Failed to fetch data", err);
    } finally {
      setLoading(false);
    }
  };

  const chartData = data ? buildChartData(data) : [];

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
          {/* 
          <div className="border rounded-lg overflow-hidden bg-white dark:bg-slate-950 shadow-sm p-6">
            <h3 className="font-bold text-sm uppercase text-slate-500 mb-2">
              Price History &amp; Predictions — {data.region_name}
            </h3>
            <GenericLineChart<ChartPoint>
              items={chartData}
              labelKey="date"
              configs={[
                { key: "actual", label: "Actual Price", color: "#5FC3D6" },
                {
                  key: "predicted",
                  label: "Predicted Price",
                  color: "#F97316",
                },
              ]}
              height="400px"
            />
          </div>          */}


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
                    <th className="p-4 text-xs font-bold text-slate-500">
                      Date
                    </th>
                    <th className="p-4 text-xs font-bold text-slate-500">
                      Difference
                    </th>
                    <th className="p-4 text-xs font-bold text-slate-500 text-right">
                      Direction
                    </th>
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
                        {typeof row[1] === "number"
                          ? row[1].toFixed(2)
                          : String(row[1])}
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
                    <th className="p-4 text-xs font-bold text-slate-500">
                      Group
                    </th>
                    <th className="p-4 text-xs font-bold text-slate-500">
                      Pattern
                    </th>
                    <th className="p-4 text-xs font-bold text-slate-500 text-right">
                      Count
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {Object.entries(data.frequencies).flatMap(
                    ([group, patternCounts]) =>
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
