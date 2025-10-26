from fastapi import FastAPI, Form, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from minio_client import upload_file
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import timedelta
import json
import psycopg2
import os
from db import get_connection
from cache import r
from mq import publish_order
from search_client import search_orders
from auth import (
    Token, UserCreate, UserLogin, User, 
    create_access_token, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from user_service import create_user, authenticate_user, create_users_table, create_admin_user
from dotenv import load_dotenv
import time
load_dotenv()

# Check authentication status for documentation
def get_auth_status():
    enable_auth = os.getenv("ENABLE_AUTH", "true").lower() == "true"
    if enable_auth:
        return """
    ### 🔑 Authentication: ENABLED
    
    All order-related endpoints require JWT authentication. 
    Use the `/login` endpoint to get your token.
    
    **Steps:**
    1. Login with admin credentials: `admin` / `admin123`
    2. Copy the JWT token from response
    3. Click "Authorize" button and paste token
    4. Test protected endpoints
    """
    else:
        return """
    ### 🚫 Authentication: DISABLED (Debug Mode)
    
    **⚠️ WARNING: Authentication is currently DISABLED for debugging!**
    
    All endpoints are accessible without authentication.
    You can still use the "Authorize" button, but any token will work.
    
    **To enable authentication:** Set `ENABLE_AUTH=true` in .env file
    """

# Create FastAPI app with enhanced documentation
app = FastAPI(
    title="🛒 Event-Driven Order Management API",
    description=f"""
    ## Order Management System with Authentication
    
    This API provides a complete order management system with:
    
    * **🔐 JWT Authentication** - Secure token-based authentication
    * **📦 Order Management** - Create, search, and retrieve orders
    * **🔍 Elasticsearch Integration** - Full-text search capabilities
    * **📁 File Upload** - Invoice management with MinIO
    * **⚡ Real-time Processing** - RabbitMQ message queues
    
    {get_auth_status()}
    """,
    version="2.0.0",
    contact={
        "name": "Order Management API",
        "email": "admin@example.com",
    },
    license_info={
        "name": "MIT",
    },
)

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

@app.get("/search",
         tags=["📦 Order Management"],
         summary="Search Orders",
         description="Search orders by item name or order ID using Elasticsearch.")
async def search_orders_api(
    q: str, 
    current_user: User = Depends(get_current_active_user)
):
    """
    Search orders using Elasticsearch full-text search.
    
    **Requires:** Valid JWT token in Authorization header
    
    **Parameters:**
    - **q**: Search query (item name or order ID)
    
    **Returns:** List of matching orders
    
    **Examples:**
    - Search by item: `q=laptop`
    - Search by order ID: `q=12345`
    """
    try:
        results = search_orders(q)
        return {"results": results}
    except Exception as e:
        # Return a friendly error if ES is not reachable or query fails
        raise HTTPException(status_code=503, detail=f"Search service error: {e}")


@app.post("/create_order", 
          response_model=OrderResponse,
          tags=["📦 Order Management"],
          summary="Create New Order",
          description="Create a new order and queue it for processing.")
async def create_order(
    item: str = Form(..., description="Product name"), 
    quantity: int = Form(..., description="Quantity (must be > 0)"), 
    price: float = Form(..., description="Price per unit (must be > 0)"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new order and add it to the processing queue.
    
    **Requires:** Valid JWT token in Authorization header
    
    **Form Parameters:**
    - **item**: Product name (required)
    - **quantity**: Number of items (must be > 0)
    - **price**: Price per unit (must be > 0)
    
    **Returns:** Order confirmation with generated order ID
    
    **Process:**
    1. Validates input data
    2. Generates unique order ID
    3. Publishes to RabbitMQ queue
    4. Returns order confirmation
    """
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

@app.get("/orders/{order_id}",
         tags=["📦 Order Management"],
         summary="Get Order by ID",
         description="Retrieve a specific order by its ID from cache or database.")
async def get_order(
    order_id: int, 
    current_user: User = Depends(get_current_active_user)
):
    """
    Get order details by order ID.
    
    **Requires:** Valid JWT token in Authorization header
    
    **Parameters:**
    - **order_id**: Unique order identifier
    
    **Returns:** Order details with source information (cache/database)
    """
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
@app.post("/upload_invoice/",
          tags=["📁 File Management"],
          summary="Upload Invoice",
          description="Upload an invoice file for a specific order to MinIO storage.")
async def upload_invoice(
    order_id: int = Form(..., description="Order ID to associate with the invoice"), 
    file: UploadFile = File(..., description="Invoice file to upload"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload an invoice file for a specific order.
    
    **Requires:** Valid JWT token in Authorization header
    
    **Form Parameters:**
    - **order_id**: Order ID to associate with the invoice
    - **file**: Invoice file (PDF, image, etc.)
    
    **Returns:** Upload confirmation with object path
    
    **Storage:** Files are stored in MinIO under `invoices/{order_id}/`
    """
    file_location = f"/tmp/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    object_name = f"invoices/{order_id}/{file.filename}"
    upload_file(file_location, object_name)
    return {"status": "uploaded", "object": object_name}

# Authentication endpoints
@app.post("/register", 
          response_model=User,
          tags=["🔐 Authentication"],
          summary="Register New User",
          description="Create a new user account with username, email, and password.")
async def register_user(user: UserCreate):
    """
    Register a new user account.
    
    - **username**: Unique username (required)
    - **email**: Valid email address (required)  
    - **full_name**: User's full name (required)
    - **password**: Password (min 6 characters, required)
    """
    # Check if user already exists
    from user_service import get_user_by_username, get_user_by_email
    if get_user_by_username(user.username):
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    if get_user_by_email(user.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    created_user = create_user(user)
    if not created_user:
        raise HTTPException(
            status_code=400,
            detail="User registration failed"
        )
    return created_user

@app.post("/login", 
          response_model=Token,
          tags=["🔐 Authentication"],
          summary="User Login",
          description="Authenticate user and receive JWT token for API access.")
async def login_user(user_credentials: UserLogin):
    """
    Authenticate user and return JWT access token.
    
    **Default Admin Credentials:**
    - **username**: admin
    - **password**: admin123
    
    **Returns:**
    - **access_token**: JWT token for authentication
    - **token_type**: Always "bearer"
    
    **Usage:**
    1. Copy the access_token from response
    2. Click "Authorize" button in Swagger UI
    3. Paste token (without "Bearer" prefix)
    4. Test protected endpoints
    """
    user = authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", 
         response_model=User,
         tags=["🔐 Authentication"],
         summary="Get Current User",
         description="Get information about the currently authenticated user.")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.
    
    **Requires:** Valid JWT token in Authorization header
    
    **Returns:** User profile information
    """
    return current_user

@app.get("/protected",
         tags=["🔐 Authentication"], 
         summary="Test Protected Route",
         description="Example endpoint that requires authentication.")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """
    Example protected route for testing authentication.
    
    **Requires:** Valid JWT token in Authorization header
    
    **Returns:** Welcome message with user's name
    """
    return {"message": f"Hello {current_user.full_name}! This is a protected route."}

# Initialize database and admin user on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and create admin user."""
    try:
        print("🚀 Starting application initialization...")
        create_users_table()
        admin_user = create_admin_user()
        if admin_user:
            print(f"✅ Admin user '{admin_user.username}' is ready")
        else:
            print("⚠️ Admin user creation failed or already exists")
        print("✅ Application startup completed successfully")
    except Exception as e:
        print(f"❌ Startup initialization error: {e}")
        import traceback
        traceback.print_exc()