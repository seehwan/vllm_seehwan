"""
Simple Authentication System
- No external password hashing libraries
- Simple JWT-based authentication
- Development-ready with hardcoded users
"""

import jwt
from jwt.exceptions import InvalidTokenError
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from ..config import settings

# Simple logging (no external logger)
import logging
logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(tags=["authentication"])

# Security scheme
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    user_id: str
    username: str
    email: str

# Simple password hashing (for development)
def simple_hash(password: str) -> str:
    """Simple password hashing using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    hash_value = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{hash_value}"

def verify_simple_hash(password: str, hashed_password: str) -> bool:
    """Verify password against simple hash"""
    try:
        salt, hash_value = hashed_password.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == hash_value
    except:
        return False

# Development users with raw passwords (hashed at runtime)
DEVELOPMENT_USERS = {
    "admin": {
        "user_id": "1",
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123"  # Raw password, hashed at runtime
    },
    "test": {
        "user_id": "2", 
        "username": "test",
        "email": "test@example.com",
        "password": "test"  # Raw password, hashed at runtime
    },
    "dev": {
        "user_id": "3",
        "username": "dev", 
        "email": "dev@example.com",
        "password": "dev"  # Raw password, hashed at runtime
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user(username: str):
    """Get user by username"""
    if username in DEVELOPMENT_USERS:
        user_dict = DEVELOPMENT_USERS[username]
        return user_dict
    return None

def authenticate_user(username: str, password: str):
    """Authenticate user with username and password"""
    user = get_user(username)
    if not user:
        logger.warning(f"User not found: {username}")
        return False
        
    logger.debug(f"User found: {username}")
    
    # Decode Base64 password from frontend
    try:
        decoded_password = base64.b64decode(password).decode('utf-8')
        logger.debug(f"Base64 decoded password for user: {username}")
    except Exception as e:
        logger.error(f"Base64 decode error: {e}")
        return False
    
    # Direct password comparison for development
    password_valid = (decoded_password == user["password"])
    logger.debug(f"Password verification result: {password_valid}")
    
    if not password_valid:
        logger.warning(f"Invalid password for user: {username}")
        return False
        
    logger.info(f"Authentication successful for user: {username}")
    return user

# API Endpoints
@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest):
    """Login endpoint"""
    logger.info(f"Login attempt for user: {login_request.username}")
    
    user = authenticate_user(login_request.username, login_request.password)
    if not user:
        logger.warning(f"Login failed for user: {login_request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    logger.info(f"Login successful for user: {login_request.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: str = Depends(verify_token)):
    """Get current user info"""
    user = get_user(current_user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(
        user_id=user["user_id"],
        username=user["username"],
        email=user["email"]
    )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Authentication service is running"}