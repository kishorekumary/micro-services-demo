import pika
import json
import os
from dotenv import load_dotenv
load_dotenv()

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", "5672"))
RABBIT_QUEUE = os.getenv("RABBIT_QUEUE", "order_queue")
RABBIT_USER = os.getenv("RABBIT_USER", "guest")
RABBIT_PASSWORD = os.getenv("RABBIT_PASSWORD", "guest")

def publish_order(order_data: dict):
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host= RABBIT_HOST, port= RABBIT_PORT, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=RABBIT_QUEUE, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=RABBIT_QUEUE,
        body=json.dumps(order_data),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()