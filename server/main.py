#!/usr/bin/env python3

import asyncio
from infrastructure.postgres_connector import AsyncPostgresConnector
from typing import Optional

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


async def main():
    regions = [394463]
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
                data.append([r[5], r[6]])  # date, price

            pred_service = PredictionService()
            pred_service.run(data, group_size=3, repeats=100, k=5)


# asyncio.run(main())
