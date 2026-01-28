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