import { MetroRecord, Region } from "@/lib/types";
import pool from "../lib/db/db";
import YearlyHistoricalDashboard from "@/components/YearlyHistoricalDashboard";
import MoYHistoricalDashboard from "@/components/MoYHistoricalDashboard";

type Props = {
  searchParams: { [key: string]: string | string[] | undefined };
};

export default async function Home({ searchParams }: Props) {
  // setup search params with defaults
  const params = await searchParams;
  const selectedRegionId =
    typeof params.regionId === "string" ? params.regionId : "394463";
  const selectedYear = typeof params.year === "string" ? params.year : "2024";
  const metroResults = await pool.query<MetroRecord>(
    "SELECT * FROM metro_us mus join regions r on mus.region_id = r.region_id WHERE mus.region_id = $1 ORDER BY date ASC",
    [selectedRegionId],
  );

  // fetch filters
  const yearResults = await pool.query<{ year: number }>(
    "SELECT DISTINCT EXTRACT(YEAR from date) as year FROM metro_us",
  );
  const regionResults = await pool.query<Region>("SELECT * FROM regions");

  // fetch and map data for regions, states, and years
  const regions = regionResults.rows;
  const states = [...new Set(regions.map((item) => item.state_name))].sort();
  const years = yearResults.rows
    .map((item) => Number(item.year))
    .sort((a, b) => b - a);

  return (
    <div>
      <div className="flex flex-col items-center jusify-center gap-[2rem]">
        <h2 className="">Single Year Region Data</h2>
        <YearlyHistoricalDashboard
          initialProperties={metroResults.rows.filter(
            (x) => x.date.getFullYear() === Number(selectedYear),
          )}
          states={states}
          regions={regions}
          years={years}
          initialRegionId={selectedRegionId}
          initialYear={selectedYear}
        />
      </div>
      <div>
        <MoYHistoricalDashboard allData={metroResults.rows} />
      </div>
    </div>
  );
}
