import os
import time
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

load_dotenv()

def get_connection(max_retries=5, retry_delay=5):
    """
    Get a database connection with retry logic.
    
    Args:
        max_retries (int): Maximum number of connection attempts
        retry_delay (int): Delay between retries in seconds
        
    Returns:
        psycopg2.connection: A database connection object
        
    Raises:
        psycopg2.OperationalError: If connection fails after all retries
    """
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB", "orders_db"),
                user=os.getenv("POSTGRES_USER", "user"),
                password=os.getenv("POSTGRES_PASSWORD", "password"),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432")
            )
            print("Successfully connected to the database")
            return conn
        except OperationalError as e:
            if attempt == max_retries - 1:  # Last attempt
                print(f"Failed to connect to database after {max_retries} attempts")
                raise e
            print(f"Attempt {attempt + 1} failed: {e}")
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)