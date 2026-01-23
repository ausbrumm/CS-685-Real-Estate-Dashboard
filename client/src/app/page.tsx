import { MyBarChart } from "../components/BarChart";
import pool from "../lib/db/db";

export default async function Home() {
  const result = await pool.query<Property>("SELECT * FROM properties");
  const properties = result.rows;
  return (
    <div>
      {properties.map((property: Property) => (
        // usage is now safe and autocompletes!
        <div key={property.id}>{property.address}</div>
      ))}
      <div className="w-[50%]">
        <MyBarChart properties={properties} />
      </div>
    </div>
  );
}
