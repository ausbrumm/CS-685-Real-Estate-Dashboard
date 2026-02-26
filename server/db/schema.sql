-- Region lookup table
CREATE TABLE IF NOT EXISTS public.regions(
    region_id bigint NOT NULL,
    region_name text NOT NULL,
    state_name text NOT NULL,
    CONSTRAINT regions_pkey PRIMARY KEY (region_id)
);

-- Metro-level time series data
CREATE TABLE IF NOT EXISTS public.metro_us(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_id bigint NOT NULL,
    size_rank integer NOT NULL,
    date date NOT NULL,
    avg_cost numeric(15,2),

    CONSTRAINT metro_us_region_date_unique UNIQUE (region_id, date),
    CONSTRAINT metro_us_region_fk
        FOREIGN KEY (region_id)
        REFERENCES public.regions (region_id)
);

-- Individual property listings
CREATE TABLE IF NOT EXISTS public.property_listings(
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    address text NOT NULL,
    city text NOT NULL,
    state text NOT NULL,
    zip text NOT NULL,
    sqft integer,
    beds integer,
    baths integer,
    built_year integer,
    property_type text,
    status text,
    price numeric(15,2),
    agent text,
    broker text,
    lat numeric(10,8),
    lon numeric(11,8),
    parcel text,
    last_change date,
    region_id bigint,
    CONSTRAINT property_listings_unique UNIQUE (address, city, state, zip),
    CONSTRAINT property_listings_region_fk 
        FOREIGN KEY (region_id) 
        REFERENCES public.regions(region_id)
);
-- Create subdivision of coastline to "chunk" the math
CREATE TABLE coastline_subdivided AS
-- gid = geographic ID, primary key
SELECT gid, ST_Subdivide(geom, 255) as geom
FROM coastline_table;
-- GIST: genarilized search tree (B-tree), used for sorting spatial data
CREATE INDEX idx_coast_subdivide_gist ON coastline_subdivided USING GIST (geom);

CREATE TABLE property_geometries AS
SELECT 
    id, 
    ST_SetSRID(ST_Point(lon, lat), 4326)::geometry(Point, 4326) as geom
FROM property_listings
WHERE lon IS NOT NULL AND lat IS NOT NULL;

CREATE INDEX idx_prop_geometries_gist ON property_geometries USING GIST (geom);

`CREATE MATERIALIZED VIEW property_listings_geo AS
SELECT 
    *, 
    ST_SetSRID(ST_Point(lon, lat), 4326)::geometry(Point, 4326) as geom
FROM property_listings
WHERE lon IS NOT NULL AND lat IS NOT NULL;

CREATE INDEX idx_property_geo_gist ON property_listings_geo USING GIST (geom);`


CREATE INDEX IF NOT EXISTS idx_listings_state ON property_listings(state);
CREATE INDEX IF NOT EXISTS idx_listings_price ON property_listings(price);
CREATE INDEX IF NOT EXISTS idx_listings_status ON property_listings(status);
CREATE INDEX IF NOT EXISTS idx_listings_region_id ON property_listings(region_id);
CREATE INDEX IF NOT EXISTS idx_property_geom_gist ON property_geometries USING gist(geom);