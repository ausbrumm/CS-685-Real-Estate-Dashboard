import csv
import requests
from io import StringIO

ZILLOW_URL = (
    "https://files.zillowstatic.com/research/public_csvs/"
    "zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)

def fetch_raw_data() -> list[dict]:
    
    # Fetch raw housing data and return normalized rows
    # No db logic yet
    resp = requests.get(ZILLOW_URL)
    # check for HTTP error
    resp.raise_for_status()
    
    reader = csv.DictReader(StringIO(resp.text))
    rows = []

    for row in reader:
        rows.append({
            "region_id": int(row["RegionID"]),
            "region_name": row["RegionName"],
            "state_name": row["StateName"],
            "size_rank": int(row["SizeRank"]),
            "date": row["Date"],
            "avg_cost": float(row["AverageCost"]) if row["AverageCost"] else None

        })

    return rows
