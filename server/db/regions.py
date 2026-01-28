from collections import defaultdict

REGION_INSERT_SQL = """
INSERT INTO regions (region_id, region_name, state_name)
VALUES (%s, %s, %s)
ON CONFLICT (region_id) DO NOTHING;
"""  

def prepare_region_rows(raw_rows: list[dict]) -> list[tuple]:
    """
    Remove duplicate regions from raw data
    """
    regions = {}

    for r in raw_rows:
        regions[r["region_id"]] = (
            r["region_id"],
            r["region_name"],
            r["state_name"]
        )

    return list(regions.values())