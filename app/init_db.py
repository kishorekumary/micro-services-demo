import time
import psycopg2

DB_CONFIG = {
    "dbname": "orders_db",
    "user": "user",
    "password": "password",
    "host": "postgres",
    "port": "5432",
}

TABLE_CREATION_SQL = """
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    item TEXT,
    quantity INT,
    price NUMERIC,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create a function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop the trigger if it exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_orders_updated_at') THEN
        -- Create a trigger to update the updated_at column on row update
        EXECUTE '
        CREATE TRIGGER update_orders_updated_at
        BEFORE UPDATE ON orders
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();';
    END IF;
END$$;
"""

def wait_for_db():
    for i in range(10):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            print("✅ PostgreSQL is ready")
            return
        except Exception as e:
            print("⏳ Waiting for PostgreSQL...", e)
            time.sleep(3)
    raise Exception("❌ PostgreSQL not reachable after multiple attempts")

def init_db():
    wait_for_db()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(TABLE_CREATION_SQL)
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

if __name__ == "__main__":
    init_db()