from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv

load_dotenv()

ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")

es = Elasticsearch(ES_HOST)

def ensure_index():
    if not es.indices.exists(index="orders"):
        es.indices.create(index="orders", mappings={
            "properties": {
                "order_id": {"type": "integer"},
                "item": {"type": "text"},
                "quantity": {"type": "integer"},
                "price": {"type": "float"},
                "created_at": {"type": "date"}
            }
        })

def index_order(order: dict):
    ensure_index()
    es.index(index="orders", id=order["order_id"], document=order)
    print(f"✅ Indexed order {order['order_id']} in Elasticsearch")

def search_orders(query: str):
    # Ensure index exists to avoid index_not_found_exception on first search
    ensure_index()
    should_clauses = [
        {"match": {"item": query}}
    ]
    # If the query is numeric, also try to match order_id exactly
    q = query.strip()
    if q.isdigit():
        try:
            should_clauses.append({"term": {"order_id": int(q)}})
        except ValueError:
            pass

    res = es.search(
        index="orders",
        query={"bool": {"should": should_clauses}}
    )
    return [hit["_source"] for hit in res["hits"]["hits"]]