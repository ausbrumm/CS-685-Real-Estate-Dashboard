import { MetroRecord, Region } from "@/lib/types";
import pool from "../../lib/db/db";
import YearlyHistoricalDashboard from "@/components/YearlyHistoricalDashboard";
import MoYHistoricalDashboard from "@/components/MoYHistoricalDashboard";
import StateHistoricalDashboard from "@/components/StateHistoricalDashboard";

type Props = {
  searchParams: { [key: string]: string | string[] | undefined };
};

export default async function Historical({ searchParams }: Props) {
  // setup search params with defaults
  const params = await searchParams;
  const selectedRegionId = String(params.regionId || "394463");
  const selectedYear = String(params.year || "2024");

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

  const selectedRegion = regions.find(
    (r) => String(r.region_id) === selectedRegionId,
  );

  const selectedState = selectedRegion?.state_name || "IL";
  console.log(selectedState);
  const stateWideResults = await pool.query<MetroRecord>(
    `SELECT mus.date, mus.avg_cost, mus.region_id
     FROM metro_us mus 
     JOIN regions r ON mus.region_id = r.region_id 
     WHERE r.state_name = $1 
     ORDER BY date ASC`,
    [selectedState],
  );

  console.log(selectedRegionId);
  const specificRegionData = stateWideResults.rows.filter(
    (r) => String(r.region_id) === selectedRegionId,
  );

  return (
    <div>
      <div className="flex flex-col items-center jusify-center gap-[2rem]">
        <h2 className="">Single Year Region Data</h2>
        <YearlyHistoricalDashboard
          initialProperties={specificRegionData.filter(
            (x) => new Date(x.date).getFullYear() === Number(selectedYear),
          )}
          states={states}
          regions={regions}
          years={years}
          initialRegionId={selectedRegionId}
          initialYear={selectedYear}
        />
      </div>
      <div>
        <MoYHistoricalDashboard allData={specificRegionData} />
      </div>
      {/* <div>
        <StateHistoricalDashboard allData={stateWideResults.rows} />
      </div> */}
    </div>
  );
}
