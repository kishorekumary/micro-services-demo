import psycopg2
import os
from typing import Optional
from auth import User, UserInDB, UserCreate, get_password_hash, verify_password
from db import get_connection
import logging

logger = logging.getLogger(__name__)

def create_users_table():
    """Create users table if it doesn't exist."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    disabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("Users table created successfully")
    except Exception as e:
        logger.error(f"Error creating users table: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Get user by username."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT username, email, full_name, hashed_password, disabled FROM users WHERE username = %s",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return UserInDB(
                    username=row[0],
                    email=row[1],
                    full_name=row[2],
                    hashed_password=row[3],
                    disabled=row[4]
                )
            return None
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT username, email, full_name, hashed_password, disabled FROM users WHERE email = %s",
                (email,)
            )
            row = cursor.fetchone()
            if row:
                return UserInDB(
                    username=row[0],
                    email=row[1],
                    full_name=row[2],
                    hashed_password=row[3],
                    disabled=row[4]
                )
            return None
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None
    finally:
        conn.close()

def create_user(user: UserCreate) -> Optional[User]:
    """Create a new user."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            hashed_password = get_password_hash(user.password)
            cursor.execute(
                """
                INSERT INTO users (username, email, full_name, hashed_password)
                VALUES (%s, %s, %s, %s)
                RETURNING username, email, full_name, disabled
                """,
                (user.username, user.email, user.full_name, hashed_password)
            )
            row = cursor.fetchone()
            conn.commit()
            if row:
                return User(
                    username=row[0],
                    email=row[1],
                    full_name=row[2],
                    disabled=row[3]
                )
            return None
    except psycopg2.IntegrityError as e:
        logger.error(f"User creation failed - duplicate entry: {e}")
        conn.rollback()
        return None
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password."""
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_admin_user():
    """Create default admin user from environment variables."""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_full_name = os.getenv("ADMIN_FULL_NAME", "System Administrator")
    
    logger.info(f"Creating admin user with username: '{admin_username}'")
    
    # Check if admin user already exists
    existing_admin = get_user_by_username(admin_username)
    if existing_admin:
        logger.info(f"Admin user '{admin_username}' already exists")
        return existing_admin
    
    # Validate password length for bcrypt
    if len(admin_password.encode('utf-8')) > 72:
        logger.warning(f"Admin password is too long ({len(admin_password.encode('utf-8'))} bytes), truncating to 72 bytes")
        admin_password = admin_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    
    # Create admin user
    try:
        admin_user = UserCreate(
            username=admin_username,
            email=admin_email,
            full_name=admin_full_name,
            password=admin_password
        )
        
        created_user = create_user(admin_user)
        if created_user:
            logger.info(f"Admin user '{admin_username}' created successfully")
        else:
            logger.error(f"Failed to create admin user '{admin_username}'")
        
        return created_user
    except Exception as e:
        logger.error(f"Error during admin user creation: {e}")
        return None
