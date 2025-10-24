import pika
import json
import time

connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq.docker'))
channel = connection.channel()
channel.queue_declare(queue='order_queue', durable=True)

for order_id in range(1400, 1405):
    order = {
        "order_id": order_id,
        "item": f"Product-{order_id}",
        "quantity": order_id * 2,
        "price": 99.5 * order_id
    }
    channel.basic_publish(
        exchange='',
        routing_key='order_queue',
        body=json.dumps(order),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    print(f"[x] Sent Order: {order}")
    time.sleep(1)

connection.close()