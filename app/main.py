from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from minio_client import upload_file
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import psycopg2
import os
from db import get_connection
from cache import r
from mq import publish_order
from search_client import search_orders
from dotenv import load_dotenv
import time
load_dotenv()

app = FastAPI(title="Event-Driven Order App")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class OrderCreate(BaseModel):
    item: str
    quantity: int
    price: float

class OrderResponse(BaseModel):
    order_id: int
    item: str
    quantity: int
    price: float
    status: str


@app.get("/", response_class=HTMLResponse)
def index():
    html = """
    <h2>Order Management App</h2>
    <form action="/create_order" method="post">
        Item: <input name="item"><br>
        Quantity: <input name="quantity" type="number"><br>
        Price: <input name="price" type="number"><br>
        <button type="submit">Create Order</button>
    </form>
    """
    return html

@app.get("/search")
async def search_orders_api(q: str):
    try:
        results = search_orders(q)
        return {"results": results}
    except Exception as e:
        # Return a friendly error if ES is not reachable or query fails
        raise HTTPException(status_code=503, detail=f"Search service error: {e}")


@app.post("/create_order", response_model=OrderResponse)
async def create_order(item: str = Form(...), quantity: int = Form(...), price: float = Form(...)):
    try:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
        if price <= 0:
            raise HTTPException(status_code=400, detail="Price must be greater than 0")
        order_id = int(quantity * 1000) + int(time.time()*1000) % 10000
        # Create a dictionary with all order data including the generated order_id
        order_data = {
            "order_id": order_id,
            "item": item,
            "quantity": quantity,
            "price": price,
            "status": "created"
        }
        publish_order(order_data)
        return {"status": "Order queued", "order_id": order_id, "item": item, "quantity": quantity, "price": price}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    cached = r.get(f"order:{order_id}")
    if cached:
        return {"source": "cache", "order": json.loads(cached)}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT order_id, item, quantity, price FROM orders WHERE order_id = %s", (order_id,))
    row = cur.fetchone()
    if not row:
        return {"error": "Order not found"}
    order = {"order_id": row[0], "item": row[1], "quantity": row[2], "price": float(row[3])}
    r.set(f"order:{order_id}", json.dumps(order), ex=300)
    return {"source": "database", "order": order}
@app.post("/upload_invoice/")
async def upload_invoice(order_id: int = Form(...), file: UploadFile = File(...)):
    file_location = f"/tmp/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    object_name = f"invoices/{order_id}/{file.filename}"
    upload_file(file_location, object_name)
    return {"status": "uploaded", "object": object_name}