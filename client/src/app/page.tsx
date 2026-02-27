import { MetroRecord, Region } from "@/lib/types";
import pool from "../lib/db/db";
import YearlyHistoricalDashboard from "@/components/YearlyHistoricalDashboard";
import MoYHistoricalDashboard from "@/components/MoYHistoricalDashboard";

type Props = {
  searchParams: { [key: string]: string | string[] | undefined };
};

export default async function Home({ searchParams }: Props) {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center p-6">
      <div className="w-full text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-3xl md:text-3xl font-bold">
            CS 685 - Real Estate Data Dashboards
          </h1>
          <div className="flex flex-col md:flex-row items-center justify-center gap-2 md:gap-3">
            <p className="px-3 py-1">Authors: Austin Brummett, David Lakes</p>
            <p className="px-3 py-1">Professor: Dr. Arash Raifey</p>
          </div>
        </div>

        <hr className="border-border w-0 mx-auto h-10" />

        <section className="text-white p-8 md:p-12 rounded-3xl shadow-xl">
          <div className="max-w-3xl mx-auto space-y-20">
            <p className="text-sm md:text-xl leading-relaxed">
              The purpose of this project is to analyze real estate data and
              make a prediction to estimate the cost of housing in a particular
              state or region within a state. The data for this web app comes
              from Zillow.com. I have no idea what to write here right now.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
