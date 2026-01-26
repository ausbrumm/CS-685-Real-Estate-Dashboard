CREATE DATABASE real_estate_db;

-- Table: public.metro_us

-- DROP TABLE IF EXISTS public.metro_us;

CREATE TABLE IF NOT EXISTS public.metro_us
(
    id integer NOT NULL DEFAULT nextval('metro_us_id_seq'::regclass),
    region_id numeric(15,0) NOT NULL,
    size_rank numeric(15,0) NOT NULL,
    region_name character varying(255) COLLATE pg_catalog."default",
    state_name character varying(255) COLLATE pg_catalog."default",
    date date NOT NULL,
    avg_cost numeric(15,2),
    source character varying(100) COLLATE pg_catalog."default",
    CONSTRAINT metro_us_pkey PRIMARY KEY (id)
)