CREATE DATABASE real_estate_db;

-- Table: public.metro_us

-- DROP TABLE IF EXISTS public.metro_us;

CREATE TABLE IF NOT EXISTS public.metro_us
(
    id bigint NOT NULL DEFAULT nextval('metro_us_id_seq'::regclass),
    region_id bigint NOT NULL,
    size_rank integer NOT NULL,
    date date NOT NULL,
    avg_cost numeric(15,2),
    CONSTRAINT metro_us_pkey PRIMARY KEY (id),
    CONSTRAINT metro_us_region_date_unique UNIQUE (region_id, date),
    CONSTRAINT metro_us_region_fk FOREIGN KEY (region_id)
        REFERENCES public.regions (region_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

CREATE TABLE IF NOT EXISTS public.regions
(
    region_id bigint NOT NULL,
    region_name text COLLATE pg_catalog."default",
    state_name text COLLATE pg_catalog."default",
    CONSTRAINT regions_pkey PRIMARY KEY (region_id)
)