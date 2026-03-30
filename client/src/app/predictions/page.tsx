import { Region } from "@/lib/types";
import pool from "../../lib/db/db";
import PredictionDisplay from "@/components/PredictionDisplay";

type Props = {
  searchParams: { [key: string]: string | string[] | undefined };
};

export default async function Predictions({ searchParams }: Props) {
  // setup search params with defaults
  const params = await searchParams;
  const selectedRegionId = String(params.regionId || "394463");

  // fetch filters
  const yearResults = await pool.query<{ year: number }>(
    "SELECT DISTINCT EXTRACT(YEAR from date) as year FROM public.zillow_data WHERE region_id = $1", [selectedRegionId]
  );
  console.log(yearResults.rows.map((item) => Number(item.year)).sort((a, b) => a-b))
  const regionResults = await pool.query<Region>("SELECT * FROM regions");

  // fetch and map data for regions, states, and years
  const regions = regionResults.rows;
  const years = yearResults.rows
    .map((item) => Number(item.year))
    .sort((a, b) => a-b);

  return (
    <div>
      <div className="flex flex-col items-center jusify-center gap-[2rem]">
        <h2 className="">Prediction Information</h2>
        <PredictionDisplay regions={regions} years={years.slice(7).sort((a, b) => b-a)}/>
      </div>

    </div>
  );
}
