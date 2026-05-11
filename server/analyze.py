#!/usr/bin/env python3
"""Standalone next-month prediction analysis command.

Fetches Zillow data for one or more regions, predicts exactly one month past
the latest available data point, and prints a compact summary that includes
the region, group_size, and k values used for the forecast.

Usage:
    python analyze.py [--group-size {1,2,3,4,6,12}] [--k {1,3,5,7,9,11}] [--region REGION_ID ...]
"""

import argparse
import asyncio
import calendar
import os

from infrastructure.postgres_connector import AsyncPostgresConnector
from infrastructure.prediction_service import PredictionService

DB_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", 5432)),
    "dbname": os.environ.get("POSTGRES_DB", "real_estate_db"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "12345"),
}

REGIONS = [394463, 394910, 394338, 753899, 394357, 394466, 394596, 395107]


def _next_month_date(last_date):
    if last_date.month == 12:
        year = last_date.year + 1
        month = 1
    else:
        year = last_date.year
        month = last_date.month + 1
    return last_date.replace(year=year, month=month, day=calendar.monthrange(year, month)[1])


def _calculate_bound_accuracy(actual_data, error_band):
    actual_by_date = {date: float(price) for date, price in actual_data}
    hits = 0
    total = 0

    for band in error_band:
        band_date = band.get("date")
        if band_date not in actual_by_date:
            continue

        actual_price = actual_by_date[band_date]
        if band["lower"] <= actual_price <= band["upper"]:
            hits += 1
        total += 1

    return hits / total if total else 0.0


def _build_accuracy_stats(prediction_service, data, group_size, k, runs=100):
    prediction_accuracies = []
    bound_accuracies = []

    for _ in range(runs):
        _, _, _, _, actual_data, _, acc_summary, error_band, _ = prediction_service.run(
            data,
            group_size=group_size,
            k=k,
        )
        prediction_accuracies.append(acc_summary["accuracy"])
        bound_accuracies.append(_calculate_bound_accuracy(actual_data, error_band))

    return {
        "prediction_accuracy": (
            sum(prediction_accuracies) / len(prediction_accuracies)
            if prediction_accuracies
            else 0.0
        ),
        "bounds_accuracy": (
            sum(bound_accuracies) / len(bound_accuracies) if bound_accuracies else 0.0
        ),
    }


def _build_future_projection(prediction_service, data, group_size, k, pred_date):
    _, _, _, _, projected_data, _, _, _, _ = prediction_service.run(
        data,
        group_size=group_size,
        k=k,
        pred_date=pred_date,
    )
    return projected_data


def _format_report(summaries):
    width = 166
    lines = []
    lines.append("=" * width)
    lines.append("NEXT MONTH FORECAST SUMMARY")
    lines.append("=" * width)
    lines.append(
        f"{'Region':<10} {'Name':<24} {'Group Size':>10} {'K':>4} "
        f"{'Last Month':>12} {'Pred Month':>12} {'Last Price':>14} "
        f"{'Predicted':>14} {'Change':>12} {'Pct Change':>11} {'Dir':>4} "
        f"{'Pred Acc':>10} {'Bound Acc':>11}"
    )
    lines.append("-" * width)

    for summary in summaries:
        lines.append(
            f"{summary['region']:<10} {summary['region_name'][:24]:<24} "
            f"{summary['group_size']:>10} {summary['k']:>4} "
            f"{str(summary['last_date']):>12} {str(summary['predicted_date']):>12} "
            f"${summary['last_price']:>13,.2f} ${summary['predicted_price']:>13,.2f} "
            f"${summary['change']:>11,.2f} {summary['pct_change']:>10.2%} "
            f"{summary['direction']:>4} {summary['prediction_accuracy']:>9.2%} "
            f"{summary['bounds_accuracy']:>10.2%}"
        )

    lines.append("=" * width)
    return "\n".join(lines)


def _resolve_log_target(region_ids, group_size, k):
    if len(region_ids) == 1:
        return f"logs/region_{region_ids[0]}.txt", "a"
    return f"logs/g{group_size}_k{k}.txt", "w"


def _build_future_summary(
    region_id,
    region_name,
    group_size,
    k,
    projected_data,
    prediction_accuracy=0.0,
    bounds_accuracy=0.0,
):
    last_date, last_price = projected_data[-2]
    predicted_date, predicted_price = projected_data[-1]
    change = float(predicted_price) - float(last_price)
    pct_change = change / float(last_price) if last_price else 0.0

    return {
        "region": region_id,
        "region_name": region_name,
        "group_size": group_size,
        "k": k,
        "last_date": last_date,
        "predicted_date": predicted_date,
        "last_price": float(last_price),
        "predicted_price": float(predicted_price),
        "change": change,
        "pct_change": pct_change,
        "direction": "U" if change >= 0 else "D",
        "prediction_accuracy": prediction_accuracy,
        "bounds_accuracy": bounds_accuracy,
    }


async def main(group_size: int = 3, k: int = 5, regions=None):
    svc = PredictionService()
    region_ids = regions or REGIONS
    summaries = []

    async with AsyncPostgresConnector(**DB_CONFIG) as db:
        for region_id in region_ids:
            rows = await db.fetch_all(
                "SELECT * FROM public.zillow_data WHERE region_id = %s ORDER BY date;",
                [str(region_id)],
            )
            if not rows:
                continue

            region_name = rows[0][3]
            data = [(row[5], row[6]) for row in rows]
            if len(data) < 2:
                continue

            accuracy_stats = _build_accuracy_stats(
                svc,
                data,
                group_size=group_size,
                k=k,
            )
            pred_date = _next_month_date(data[-1][0])
            projected_data = _build_future_projection(
                svc,
                data,
                group_size=group_size,
                k=k,
                pred_date=pred_date,
            )
            if len(projected_data) < 2:
                continue

            summaries.append(
                _build_future_summary(
                    region_id=region_id,
                    region_name=region_name,
                    group_size=group_size,
                    k=k,
                    projected_data=projected_data,
                    prediction_accuracy=accuracy_stats["prediction_accuracy"],
                    bounds_accuracy=accuracy_stats["bounds_accuracy"],
                )
            )

    if not summaries:
        print("No forecasts generated.")
        return

    report = _format_report(summaries)
    print(report)

    os.makedirs("logs", exist_ok=True)
    log_path, mode = _resolve_log_target(region_ids, group_size, k)
    with open(log_path, mode, encoding="utf-8") as file_obj:
        if mode == "a" and file_obj.tell() > 0:
            file_obj.write("\n" + ("#" * 140) + "\n\n")
        file_obj.write(report + "\n")

    print(f"\nLog saved to {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run real estate next-month forecast analysis")
    parser.add_argument(
        "--group-size",
        "-g",
        type=int,
        default=3,
        choices=[1, 2, 3, 4, 6, 12],
        help="Group size for pattern matching; must divide 12 (default: 3)",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        choices=[1, 3, 5, 7, 9, 11],
        help="k nearest neighbors for magnitude estimation (default: 5)",
    )
    parser.add_argument(
        "--region",
        dest="regions",
        type=int,
        action="append",
        help="Specific region_id to analyze; repeat to include multiple regions",
    )
    args = parser.parse_args()
    asyncio.run(main(group_size=args.group_size, k=args.k, regions=args.regions))
