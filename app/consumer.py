import pika
import psycopg2
import psycopg2.pool
import redis
import json
import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps

from db import get_connection
from cache import r
from dotenv import load_dotenv
from search_client import index_order
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('consumer.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connection pool
db_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    **{
        'dbname': os.getenv("POSTGRES_DB", "orders_db"),
        'user': os.getenv("POSTGRES_USER", "user"),
        'password': os.getenv("POSTGRES_PASSWORD", "password"),
        'host': os.getenv("POSTGRES_HOST", "localhost"),
        'port': os.getenv("POSTGRES_PORT", "5432")
    }
)

def get_db_connection():
    """Get a connection from the connection pool."""
    return db_pool.getconn()

def release_db_connection(conn):
    """Release a connection back to the pool."""
    db_pool.putconn(conn)

def with_db_connection(func):
    """Decorator to handle database connection for a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = get_db_connection()
        try:
            result = func(conn, *args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                release_db_connection(conn)
    return wrapper

def validate_order(order: Dict[str, Any]) -> bool:
    """Validate the order data structure."""
    required_fields = ['order_id', 'item', 'quantity', 'price']
    return all(field in order for field in required_fields) and \
           isinstance(order['quantity'], (int, float)) and \
           isinstance(order['price'], (int, float)) and \
           order['quantity'] > 0 and order['price'] > 0

@with_db_connection
def process_order(conn, order: Dict[str, Any]) -> None:
    """Process a single order and store it in the database and cache."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO orders (order_id, item, quantity, price)
            VALUES (%(order_id)s, %(item)s, %(quantity)s, %(price)s)
            RETURNING order_id
            """,
            {
                'order_id': order['order_id'],
                'item': order['item'],
                'quantity': order['quantity'],
                'price': order['price']
            }
        )
        conn.commit()
        
        # Cache the order with TTL (1 hour)
        r.setex(
            f"order:{order['order_id']}", 
            3600,  # 1 hour TTL
            json.dumps(order)
        )
        # Index into Elasticsearch (non-blocking for processing flow)
        try:
            index_order(order)
            logger.info(f"Indexed order {order['order_id']} in Elasticsearch")
        except Exception as e:
            logger.warning(f"Failed to index order {order['order_id']}: {e}")
        logger.info(f"Processed order {order['order_id']}")

def get_rabbitmq_connection():
    """Create and return a RabbitMQ connection with retry logic."""
    retries = 0
    max_retries = 5
    backoff = 5  # seconds
    
    while retries < max_retries:
        try:
            credentials = pika.PlainCredentials(
                os.getenv("RABBIT_USER", "guest"),
                os.getenv("RABBIT_PASSWORD", "guest")
            )
            parameters = pika.ConnectionParameters(
                host=os.getenv("RABBIT_HOST", "localhost"),
                port=int(os.getenv("RABBIT_PORT", "5672")),
                credentials=credentials,
                connection_attempts=3,
                retry_delay=5,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            return pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError as e:
            retries += 1
            if retries == max_retries:
                logger.error("Max retries reached. Could not connect to RabbitMQ.")
                raise
            logger.warning(f"Failed to connect to RabbitMQ. Retrying in {backoff} seconds...")
            time.sleep(backoff)
            backoff *= 2  # Exponential backoff

def on_message(channel, method_frame, header_frame, body):
    """Callback for processing incoming messages."""
    try:
        order = json.loads(body.decode())
        
        if not validate_order(order):
            logger.error(f"Invalid order format: {order}")
            channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=False)
            return
            
        process_order(order)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        
    except json.JSONDecodeError:
        logger.error("Failed to decode message")
        channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Error processing order: {e}", exc_info=True)
        channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=False)

def delete_existing_queue(channel, queue_name):
    """Delete the queue if it exists."""
    try:
        # First try to delete with if_empty=False (delete even if not empty)
        channel.queue_delete(queue=queue_name, if_empty=False, if_unused=False)
        logger.info(f"Deleted existing queue: {queue_name}")
        return True
    except pika.exceptions.ChannelClosedByBroker as e:
        if e.reply_code == 404:  # Queue doesn't exist
            logger.info(f"Queue {queue_name} doesn't exist, nothing to delete")
            return False
        elif 'PRECONDITION_FAILED' in str(e):
            logger.warning(f"Could not delete queue {queue_name}: {e}")
            return False
        else:
            logger.error(f"Error deleting queue {queue_name}: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error deleting queue {queue_name}: {e}")
        return False

def setup_queue_with_dlx(channel, queue_name):
    """Set up the queue with dead-letter exchange."""
    # Declare dead-letter exchange if it doesn't exist
    channel.exchange_declare(
        exchange='dlx',
        exchange_type='direct',
        durable=True
    )
    
    # Declare DLX queue if it doesn't exist
    channel.queue_declare(
        queue='dlx.queue',
        durable=True
    )
    channel.queue_bind(
        exchange='dlx',
        queue='dlx.queue',
        routing_key='dlx.queue'
    )
    
    # First try to delete any existing queue
    delete_existing_queue(channel, queue_name)
    
    # Now declare the queue with DLX arguments
    try:
        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'dlx',
                'x-dead-letter-routing-key': 'dlx.queue'
            }
        )
    except pika.exceptions.ChannelClosedByBroker as e:
        if 'inequivalent arg' in str(e):
            # If we can't declare with DLX, try without it
            logger.warning("Could not declare queue with DLX, trying without...")
            channel = connection.channel()  # Get a new channel
            channel.queue_declare(
                queue=queue_name,
                durable=True
            )

def start_consumer():
    """Start the RabbitMQ consumer."""
    while True:
        try:
            connection = get_rabbitmq_connection()
            channel = connection.channel()
            
            # Set up queue with DLX
            queue_name = os.getenv("RABBIT_QUEUE", "order_queue")
            setup_queue_with_dlx(channel, queue_name)
            
            # Set prefetch count
            channel.basic_qos(prefetch_count=10)
            
            # Start consuming
            channel.basic_consume(
                queue=os.getenv("RABBIT_QUEUE", "order_queue"),
                on_message_callback=on_message,
                auto_ack=False
            )
            
            logger.info("[*] Waiting for messages. To exit press CTRL+C")
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError:
            logger.error("Connection lost. Reconnecting...")
            time.sleep(5)
            continue
        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
            if 'connection' in locals() and connection.is_open:
                connection.close()
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            time.sleep(5)
            continue

def callback(ch, method, properties, body):
    order = json.loads(body.decode())
    index_order(order)
    ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":
    logger.info("Starting order processing consumer...")
    start_consumer()