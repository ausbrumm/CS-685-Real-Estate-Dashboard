# async_ingest.py
import csv
import asyncio
import logging
from io import StringIO
import requests

from postgres_connector import AsyncPostgresConnector
from psycopg import sql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ZILLOW_URL = (
    "https://files.zillowstatic.com/research/public_csvs/"
    "zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)

REGION_INSERT_SQL = """
INSERT INTO regions (region_id, region_name, state_name)
VALUES (%s, %s, %s)
ON CONFLICT (region_id) DO NOTHING;
"""

METRO_COPY_COLUMNS = ["region_id", "size_rank", "date", "avg_cost"]


def fetch_raw_data() -> list[dict]:
    """Fetch Zillow CSV and convert wide format to long format."""
    logger.info("Fetching Zillow data...")
    resp = requests.get(ZILLOW_URL)
    resp.raise_for_status()  # make sure HTTP errors raise exceptions

    reader = csv.DictReader(StringIO(resp.text))
    rows = []

    for row in reader:
        region_id = int(row["RegionID"])
        region_name = row["RegionName"]
        state_name = row["StateName"]
        size_rank = int(row["SizeRank"])

        # Loop over all monthly columns (skip metadata)
        for date_str, avg_cost_str in row.items():
            if date_str in ("RegionID", "RegionName", "RegionType", "StateName", "SizeRank"):
                continue
            try:
                avg_cost = float(avg_cost_str) if avg_cost_str else None
                rows.append({
                    "region_id": region_id,
                    "region_name": region_name,
                    "state_name": state_name,
                    "size_rank": size_rank,
                    "date": date_str,  # YYYY-MM-DD format from CSV
                    "avg_cost": avg_cost
                })
            except ValueError as e:
                logger.warning(f"Skipping cell {date_str} for region {region_name}: {e}")

    logger.info(f"Fetched {len(rows)} rows")
    return rows



def prepare_metro_rows(raw_rows: list[dict]) -> list[tuple]:
    """Prepare metro_us rows for COPY ingestion."""
    return [
        (
            r["region_id"],
            r["size_rank"],
            r["date"],
            r["avg_cost"]
        )
        for r in raw_rows
    ]
def prepare_region_rows(raw_rows: list[dict]) -> list[tuple]:
    """
    Deduplicate regions and prepare tuples for insertion into the `regions` table.

    Each tuple is: (region_id, region_name, state_name)
    """
    regions = {}
    for r in raw_rows:
        # Keep only one entry per region_id
        regions[r["region_id"]] = (
            r["region_id"],
            r["region_name"],
            r["state_name"]
        )
    return list(regions.values())



async def main():
    raw_rows = fetch_raw_data()
    region_rows = prepare_region_rows(raw_rows)
    metro_rows = prepare_metro_rows(raw_rows)

    connector = AsyncPostgresConnector()
    await connector.connect()

    try:
        # Insert regions
        logger.info(f"Inserting {len(region_rows)} regions...")
        await connector.execute_many(REGION_INSERT_SQL, region_rows)
        logger.info("Regions inserted successfully.")

        # Bulk insert metro_us using COPY
        logger.info(f"Inserting {len(metro_rows)} metro_us rows via COPY...")
        copy_query = sql.SQL("COPY {} ({}) FROM STDIN").format(
            sql.Identifier("metro_us"),
            sql.SQL(", ").join(sql.Identifier(c) for c in METRO_COPY_COLUMNS)
        )
        async with connector._get_connection() as conn:
            async with conn.cursor() as cur:
                async with cur.copy(copy_query) as copy:
                    for row in metro_rows:
                        await copy.write_row(row)
        await connector.disconnect()
        logger.info("Metro_us data inserted successfully.")

    except Exception as e:
        logger.exception(f"Error during ingestion: {e}")
        await connector.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
