"use client";

import { useMemo } from "react";
import { MetroRecord } from "@/lib/types";
import { MyBarChart } from "./BarChart";

// Labels for 12 month grids
const MONTH_LABELS = [
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

interface DashboardGridProps {
  allData: MetroRecord[];
}

const formatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

export default function StateHistoricalDashboard({
  allData,
}: DashboardGridProps) {
  // Calculate the average cost per month across all regions for a given state
  const stateMonthlyAverages = useMemo(() => {
    const buckets: number[][] = Array.from({ length: 12 }, () => []);

    allData.forEach((record) => {
      const dateObj = new Date(record.date);
      const monthIndex = dateObj.getMonth();

      const cost =
        typeof record.avg_cost === "string"
          ? parseFloat(record.avg_cost)
          : record.avg_cost;
      if (!isNaN(cost) && cost !== null) {
        buckets[monthIndex].push(cost);
      }
    });

    return buckets.map((costs, index) => {
      const average =
        costs.length > 0
          ? costs.reduce((sum, val) => sum + val, 0) / costs.length
          : 0;

      return {
        month: MONTH_LABELS[index],
        avg_cost: parseFloat(average.toFixed(2)),
      };
    });
  }, [allData]);

  return (
    <div className="mt-10 p-6 space-y-6">
      <div className="p-4 rounded-lg shadow flex flex-wrap gap-6 items-center justify-center">
        <h1 className="text-xl font-bold mr-auto">
          State-Wide Monthly Averages
        </h1>
        <p className="text-sm text-muted-foreground">
          Aggregated across {allData.length} total records
        </p>
      </div>

      <div className="p-6 rounded-lg shadow border bg-card">
        <div className="w-full h-full">
          <MyBarChart
            data={stateMonthlyAverages}
            xProp="month"
            yProp="avg_cost"
            label="Avg Cost ($)"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {stateMonthlyAverages.map((item) => (
          <div key={item.month} className="p-3 border rounded text-center">
            <div className="text-xs font-semibold text-gray-500 uppercase">
              {item.month}
            </div>
            <div className="text-lg font-bold">
              {formatter.format(item.avg_cost)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
