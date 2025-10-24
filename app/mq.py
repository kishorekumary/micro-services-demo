import pika
import json
import os
import time
import logging
from typing import Dict, Any, Optional
from functools import wraps
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# RabbitMQ configuration
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", "5672"))
RABBIT_QUEUE = os.getenv("RABBIT_QUEUE", "order_queue")
RABBIT_USER = os.getenv("RABBIT_USER", "guest")
RABBIT_PASSWORD = os.getenv("RABBIT_PASSWORD", "guest")

class RabbitMQPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ with retry logic."""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=RABBIT_HOST,
                        port=RABBIT_PORT,
                        credentials=credentials,
                        heartbeat=600,
                        blocked_connection_timeout=300,
                        connection_attempts=3,
                        retry_delay=5
                    )
                )
                self.channel = self.connection.channel()
                self.connected = True
                logger.info("Connected to RabbitMQ")
                return
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to connect to RabbitMQ after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
    
    def ensure_connection(self):
        """Ensure we have a valid connection."""
        if not self.connected or not self.connection or self.connection.is_closed:
            self._connect()
    
    def publish_order(self, order_data: Dict[str, Any]) -> bool:
        """Publish an order to the queue.
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            self.ensure_connection()
            
            # Declare queue without any special arguments to avoid conflicts
            self.channel.queue_declare(
                queue=RABBIT_QUEUE,
                durable=True,
                passive=True  # Only check if queue exists, don't modify it
            )
            
            # Publish the message
            self.channel.basic_publish(
                exchange='',
                routing_key=RABBIT_QUEUE,
                body=json.dumps(order_data),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            logger.info(f"Published order {order_data.get('order_id')} to {RABBIT_QUEUE}")
            return True
            
        except pika.exceptions.ChannelClosedByBroker as e:
            logger.error(f"Channel error: {e}")
            self.connected = False
            return False
            
        except pika.exceptions.AMQPChannelError as e:
            logger.error(f"Channel error: {e}")
            self.connected = False
            return False
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return False
    
    def close(self):
        """Close the connection."""
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
                logger.info("Closed RabbitMQ connection")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
        finally:
            self.connected = False

# Create a singleton instance
publisher = RabbitMQPublisher()

def publish_order(order_data: Dict[str, Any]) -> bool:
    """Publish an order to the queue.
    
    This is a convenience wrapper around the RabbitMQPublisher class.
    """
    try:
        return publisher.publish_order(order_data)
    except Exception as e:
        logger.error(f"Failed to publish order: {e}", exc_info=True)
        return False