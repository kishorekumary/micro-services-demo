# 🔐 Authentication System

This document describes the JWT-based authentication system implemented for the Order Management System.

## Features

- **JWT Token Authentication** - Secure token-based authentication
- **User Registration & Login** - Complete user management system
- **Protected Routes** - All order operations require authentication
- **Admin Account** - Default admin account created from environment variables
- **React Frontend** - Beautiful login/registration UI with context-based state management

## Backend Components

### 1. Authentication Module (`app/auth.py`)
- JWT token creation and verification
- Password hashing with bcrypt
- Authentication middleware
- Token validation decorators

### 2. User Service (`app/user_service.py`)
- User CRUD operations
- Database table creation
- Admin account initialization
- User authentication logic

### 3. Protected Endpoints
All the following endpoints now require authentication:
- `POST /create_order` - Create new orders
- `GET /search` - Search orders
- `GET /orders/{order_id}` - Get specific order
- `POST /upload_invoice/` - Upload invoice files

### 4. Authentication Endpoints
- `POST /register` - Register new user
- `POST /login` - User login (returns JWT token)
- `GET /me` - Get current user info
- `GET /protected` - Example protected route

## Frontend Components

### 1. Authentication Context (`frontend/src/contexts/AuthContext.js`)
- Centralized authentication state management
- Automatic token handling with axios interceptors
- Login/logout functionality
- User registration

### 2. Login Component (`frontend/src/components/Login.js`)
- User-friendly login form
- Error handling and validation
- Admin credentials display

### 3. Registration Component (`frontend/src/components/Register.js`)
- New user registration form
- Password confirmation
- Form validation

### 4. Header Component (`frontend/src/components/Header.js`)
- User welcome message
- Logout functionality
- Modern UI design

## Environment Variables

Add these to your `app/.env` file:

```bash
# 🔐 Authentication configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-please
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 👤 Default admin account
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
ADMIN_FULL_NAME=System Administrator
```

## Default Admin Account

The system automatically creates an admin account on startup:
- **Username:** `admin` (configurable via `ADMIN_USERNAME`)
- **Password:** `admin123` (configurable via `ADMIN_PASSWORD`)
- **Email:** `admin@example.com` (configurable via `ADMIN_EMAIL`)

## How to Use

### 1. Start the System
```bash
docker-compose up --build
```

### 2. Access the Frontend
Open http://localhost:4000 in your browser

### 3. Login Options
- **Admin Login:** Use `admin` / `admin123`
- **New User:** Click "Register here" to create a new account

### 4. API Usage
For direct API access, include the JWT token in the Authorization header:
```bash
# Login to get token
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token for protected endpoints
curl -X GET http://localhost:8000/search?q=pc \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Testing

Run the authentication test script:
```bash
python test_auth.py
```

This will test:
- Admin login
- Protected route access
- Order creation with auth
- Order search with auth
- User registration
- New user login
- Unauthorized access blocking

## Security Features

### 1. Password Security
- Passwords are hashed using bcrypt
- Minimum password length validation
- Secure password storage

### 2. JWT Security
- Configurable secret key
- Token expiration (30 minutes default)
- Secure token validation

### 3. Route Protection
- All sensitive endpoints require authentication
- Automatic token validation
- Proper error responses for unauthorized access

### 4. Frontend Security
- Automatic token storage in localStorage
- Axios interceptors for token handling
- Automatic logout on token expiration
- Protected route rendering

## Database Schema

The system creates a `users` table with the following structure:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    disabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Troubleshooting

### 1. "Could not validate credentials" Error
- Check if JWT_SECRET_KEY is set correctly
- Verify token hasn't expired
- Ensure Authorization header format: `Bearer <token>`

### 2. "Username already registered" Error
- User already exists in database
- Try different username or use existing credentials

### 3. Frontend Login Issues
- Check if backend is running on port 8000
- Verify CORS settings
- Check browser console for errors

### 4. Database Connection Issues
- Ensure PostgreSQL is running
- Check database connection parameters
- Verify users table was created

## Production Considerations

### 1. Security
- Change `JWT_SECRET_KEY` to a strong, random value
- Use HTTPS in production
- Set secure admin credentials
- Consider token refresh mechanism

### 2. Environment Variables
- Use proper secret management
- Don't commit sensitive values to git
- Use different credentials per environment

### 3. Database
- Use connection pooling
- Implement proper backup strategy
- Monitor user table growth

## API Documentation

The authentication endpoints are automatically documented in the FastAPI Swagger UI:
- Visit http://localhost:8000/docs
- All endpoints show authentication requirements
- Interactive testing with token authentication
