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

export default function MoYHistoricalDashboard({
  allData,
}: DashboardGridProps) {
  const monthlyDataBuckets = useMemo(() => {
    // create monthly buckets
    const buckets: MetroRecord[][] = Array.from({ length: 12 }, () => []);

    // populate data based on records for each month
    allData.forEach((record) => {
      const dateObj = new Date(record.date);
      const monthIndex = dateObj.getMonth(); // 0 = Jan, 11 = Dec
      buckets[monthIndex].push(record);
    });

    return buckets;
  }, [allData]);

  return (
    <div className="p-6 space-y-6 min-h-screen">
      <div className="p-4 rounded-lg shadow flex flex-wrap gap-6 items-center justify-center">
        <h1 className="text-xl font-bold text-white-800 mr-auto">
          Year-over-Year Analysis
        </h1>
      </div>

      {/* 12 month layout */}
      <div className="grid grid-cols-1 md:grid-cols-1 lg:grid-cols-2 xl:grid-cols-2 gap-6">
        {monthlyDataBuckets.map((monthData, index) => (
          <div key={index} className="p-4 rounded-lg shadow border">
            <h3 className="text-lg font-semibold text-white-700 mb-2 text-center">
              {MONTH_LABELS[index]}
            </h3>
            {monthData.length > 0 ? (
              <div className="h-40 w-full">
                <MyBarChart
                  data={monthData}
                  xProp="date"
                  yProp="avg_cost"
                  label=""
                />
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400 italic">
                No Data
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
