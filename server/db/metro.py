METRO_INSERT_SQL = """
INSERT INTO metro_us (region_id, size_rank, date, avg_cost)
VALUES (%s, %s, %s, %s)
ON CONFLICT (region_id, date)
DO UPDATE SET avg_cost = EXCLUDED.avg_cost;
"""

def prepare_metro_rows(raw_rows: list[dict]) -> list[tuple]:
    return [
        (
            r["region_id"],
            r["size_rank"],
            r["date"],
            r["avg_cost"]
        )
        for r in raw_rows
    ]