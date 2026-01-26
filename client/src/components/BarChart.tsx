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

type MyChartProps = {
  properties: Property[];
};

// TODO: Make this more generic so it can be a reusable component, maybe pass in properties AND the keys of importance?
//       add options for some of the other values for config?

export function MyBarChart({ properties }: MyChartProps) {
  // Sort properties by price (optional, but good for visualization)
  const sortedProperties = [...properties].sort((a, b) => a.price - b.price);

  // Create labels for each bar (e.g., the address)
  // The X-axis needs a label for every single bar you draw
  const chartLabels = sortedProperties.map((p) => p.address);
  const chartData = sortedProperties.map((p) => p.price);

  return (
    <div className="mt-[20px] w-full">
      <Bar
        data={{
          labels: chartLabels,
          datasets: [
            {
              label: "Property Price", // This is the legend title
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
