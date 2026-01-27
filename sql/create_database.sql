CREATE DATABASE real_estate_db;

-- Table: public.metro_us

-- DROP TABLE IF EXISTS public.metro_us;

CREATE TABLE IF NOT EXISTS public.metro_us
(
    id BIGINT NOT NULL DEFAULT nextval('metro_us_id_seq'::regclass),
    region_id BIGINT NOT NULL,
    size_rank INTEGER NOT NULL,
    region_name TEXT COLLATE pg_catalog."default",
    state_name TEXT COLLATE pg_catalog."default",
    date date NOT NULL,
    avg_cost numeric(15,2),
    CONSTRAINT metro_us_pkey PRIMARY KEY (id)
)