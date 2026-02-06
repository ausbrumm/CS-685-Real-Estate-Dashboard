# get_individual_listings.py
import asyncio
import csv
from postgres_connector import AsyncPostgresConnector
from psycopg import sql
from datetime import datetime

TSV_FILE = "./realestateUS.tsv"
TABLE_NAME = "property_listings"
CHUNK_SIZE = 10000

# Postgres table column names
COLUMNS = [
    "address", "city", "state", "zip", "sqft", "beds", "baths",
    "built_year", "property_type", "status", "price", "agent",
    "broker", "lat", "lon", "parcel", "last_change"
]

async def insert_batch(connector, batch):
    """Insert a batch of rows safely using ON CONFLICT to avoid duplicates."""
    columns_sql = sql.SQL(", ").join(sql.Identifier(c) for c in COLUMNS)
    values_sql = sql.SQL(", ").join(sql.Placeholder() * len(COLUMNS))
    
    query = sql.SQL("""
        INSERT INTO {table} ({columns})
        VALUES ({values})
        ON CONFLICT (address, city, state, zip) DO NOTHING
    """).format(
        table=sql.Identifier(TABLE_NAME),
        columns=columns_sql,
        values=values_sql
    )
    
    await connector.execute_many(query, batch)

async def load_tsv_to_postgres():
    connector = AsyncPostgresConnector()
    await connector.connect()
    
    try:
        with open(TSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            batch = []
            for i, row in enumerate(reader, 1):
                # Convert values, handling empty strings
                last_change = None
                if row.get("last_change"):
                    try:
                        last_change = datetime.strptime(row["last_change"], "%Y-%m-%d").date()
                    except ValueError:
                        last_change = None  # invalid dates become NULL
                
                batch.append((
                    row["address"],
                    row["city"],
                    row["state"],
                    row["zip"],
                    int(row["sqft"]) if row.get("sqft") else None,
                    int(row["beds"]) if row.get("beds") else None,
                    int(row["baths"]) if row.get("baths") else None,
                    int(row["built"]) if row.get("built") else None,
                    row["type"],
                    row["status"],
                    float(row["price"]) if row.get("price") else None,
                    row["agent"],
                    row["broker"],
                    float(row["lat"]) if row.get("lat") else None,
                    float(row["lon"]) if row.get("lon") else None,
                    row["parcel"],
                    last_change
                ))
                
                # Insert in chunks
                if i % CHUNK_SIZE == 0:
                    await insert_batch(connector, batch)
                    print(f"Inserted {i} rows")
                    batch.clear()
            
            # Insert remaining rows
            if batch:
                await insert_batch(connector, batch)
                print(f"Inserted total {i} rows")
    
    finally:
        await connector.disconnect()

if __name__ == "__main__":
    asyncio.run(load_tsv_to_postgres())
