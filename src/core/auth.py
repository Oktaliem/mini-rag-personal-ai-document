"""
Core authentication logic.

This module contains the core authentication business logic.
"""

from datetime import datetime, timedelta
from typing import Optional, Set, Dict, Any
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from .config import settings
from .models import User, UserCreate, UserLogin, Token, TokenData


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token blacklist (in production, use Redis or database)
BLACKLISTED_TOKENS: Set[str] = set()
BLACKLISTED_REFRESH_TOKENS: Set[str] = set()

# In-memory user database (in production, use real database)
USERS_DB: Dict[str, Dict[str, Any]] = {}

# JWT Configuration
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password."""
    user_data = USERS_DB.get(username)
    if not user_data:
        return None
    
    if not verify_password(password, user_data["hashed_password"]):
        return None
    
    if not user_data["is_active"]:
        return None
    
    return User(**user_data)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.refresh_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
        return token_data
    except jwt.JWTError:
        return None


def get_current_user(token: str) -> Optional[User]:
    """Get current user from token."""
    token_data = verify_token(token)
    if token_data is None:
        return None

    username = token_data.username
    if username is None:
        return None

    user_data = USERS_DB.get(username)
    if user_data is None:
        return None
    
    return User(**user_data)


def get_current_active_user(token: str) -> User:
    """Get current active user from token."""
    user = get_current_user(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_admin_user(token: str) -> User:
    """Get current admin user from token."""
    user = get_current_active_user(token)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return user


def get_current_user_from_token(token: str) -> Optional[User]:
    """Get current user from token (for API dependencies)."""
    if is_token_blacklisted(token):
        return None
    return get_current_user(token)


def get_current_active_user_from_token_sync(token: str) -> Optional[User]:
    """Get current active user from token (sync helper for dependencies)."""
    user = get_current_user_from_token(token)
    if user and not user.is_active:
        return None
    return user


async def get_current_active_user_from_token(token: Optional[str] = None) -> User:
    """Get current active user from token parameter (async version for API docs)."""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    
    user = get_current_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


def blacklist_token(token: str) -> None:
    """Add token to blacklist."""
    BLACKLISTED_TOKENS.add(token)


def blacklist_refresh_token(token: str) -> None:
    """Add refresh token to blacklist."""
    BLACKLISTED_REFRESH_TOKENS.add(token)


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted."""
    return token in BLACKLISTED_TOKENS


def is_refresh_blacklisted(token: str) -> bool:
    """Check if refresh token is blacklisted."""
    return token in BLACKLISTED_REFRESH_TOKENS


def create_user(user_data: UserCreate) -> User:
    """Create a new user."""
    if user_data.username in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]
    
    USERS_DB[user_data.username] = user_dict
    
    return User(**user_dict)


def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username."""
    user_data = USERS_DB.get(username)
    if user_data:
        return User(**user_data)
    return None


def update_user(username: str, user_data: dict) -> Optional[User]:
    """Update user data."""
    if username not in USERS_DB:
        return None
    
    USERS_DB[username].update(user_data)
    return User(**USERS_DB[username])


def delete_user(username: str) -> bool:
    """Delete a user."""
    if username in USERS_DB:
        del USERS_DB[username]
        return True
    return False


def initialize_default_users() -> None:
    """Initialize default users with properly hashed passwords."""
    default_users = {
        "admin": {
            "username": "admin",
            "password": "admin123",  # Change this in production!
            "email": "admin@example.com",
            "full_name": "Administrator",
            "role": "admin"
        },
        "user": {
            "username": "user", 
            "password": "user123",  # Change this in production!
            "email": "user@example.com",
            "full_name": "Regular User",
            "role": "user"
        }
    }
    
    for username, user_data in default_users.items():
        hashed_password = get_password_hash(user_data["password"])
        USERS_DB[username] = {
            "username": username,
            "hashed_password": hashed_password,
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "is_active": True,
            "role": user_data["role"]
        }
        print(f"Initialized user: {username}")


# Initialize users on import
initialize_default_users()
