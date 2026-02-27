from fastapi import FastAPI, HTTPException, Query, APIRouter
from pydantic import BaseModel
from typing import List, Dict
import asyncio
import pandas as pd
from io import StringIO
import requests

from infrastructure.postgres_connector import AsyncPostgresConnector
from infrastructure.prediction_service import PredictionService, ZillowData

router = APIRouter()

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "real_estate_db",
    "user": "postgres",
    "password": "12345",
}

class PredictionResponse(BaseModel):
    region_id: int
    region_name: str
    patterns: List[str]
    groups: List[List[any]]
    changes: List[List[any]]
    frequencies: Dict[str, Dict[str, int]]  # str keys since JSON can't have int keys
    original_data: List[List[any]]
    results: List[List[any]]
    status: str

    class Config:
        arbitrary_types_allowed = True

@router.get("/predict/{region_id}", response_model=PredictionResponse)
async def get_prediction(region_id: int, start_month: int = 0):
    """
    Fetches data for a specific region from Postgres and runs the Prediction Service.
    """
    async with AsyncPostgresConnector(**DB_CONFIG) as db:
    
        query = "SELECT * FROM public.zillow_data WHERE region_id = %s ORDER BY date;"
        rows = await db.fetch_all(query, [str(region_id)])

        if not rows:
            raise HTTPException(status_code=404, detail=f"No data found for region {region_id}")

        # r[1]=id, r[3]=name, r[4]=state, r[5]=date, r[6]=cost
        data = []
           
        for r in rows:
            # data.append([r[1], r[3], r[4], r[5], r[6]])
            data.append([r[5], r[6]]) # date, price

        region_name = rows[0][3]

        # run prediction service
        pred_service = PredictionService()
        results, patterns, groups, changes, data, frequencies = pred_service.run(data, start_month)

        return {
            "region_id": region_id,
            "region_name": region_name,
            "patterns": patterns,
            "groups": [[str(g[0]), float(g[1]), g[2]] for g in groups],
            "changes": [[str(c[0]), float(c[1]), c[2]] for c in changes],
            "frequencies": {
                str(k): dict(v) for k, v in frequencies.items()  # int keys -> str, Counter -> dict
            },
            "original_data": [[str(row[0]), float(row[1])] for row in data],
            "results": [
                [str(r[0]) if r[0] else None, float(r[1]) if r[1] else 0, r[2]] + 
                [[item[0], float(item[1]), item[2]] for item in r[3:]]
                for r in results
            ],
            "status": "success"
        }