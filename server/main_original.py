#!/usr/bin/env python3

import argparse
import asyncio
from infrastructure.postgres_connector import AsyncPostgresConnector
import pandas as pd
import requests
from io import StringIO
from typing import Optional

from collections import defaultdict
from decimal import Decimal

# FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.prediction_service import PredictionService
from endpoints.prediction_api import router as prediction_router

app = FastAPI(title="Zillow Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction_router)

# Global state
db: Optional[AsyncPostgresConnector] = None


async def fetch_zillow_data() -> list[tuple]:
    url = "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv?t=1769456072"
    response = requests.get(url)
    csv_data = StringIO(response.text)

    df = pd.read_csv(csv_data)

    # Melt df so each month is an entry
    df_long = df.melt(
        id_vars=["RegionID", "SizeRank", "RegionName", "StateName"],
        var_name="date",
        value_name="avg_cost",
    )

    # Convert date strings to datetime
    df_long["date"] = pd.to_datetime(df["date"])

    # Create id column
    df_long["id"] = range(1, len(df_long) + 1)

    # Reorder columns
    df_long = df_long[
        ["id", "RegionID", "SizeRank", "RegionName", "StateName", "date", "avg_cost"]
    ]
    df_long.columns = [
        "id",
        "region_id",
        "size_rank",
        "region_name",
        "state_name",
        "date",
        "avg_cost",
    ]

    return list(df_long.itertuples(index=False, name=None))


async def main(cutoff: int, start_month: int):
    regions = [395107]
    data = []
    for region in regions:
        async with AsyncPostgresConnector(
            host="localhost",
            port=5432,
            dbname="real_estate_db",
            user="postgres",
            password="devpassword",
        ) as db:
            result = await db.fetch_all(
                "SELECT * FROM public.zillow_data where region_id = %s order by date;",
                [str(region)],
            )

            for r in result:
                data.append([r[5], r[6]])  # date, price

    #print(data)
    pred_service = PredictionService()
    training_data = pred_service.generate_training_set(data, cutoff)
    test_data = pred_service.generate_test_set(data, cutoff)

    # --- PRINT TRACE ---
    print(f"[DEBUG] Full set count: {len(data)}")
    if training_data:
        print(f"[DEBUG] First entry: {data[0][0]} -> ${data[0][1]:,.2f}")
        print(f"[DEBUG] Last entry:  {data[-1][0]} -> ${data[-1][1]:,.2f}")

    print(f"[DEBUG] Training set count: {len(training_data)}")
    if training_data:
        print(f"[DEBUG] First entry: {training_data[0][0]} -> ${training_data[0][1]:,.2f}")
        print(f"[DEBUG] Last entry:  {training_data[-1][0]} -> ${training_data[-1][1]:,.2f}")

    print(f"\n[DEBUG] Testing set count: {len(test_data)}")
    if test_data:
        print(f"[DEBUG] First entry: {test_data[0][0]} -> ${test_data[0][1]:,.2f}")
        print(f"[DEBUG] Last entry:  {test_data[-1][0]} -> ${test_data[-1][1]:,.2f}")

    _, patterns, _, _, _, training_frequencies, _, _, _ = pred_service.run(training_data, group_size=3)
    print(f"Training frequencies: {training_frequencies}")

    change_hist = pred_service.get_changes(training_data, group_size=3)
    pred_service.predict(test_data, patterns, training_frequencies, start_month, change_hist)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run real estate prediction")
    parser.add_argument("--year", "-y", type=int, default=2020,
                        help="Cutoff year: data before this year is training, on/after is test (default: 2020)")
    parser.add_argument("--month", "-m", type=int, default=0,
                        help="Start month offset 0-11 (0=Jan, 1=Feb, ... default: 0)")
    args = parser.parse_args()
    asyncio.run(main(args.year, args.month))
