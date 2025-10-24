import redis
import psycopg2
import json

# Connect to Redis & PostgreSQL
r = redis.Redis(host='127.0.0.1', port=6379)
pg_conn = psycopg2.connect(dbname="orders_db", user="user", password="password", host="127.0.0.1")
pg_cursor = pg_conn.cursor()


def get_order(order_id):
    # 1️⃣ Try Redis cache first
    data = r.get(f"order:{order_id}")
    if data:
        print("Cache hit ✅")
        return json.loads(data)

    print("Cache miss ❌ Fetching from DB...")
    # 2️⃣ If not found in cache, query Postgres
    pg_cursor.execute("SELECT order_id, item, quantity, price FROM orders WHERE order_id = %s", (order_id,))
    row = pg_cursor.fetchone()
    if not row:
        return None

    order = {
        "order_id": row[0],
        "item": row[1],
        "quantity": row[2],
        "price": float(row[3])
    }

    # 3️⃣ Save to Redis for next time
    r.set(f"order:{order_id}", json.dumps(order), ex=300)  # TTL: 300 sec
    return order
# order_num = int(input("enter order number"))
# get_order(order_num)
print(get_order(13))
get_order(101)
get_order(2)
get_order(3)
get_order(1)
