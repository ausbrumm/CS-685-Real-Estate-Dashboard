#!/usr/bin/env python3

import asyncio
from infrastructure.postgres_connector import AsyncPostgresConnector
import pandas as pd
import requests
from io import StringIO
from typing import Optional

# FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.prediction_service import PredictionService, ZillowData
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


async def main():
    regions = [394463, 394910, 394338, 753899, 394357, 394466, 394596, 395107]
    for region in regions:
        async with AsyncPostgresConnector(
            host="localhost",
            port=5432,
            dbname="real_estate_db",  # default when POSTGRES_DB not set
            user="postgres",  # default when POSTGRES_USER not set
            password="12345",
        ) as db:
            result = await db.fetch_all(
                "SELECT * FROM public.zillow_data where region_id = %s order by date;",
                [str(region)],
            )

            data = []
           
            for r in result:
               # data.append([r[1], r[3], r[4], r[5], r[6]])
               data.append([r[5], r[6]]) # date, price
            
            

            pred_service = PredictionService()
            pred_service.run(data, group_size=3)



#asyncio.run(main())
