from datetime import datetime, timedelta
from typing import Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.config.database import get_db

# JWT token security scheme
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data (dict): Data to encode in the token
        expires_delta (timedelta, optional): Token expiration time. Defaults to None.
    
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Encode JWT
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def decode_token(token: str) -> Dict:
    """
    Decode and validate a JWT token
    
    Args:
        token (str): JWT token to decode
    
    Returns:
        Dict: Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

import structlog
from app.models.user import User
logger = structlog.get_logger("analisaai-auth")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get the current authenticated user from JWT token, fetch from DB, check is_active.
    """
    token_data = decode_token(credentials.credentials)
    user_id = token_data.get("sub")
    if not user_id:
        logger.warning("Token missing subject (sub)")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing subject")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning("User not found", user_id=user_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        logger.info("Inactive user tried to authenticate", user_id=user_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    # Retorne um dicionário seguro com informações relevantes
    user_info = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "roles": [role.name for role in user.roles],
        "is_admin": user.has_role("admin")
    }
    return user_info

async def get_admin_user(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Check if current user is an admin (via role).
    """
    if not current_user.get("is_admin"):
        logger.info("User without admin role tried to access admin resource", user_id=current_user.get("id"))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions (admin required)",
        )
    return current_user