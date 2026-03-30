"use client";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

interface DatasetConfig<T> {
  key: keyof T;
  label: string;
  color?: string;
  dashed?: boolean;
}

interface GenericLineChartProps<T> {
  items: T[];
  labelKey: keyof T;
  configs: DatasetConfig<T>[];
  options?: ChartOptions<"line">;
  height?: string;
}

export function GenericLineChart<T>({
  items,
  labelKey,
  configs,
  options,
  height = "400px",
}: GenericLineChartProps<T>) {
  const chartLabels = items.map((item) => String(item[labelKey]));

  const datasets = configs.map((config) => ({
    label: config.label,
    data: items.map((item) => item[config.key] as unknown as number),
    backgroundColor: config.color || "#5FC3D6",
    borderColor: config.color || "#5FC3D6",
    borderWidth: 2,
    borderDash: config.dashed ? [6, 3] : [],
    tension: 0.3,
    pointRadius: 2,
    pointHoverRadius: 5,
    spanGaps: true,
  }));

  const defaultOptions: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        position: "top" as const,
        labels: {
          usePointStyle: true,
          pointStyleWidth: 16,
          padding: 20,
        },
      },
      tooltip: {
        callbacks: {
          label: (ctx) =>
            `${ctx.dataset.label}: $${Number(ctx.parsed.y).toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
        },
      },
    },
    scales: {
      x: {
        ticks: {
          maxTicksLimit: 12,
          maxRotation: 45,
        },
      },
      y: {
        beginAtZero: false,
        ticks: {
          callback: (value) =>
            `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
        },
      },
    },
    // caller-supplied options win
    ...options,
  };

  return (
    <div style={{ height }} className="mt-5 w-full">
      <Line data={{ labels: chartLabels, datasets }} options={defaultOptions} />
    </div>
  );
}