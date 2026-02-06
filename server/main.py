import asyncio
from infrastructure.postgres_connector import AsyncPostgresConnector
import pandas as pd
import requests
from io import StringIO
from typing import Optional
from selenium import webdriver  # assuming you're using Selenium


# Global state
browser: Optional[webdriver.Chrome] = None
current_page = 1
db: Optional[AsyncPostgresConnector] = None


async def fetch_zillow_data() -> list[tuple]:
    url = "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv?t=1769456072"
    response = requests.get(url)
    csv_data = StringIO(response.text)

    df = pd.read_csv(csv_data)

    # Melt df so each month is an entry
    df_long = df.melt(
        id_vars = ["RegionID", "SizeRank", "RegionName", "StateName"],
        var_name="date",
        value_name="avg_cost"
    )

    # Convert date strings to datetime
    df_long["date"] = pd.to_datetime(df["date"])

    # Create id column
    df_long["id"] = range(1, len(df_long) + 1)

    # Reorder columns 
    df_long = df_long[["id", "RegionID", "SizeRank", "RegionName", "StateName", "date", "avg_cost"]]
    df_long.columns = ["id", "region_id", "size_rank", "region_name", "state_name", "date", "avg_cost"]

    return list(df_long.itertuples(index=False, name=None))


async def main():
    async with AsyncPostgresConnector(
        host="localhost",
        port=5432,
        dbname="real_estate_db",   # default when POSTGRES_DB not set
        user="postgres",     # default when POSTGRES_USER not set
        password="12345",
    ) as db:
        result = await db.fetch_one("SELECT * from properties LIMIT 1;")
        print(f"Connected!\n{result}")

asyncio.run(main())