import asyncio
from io import StringIO

import httpx
import pandas as pd

from infrastructure.postgres_connector import AsyncPostgresConnector


ZILLOW_URL = (
    "https://files.zillowstatic.com/research/public_csvs/"
    "zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)


async def fetch_zillow_df() -> pd.DataFrame:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(ZILLOW_URL)
        r.raise_for_status()

    return pd.read_csv(StringIO(r.text))


def transform_zillow_df(df: pd.DataFrame) -> list[tuple]:
    """
    Transform Zillow CSV into rows that match zillow_data table
    """

    # Only columns that start with a digit are dates
    date_columns = [c for c in df.columns if c[0].isdigit()]

    df_long = df.melt(
        id_vars=["RegionID", "SizeRank", "RegionName", "StateName"],
        value_vars=date_columns,
        var_name="date",
        value_name="avg_cost",
    )

    # Parse dates safely (Zillow uses YYYY-MM-DD)
    df_long["date"] = pd.to_datetime(df_long["date"], errors="raise").dt.date

    # Drop missing values
    df_long = df_long.dropna(subset=["avg_cost"])

    # Generate IDs (required because DB does NOT auto-generate)
    df_long["id"] = range(1, len(df_long) + 1)

    # Order columns to match SQL table
    df_long = df_long[
        ["id", "RegionID", "SizeRank", "RegionName", "StateName", "date", "avg_cost"]
    ]

    return list(df_long.itertuples(index=False, name=None))


async def insert_zillow_data(db: AsyncPostgresConnector, rows: list[tuple]):
    columns = [
        "id",
        "region_id",
        "size_rank",
        "region_name",
        "state_name",
        "date",
        "avg_cost",
    ]

    await db.copy_from("zillow_data", rows, columns)


async def main():
    df = await fetch_zillow_df()
    print("Fetched Zillow data")

    rows = transform_zillow_df(df)
    print(f"Prepared {len(rows):,} rows")

    async with AsyncPostgresConnector(
        host="localhost",
        port=5432,
        dbname="real_estate_db",
        user="realestate_user",
        password="devpassword",
    ) as db:
        print("Connected to Postgres")
        await insert_zillow_data(db, rows)
        print("Inserted rows into zillow_data")


if __name__ == "__main__":
    asyncio.run(main())
