import psycopg2
from elasticsearch import Elasticsearch, helpers
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
# Connect to Postgres
pg_conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB", "orders_db"),
    user=os.getenv("POSTGRES_USER", "user"),
    password=os.getenv("POSTGRES_PASSWORD", "password"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432")
)
pg_cursor = pg_conn.cursor()

# Connect to Elasticsearch
es = Elasticsearch(os.getenv("ES_HOST", "http://localhost:9200"))

# Fetch data from Postgres
pg_cursor.execute("SELECT order_id, item, quantity, price FROM orders")
rows = pg_cursor.fetchall()

actions = []
for row in rows:
    order_id, item, quantity, price = row
    doc = {
        "order_id": order_id,
        "item": item,
        "quantity": quantity,
        "price": float(price)
    }
    actions.append({
        "_index": "orders",
        "_id": order_id,
        "_source": doc
    })

# Bulk insert to Elasticsearch
helpers.bulk(es, actions)

print(f"✅ Indexed {len(actions)} records into Elasticsearch")

pg_cursor.close()
pg_conn.close()