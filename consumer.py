import pika
import psycopg2
import redis
import json
import time

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    dbname="orders_db",
    user="user",
    password="password",
    host="postgres",
    port="5432"
)
pg_cursor = pg_conn.cursor()

# Create table if not exists
pg_cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    item TEXT,
    quantity INT,
    price NUMERIC
);
""")
pg_conn.commit()

# Connect to Redis
r = redis.Redis(host='redis', port=6379, db=0)

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='order_queue', durable=True)
channel.basic_qos(prefetch_count=1)

def callback(ch, method, properties, body):
    print(f"--- Callback triggered ---")
    print(f"method: {method}")
    print(f"properties: {properties}")
    print(f"body: {body}")
    order = json.loads(body.decode())
    print(f"[x] Received Order: {order}")

    # Store in PostgreSQL
    pg_cursor.execute(
        "INSERT INTO orders (item, quantity, price) VALUES (%s, %s, %s)",
        (order["item"], order["quantity"], order["price"])
    )
    pg_conn.commit()

    # Cache in Redis
    r.set(f"order:{order['order_id']}", json.dumps(order))

    print(f"[✓] Order {order['order_id']} saved to DB and cached in Redis")
    time.sleep(1)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='order_queue', on_message_callback=callback)

print('[*] Waiting for orders...')
channel.start_consuming()