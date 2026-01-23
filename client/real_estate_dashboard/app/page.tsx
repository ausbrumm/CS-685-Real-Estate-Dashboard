import { MyBarChart } from "../components/BarChart";
import pool from "../db/db";

export default async function Home() {
  const result = await pool.query<Property>("SELECT * FROM properties");
  const properties = result.rows;
  return (
    <div>
      {properties.map((property: Property) => (
        // usage is now safe and autocompletes!
        <div key={property.id}>{property.address}</div>
      ))}
      <MyBarChart properties={properties} />
    </div>
  );
}
