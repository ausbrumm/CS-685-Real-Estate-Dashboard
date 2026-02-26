import geopandas as gpd
from sqlalchemy import create_engine

gdf = gpd.read_file("./ne_10m_coastline/ne_10m_coastline.shp")

engine = create_engine("postgresql://postgres:devpassword@localhost:5432/real_estate_db")

gdf.to_postgis("coastline_table", engine, if_exists="replace", index=False)

print("upload complete")