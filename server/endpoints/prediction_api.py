from fastapi import FastAPI, HTTPException, Query, APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import pandas as pd
from io import StringIO
import requests
import os
import calendar
import datetime as dt

from infrastructure.postgres_connector import AsyncPostgresConnector
from infrastructure.prediction_service import PredictionService

router = APIRouter()

# Database configuration
DB_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", 5432)),
    "dbname": os.environ.get("POSTGRES_DB", "real_estate_db"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "12345"),
}


class AccuracySummary(BaseModel):
    correct: int
    wrong: int
    total: int
    accuracy: float
    mse: float
    rmse: float


class PredictionResult(BaseModel):
    date: Optional[str]
    predictions: Dict[str, Dict[str, Any]]


class PredictionResponse(BaseModel):
    region_id: int
    region_name: str
    group_size: int
    k: int
    patterns: List[str]
    groups: List[List[Any]]
    changes: List[List[Any]]
    frequencies: Dict[str, Dict[str, int]]
    original_data: List[List[Any]]
    results: List[PredictionResult]
    accuracy_summary: AccuracySummary
    status: str
    error_band: List[Any]
    last_real_date: Optional[str]

    class Config:
        arbitrary_types_allowed = True


@router.get("/predict/{region_id}", response_model=PredictionResponse)
async def get_prediction(
    region_id: int,
    pred_month: Optional[int] = None,
    pred_year: Optional[int] = None,
    group_size: int = Query(4),
    k: int = Query(5),
):
    """
    Fetches data for a specific region from Postgres and runs the Prediction Service.
    """
    async with AsyncPostgresConnector(**DB_CONFIG) as db:
        query = "SELECT * FROM public.zillow_data WHERE region_id = %s ORDER BY date;"
        rows = await db.fetch_all(query, [str(region_id)])

        if not rows:
            raise HTTPException(
                status_code=404, detail=f"No data found for region {region_id}"
            )

        # r[1]=id, r[3]=name, r[4]=state, r[5]=date, r[6]=cost
        data = []

        for r in rows:
            data.append([r[5], r[6]])  # date, price
        region_name = rows[0][3]

        # run prediction service
        pred_date = None
        if pred_month is not None or pred_year is not None:
            now = dt.date.today()
            year = pred_year if pred_year is not None else now.year
            month = pred_month if pred_month is not None else now.month
            last_day = calendar.monthrange(year, month)[1]
            pred_date = dt.date(year, month, last_day)

        pred_service = PredictionService()
        try:
            pred_service.validate_group_size(group_size)
            pred_service.validate_k(k)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        (
            results,
            patterns,
            groups,
            changes,
            data,
            frequencies,
            acc_summary,
            error_bands,
            last_real_date,
        ) = pred_service.run(
            data, group_size=group_size, k=k, pred_date=pred_date
        )

        # handle edge case where prediction service returns no results
        if not results:
            raise HTTPException(
                status_code=422,
                detail=f"Insufficient data to generate predictions for region {region_id}",
            )

        return {
            "region_id": region_id,
            "region_name": region_name,
            "group_size": group_size,
            "k": k,
            "patterns": patterns,
            "groups": [[str(g[0]), float(g[1]), g[2]] for g in groups],
            "changes": [[str(c[0]), float(c[1]), c[2]] for c in changes],
            "frequencies": {str(k): dict(v) for k, v in frequencies.items()},
            "original_data": [[str(row[0]), float(row[1])] for row in data],
            "results": [
                {
                    "date": str(r["date"]) if r["date"] else None,
                    "predictions": {
                        str(month): {
                            "direction": pred["direction"],
                            "price": float(pred["price"]),
                        }
                        for month, pred in r["predictions"].items()
                    },
                }
                for r in results
            ],
            "accuracy_summary": acc_summary,
            "error_band": error_bands,
            "status": "success",
            "last_real_date": last_real_date,
        }
