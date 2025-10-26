# 🔐 Swagger UI Authentication Guide

## How to Test Protected APIs in Swagger UI

### Step 1: Access Swagger UI
Open your browser and navigate to:
```
http://localhost:8000/docs
```

### Step 2: Login to Get JWT Token

1. **Find the Login Endpoint**
   - Look for the "🔐 Authentication" section
   - Click on `POST /login`

2. **Execute Login**
   - Click "Try it out"
   - Enter credentials:
     ```json
     {
       "username": "admin",
       "password": "admin123"
     }
     ```
   - Click "Execute"

3. **Copy the Token**
   - From the response, copy the `access_token` value
   - Example: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### Step 3: Authorize in Swagger UI

1. **Click the "Authorize" Button**
   - Look for the 🔒 "Authorize" button at the top right
   - Click it to open the authorization dialog

2. **Enter the JWT Token**
   - Paste your token in the "Value" field
   - **Important:** Enter ONLY the token (without "Bearer" prefix)
   - Click "Authorize"
   - Click "Close"

### Step 4: Test Protected Endpoints

Now you can test any protected endpoint:

#### 📦 Order Management
- `GET /search` - Search orders
- `POST /create_order` - Create new order
- `GET /orders/{order_id}` - Get order by ID

#### 🔐 Authentication  
- `GET /me` - Get current user info
- `GET /protected` - Test authentication

#### 📁 File Management
- `POST /upload_invoice/` - Upload invoice files

### Example API Usage with curl

```bash
# 1. Login to get token
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response: {"access_token": "YOUR_JWT_TOKEN", "token_type": "bearer"}

# 2. Use token for protected endpoints
curl -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 3. Create an order
curl -X POST "http://localhost:8000/create_order" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "item=Laptop" \
  -F "quantity=1" \
  -F "price=999.99"

# 4. Search orders
curl -X GET "http://localhost:8000/search?q=Laptop" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Troubleshooting

#### ❌ "Could not validate credentials"
- Check if token is correctly copied (no extra spaces)
- Ensure token hasn't expired (30 minutes default)
- Re-login to get a fresh token

#### ❌ "Method Not Allowed" (405)
- Make sure containers are running: `docker-compose up`
- Check if backend is accessible at `http://localhost:8000`

#### ❌ "Unauthorized" (401)
- Click "Authorize" button and enter your JWT token
- Make sure you're using the correct admin credentials

### API Features

#### 🔍 **Search Capabilities**
- Search by item name: `q=laptop`
- Search by order ID: `q=12345`
- Full-text search powered by Elasticsearch

#### 📊 **Order Processing**
- Real-time order processing with RabbitMQ
- Automatic indexing in Elasticsearch
- Redis caching for fast retrieval

#### 📁 **File Management**
- Upload invoices to MinIO storage
- Organized by order ID
- Supports multiple file formats

### Security Notes

- JWT tokens expire after 30 minutes
- All order operations require authentication
- Passwords are securely hashed with bcrypt
- Admin account is created automatically on startup

### Default Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@example.com`

You can also register new users via the `/register` endpoint!
