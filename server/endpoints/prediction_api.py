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
    patterns: Dict[str, str] 
    probabilities: Dict[str, float]
    subsets: Dict[int, str]
    counts: Dict[str, int]
    status: str

@router.get("/predict/{region_id}", response_model=PredictionResponse)
async def get_prediction(region_id: int, start_month: int = 0, end_month: int = 3):
    """
    Fetches data for a specific region from Postgres and runs the Prediction Service.
    """
    async with AsyncPostgresConnector(**DB_CONFIG) as db:
    
        query = "SELECT * FROM public.zillow_data WHERE region_id = %s ORDER BY date;"
        rows = await db.fetch_all(query, [str(region_id)])

        if not rows:
            raise HTTPException(status_code=404, detail=f"No data found for region {region_id}")

        # r[1]=id, r[3]=name, r[4]=state, r[5]=date, r[6]=cost
        data = [ZillowData(r[1], r[3], r[4], r[5], r[6]) for r in rows]
        region_name = rows[0][3]

        # run prediction service
        pred_service = PredictionService()
        predictions, probs, subsets, counts = pred_service.run(data, cluster_range=[start_month, end_month])

        return {
            "region_id": region_id,
            "region_name": region_name,
            "patterns": predictions,
            "probabilities": probs,
            "subsets": subsets,
            "counts": counts,
            "status": "success"
        }