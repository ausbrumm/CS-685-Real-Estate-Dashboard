CREATE DATABASE real_estate_db;

CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    address VARCHAR(255) NOT NULL,
    price NUMERIC(15, 2) NOT NULL,
    bedrooms INT NOT NULL,
    bathrooms INT NOT NULL,
    sqft INT NOT NULL,
    listing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100)
);