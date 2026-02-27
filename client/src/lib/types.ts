export interface Property {
  id: number;
  address: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  listingDate: Date;
  source: string;
}

export interface MetroRecord {
  id: number;
  region_id: number;
  size_rank: number;
  region_name: string;
  state_name: string;
  date: Date;
  avg_cost: number;
}

export interface Region {
  region_id: number;
  region_name: string;
  state_name: string;
}

export interface ChartProps<T1, T2> {
  xLabels: T1[];
  yLabels: T2[];
}
