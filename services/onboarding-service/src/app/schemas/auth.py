"""Authentication schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# Base schemas for reusability
class UserResponse(BaseModel):
    """User information returned in auth responses."""
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None
    email_verified: bool

    class Config:
        from_attributes = True


# ==========================================
# Phase 3: User Story 1 - Email/Password Signin
# ==========================================

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    turnstile_token: Optional[str] = Field(None, description="Cloudflare Turnstile token")
    remember_me: bool = Field(default=False, description="Extend session to 30 days")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!",
                "turnstile_token": "0.abc123...",
                "remember_me": False
            }
        }


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str = Field(..., description="JWT access token (15 min expiry)")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: UserResponse = Field(..., description="Authenticated user information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "expires_in": 900,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "email_verified": True
                }
            }
        }


# ==========================================
# Phase 5: User Story 3 - Session Refresh
# ==========================================

class RefreshResponse(BaseModel):
    """Token refresh response schema."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }


# ==========================================
# Phase 6: User Story 4 - Logout
# ==========================================

class LogoutResponse(BaseModel):
    """Logout response schema."""
    message: str = Field(..., description="Confirmation message")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Logged out successfully"
            }
        }


# Audit log schemas
class AuthAuditLogResponse(BaseModel):
    """Auth audit log entry response."""
    id: str
    timestamp: datetime
    event_type: str
    user_id: Optional[str] = None
    email_attempted: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    result: str

    class Config:
        from_attributes = True
