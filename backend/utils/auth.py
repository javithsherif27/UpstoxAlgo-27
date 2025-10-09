"""
Authentication utilities for order management
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

security = HTTPBearer(auto_error=False)

async def get_access_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Extract access token from Authorization header"""
    if not credentials:
        # For development/testing, allow without token
        # In production, this should raise an exception
        return "dummy_token_for_development"
    
    return credentials.credentials

async def get_current_user(access_token: str = Depends(get_access_token)) -> dict:
    """Get current user information from access token"""
    # This is a placeholder - implement actual token validation
    # In production, validate the token against Upstox or your auth system
    return {
        "user_id": "test_user",
        "access_token": access_token
    }