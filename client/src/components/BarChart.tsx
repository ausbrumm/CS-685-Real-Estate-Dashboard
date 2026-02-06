// components/BarChart.tsx
"use client";
import { Bar } from "react-chartjs-2";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

import { Property } from "@/lib/types";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
);

interface BarChartProps<T extends object> {
  data: T[];
  xProp: keyof T;
  yProp: keyof T;
  label?: string;
}

// date format
// 26-01-01
const options: Intl.DateTimeFormatOptions = {
  year: "2-digit",
  month: "numeric",
  day: "numeric",
};

function formatLabel(value: unknown): string {
  if (value instanceof Date) {
    return value.toLocaleDateString(undefined, options);
  }
  return String(value);
}

export function MyBarChart<T extends object>({
  data,
  xProp,
  yProp,
  label = "Property Price",
}: BarChartProps<T>) {
  // Create labels for each bar
  // General bar chart
  const chartLabels = data.map((p) => formatLabel(p[xProp]));
  const chartData = data.map((p) => p[yProp]);
  console.log(data);
  return (
    <div className="mt-[20px] w-full">
      <Bar
        data={{
          labels: chartLabels,
          datasets: [
            {
              label: label,
              data: chartData,
              backgroundColor: "#5FC3D6",
              borderColor: "#5FC3D6",
              borderWidth: 1,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,

          scales: {
            y: {
              beginAtZero: true,
            },
          },
        }}
      />
    </div>
  );
}
