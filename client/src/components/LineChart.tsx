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
  configs, // each set of data
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
    tension: 0.3,
    pointRadius: 3,
  }));

  const defaultOptions: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
    ...options, 
  };

  return (
    <div style={{ height }} className="mt-[20px] w-full">
      <Line 
        data={{ labels: chartLabels, datasets }} 
        options={defaultOptions} 
      />
    </div>
  );
}