CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    item TEXT,
    quantity INT,
    price NUMERIC
);