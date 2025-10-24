import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()
def get_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "orders_db"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )
    return conn