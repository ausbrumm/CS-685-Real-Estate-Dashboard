CREATE DATABASE real_estate_db;

CREATE TABLE IF NOT EXISTS metro_us (
    id SERIAL PRIMARY KEY,
    region_id NUMERIC(15) NOT NULL,
    size_rank NUMERIC(15) NOT NULL,
    region_name VARCHAR(255) NOT NULL,
    state_name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    avg_cost NUMERIC(15, 11),
    source VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS zillow_data (
    id BIGINT PRIMARY KEY,
    region_id BIGINT,
    size_rank INT,
    region_name TEXT,
    state_name TEXT,
    date DATE,
    avg_cost NUMERIC
);
