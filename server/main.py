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


async def main(cutoff: int, start_month: int, group_size: int = 3, k: int = 6):
    regions = [394463, 394910, 394338, 753899, 394357, 394466, 394596, 395107]
    pred_service = PredictionService()

    summaries = []

    for region in regions:
        print(f"\n{'='*60}")
        print(f"Region: {region}")
        print(f"{'='*60}")

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

        data = []
        for r in result:
            data.append([r[5], r[6]])  # date, price

        training_data = pred_service.generate_training_set(data, cutoff)
        test_data = pred_service.generate_test_set(data, cutoff)

        # --- PRINT TRACE ---
        print(f"[DEBUG] Full set count: {len(data)}")
        if training_data:
            print(f"[DEBUG] Training: {training_data[0][0]} -> {training_data[-1][0]}")
        if test_data:
            print(f"[DEBUG] Test:     {test_data[0][0]} -> {test_data[-1][0]}")

        _, patterns, _, _, _, training_frequencies, _, _, _ = pred_service.run(training_data, group_size=group_size)
        print(f"Training frequencies: {training_frequencies}")

        change_hist = pred_service.get_changes(training_data, group_size=group_size)
        extended_test = list(training_data[-group_size:]) + list(test_data)
        summary = pred_service.predict(extended_test, patterns, training_frequencies, start_month, change_hist, group_size=group_size, k=k)
        if summary:
            summaries.append({"region": region, **summary})

    # --- FINAL SUMMARY ---
    if summaries:
        lines = []
        lines.append(f"Flags: group_size={group_size}  k={k}  year={cutoff}  month={start_month}")
        lines.append("")
        lines.append(f"{'='*75}")
        lines.append(f"FINAL SUMMARY")
        lines.append(f"{'='*75}")
        lines.append(f"{'Region':<12} {'Correct':>8} {'Total':>7} {'Accuracy':>10} {'MSE':>14} {'RMSE':>12}")
        lines.append(f"{'-'*75}")
        for s in summaries:
            lines.append(f"{s['region']:<12} {s['correct']:>8} {s['total']:>7} {s['accuracy']:>9.0%} {s['mse']:>14,.2f} {s['rmse']:>12,.2f}")
        lines.append(f"{'='*75}")
        lines.append("")
        lines.append(f"{'='*95}")
        lines.append(f"DETAILED PREDICTIONS BY REGION")
        for s in summaries:
            lines.append(f"\n--- Region {s['region']} ---")
            lines.append(f"{'Month':<12} {'Last Known':>14} {'Magnitude':>12} {'Predicted':>14} {'Actual':>14} {'Error':>12} {'Dir':>4} {'OK':>4}")
            lines.append(f"{'='*95}")
            for r in s["rows"]:
                ok = "✓" if r["correct"] else "✗"
                lines.append(f"{str(r['month']):<12} ${r['last_known']:>13,.2f} ${r['magnitude']:>11,.2f} ${r['predicted']:>13,.2f} ${r['actual']:>13,.2f} ${r['error']:>11,.2f} {r['direction']:>4} {ok:>4}")
            lines.append(f"{'='*95}")
            lines.append(f"Success rate: {s['correct']}/{s['total']} ({s['accuracy']:.0%})  MSE: {s['mse']:,.2f}  RMSE: {s['rmse']:,.2f}")

        output = "\n".join(lines)
        print(output)

        log_path = f"logs/k{k}_g{group_size}.txt"
        import os
        os.makedirs("logs", exist_ok=True)
        with open(log_path, "w") as f:
            f.write(output + "\n")
        print(f"\nLog saved to {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run real estate prediction")
    parser.add_argument("--year", "-y", type=int, default=2020,
                        help="Cutoff year: data before this year is training, on/after is test (default: 2020)")
    parser.add_argument("--month", "-m", type=int, default=0,
                        help="Start month offset 0-11 (0=Jan, 1=Feb, ... default: 0)")
    parser.add_argument("--group-size", "-g", type=int, default=3, choices=[3, 4, 5],
                        help="Group size for pattern matching (default: 3)")
    parser.add_argument("--k", type=int, default=6, choices=[1, 3, 5, 7, 9],
                        help="k nearest neighbors for magnitude estimation (default: 6)")
    args = parser.parse_args()
    asyncio.run(main(args.year, args.month, args.group_size, args.k))
