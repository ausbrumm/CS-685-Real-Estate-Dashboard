"use client";

import { useState, useMemo } from "react";
import { MetroRecord, Region } from "@/lib/types";
import { MyBarChart } from "./BarChart";
import { useRouter } from "next/navigation";

interface HistoricalDashboardProps {
  initialProperties: MetroRecord[];
  regions: Region[];
  states: string[];
  years: number[];
  initialRegionId: string;
  initialYear: string;
}

export default function YearlyHistoricalDashboard({
  initialProperties,
  regions,
  states,
  years,
  initialRegionId,
  initialYear,
}: HistoricalDashboardProps) {
  const router = useRouter();

  const activeRegion = regions.find(
    (r) => String(r.region_id) === String(initialRegionId),
  );

  // States
  const [selectedState, setSelectedState] = useState(
    activeRegion?.state_name || states[0],
  );
  const [selectedYear, setSelectedYear] = useState(initialYear);
  const [selectedRegionId, setSelectedRegionId] = useState(initialRegionId);

  // filter based on the selected state, useMemo so it caches between renders so it quits erroring
  const availableRegions = useMemo(() => {
    return regions.filter((r) => r.state_name === selectedState);
  }, [regions, selectedState]);

  const updateFilters = (regionId: string, year: number) => {
    // Only push if values actually changed to prevent loops
    const params = new URLSearchParams();
    params.set("regionId", regionId);
    params.set("year", String(year));

    // update url to force re-render to fetch new data
    router.push(`/?${params.toString()}`, { scroll: false });
  };

  // Handlers

  const handleStateChange = (newState: string) => {
    setSelectedState(newState);
    // When state changes, pick a valid region in that new state to stop mismatched data
    const firstRegionInNewState = regions.find(
      (r) => r.state_name === newState,
    );
    if (firstRegionInNewState) {
      const newId = String(firstRegionInNewState.region_id);
      setSelectedRegionId(newId);
      updateFilters(newId, Number(selectedYear));
    }
  };

  const handleRegionChange = (newRegionId: string) => {
    // set changed region
    setSelectedRegionId(newRegionId);
    updateFilters(newRegionId, Number(selectedYear));
  };

  const handleYearChange = (newYear: number) => {
    // set changed year
    setSelectedYear(String(newYear));
    updateFilters(selectedRegionId, newYear);
  };

  return (
    <div className="space-y-4 p-4">
      <div className="flex gap-4">
        {/* State selector */}
        <label className="block">
          <span className="text-gray-700">Pick a State:</span>
          <select
            value={selectedState}
            onChange={(e) => {
              handleStateChange(e.target.value);
            }}
            className="block w-full mt-1 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          >
            {states.map((state) => (
              <option key={state} value={state}>
                {state}
              </option>
            ))}
          </select>
        </label>

        {/* Region selector (Dependent on State) */}
        <label className="block">
          <span className="text-gray-700">Pick a Region:</span>
          <select
            value={selectedRegionId}
            onChange={(e) => handleRegionChange(e.target.value)}
            className="block w-full mt-1 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          >
            {availableRegions.map((item) => (
              <option key={item.region_id} value={item.region_id}>
                {item.region_name}
              </option>
            ))}
          </select>
        </label>

        {/* Year selector */}
        <label className="block">
          <span className="text-gray-700">Pick a Year:</span>
          <select
            value={selectedYear}
            onChange={(e) => handleYearChange(Number(e.target.value))}
            className="block w-full mt-1 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </label>
      </div>

      <MyBarChart
        data={initialProperties}
        xProp="date"
        yProp="avg_cost"
        label={`Prices in ${selectedYear} (${activeRegion?.region_name || "Unknown"})`}
      />
    </div>
  );
}
