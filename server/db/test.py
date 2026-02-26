import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
from sklearn.neighbors import BallTree
import numpy as np


engine = create_engine('postgresql://realestate_user:devpassword@localhost:5432/real_estate_db')

def run_demo():
    query = text("""
            SELECT 
                 p.id,
                 p.price,
                 p.address,
                 p.city,
                 p.state,
                 p.lat,
                 p.lon,
                 ST_Distance(p.geom::geography, c.geom::geography) AS dist_m
            FROM property_listings_geo p
            CROSS JOIN LATERAL (
                 SELECT geom FROM coastline_table
                 ORDER BY geom <-> p.geom
                 LIMIT 1
            ) c
            WHERE p.price > 100000
            LIMIT 10;
          """)
    with engine.connect() as conn:
        results = conn.execute(query)
        print(f"{'Address':<15} | {'City':<10} | {'State':<5} | {'p.lat':<12} | {'p.lon':<15} | {'ID':<10} | {'Price':<12} | {'Dist to Coast (m)':<15}")
        print("-" * 45)
        for row in results:
            price = row.price if row.price is not None else 0
            print(f"{row.address:<15} | {row.city:<10} | {row.state:<5} | {row.lat:<12} | {row.lon:<15} | {row.id:<10} | ${price:<12} | {row.dist_m:,.2f}m")

if __name__ == "__main__":
    run_demo()