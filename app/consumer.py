import pika
import psycopg2
import redis
import json
import os
import pika

from db import get_connection
from cache import r
from dotenv import load_dotenv
load_dotenv()
import time

# Connectors
pg_conn = get_connection()
pg_cursor = pg_conn.cursor()


def callback(ch, method, properties, body):
    order = json.loads(body.decode())
    pg_cursor.execute(
        "INSERT INTO orders (item, quantity, price) VALUES (%s, %s, %s)",
        (order["item"], order["quantity"], order["price"])
    )
    pg_conn.commit()
    r.set(f"order:{order['order_id']}", json.dumps(order))
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"[✓] Processed Order {order['order_id']}")

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=os.getenv("RABBIT_HOST"),
        port=os.getenv("RABBIT_PORT"),
        credentials=pika.PlainCredentials(os.getenv("RABBIT_USER"), os.getenv("RABBIT_PASSWORD"))
    ))
    channel = connection.channel()
    channel.queue_declare(queue=os.getenv("RABBIT_QUEUE"), durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=os.getenv("RABBIT_QUEUE"), on_message_callback=callback)
    print("[*] Waiting for orders...")
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()