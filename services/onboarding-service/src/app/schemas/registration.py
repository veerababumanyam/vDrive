"""
Registration schemas for user signup.
"""

import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegistrationRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["photographer@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8+ chars, uppercase, lowercase, number, special char)",
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's first name",
        examples=["John"],
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's last name",
        examples=["Photographer"],
    )
    business_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Photography business name",
        examples=["Lumina Photography Studio"],
    )
    turnstile_token: str = Field(
        ...,
        description="Cloudflare Turnstile verification token",
    )
    agree_to_terms: bool = Field(
        ...,
        description="User accepts Terms of Service",
    )
    agree_to_privacy: bool = Field(
        ...,
        description="User accepts Privacy Policy",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets strength requirements.

        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        errors = []

        if len(v) < 8:
            errors.append("Password must be at least 8 characters")

        if not any(c.isupper() for c in v):
            errors.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in v):
            errors.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in v):
            errors.append("Password must contain at least one number")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            errors.append("Password must contain at least one special character")

        if errors:
            raise ValueError("; ".join(errors))

        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from names."""
        return v.strip()

    @field_validator("agree_to_terms", "agree_to_privacy")
    @classmethod
    def must_be_true(cls, v: bool, info) -> bool:
        """Terms and privacy must be accepted."""
        if not v:
            field_name = info.field_name.replace("_", " ").title()
            raise ValueError(f"{field_name} must be accepted")
        return v


class RegistrationResponse(BaseModel):
    """Response schema for successful registration."""

    user_id: str = Field(
        ...,
        description="UUID of the created user",
    )
    email: str = Field(
        ...,
        description="User's email address",
    )
    email_verified: bool = Field(
        default=False,
        description="Whether email is verified",
    )
    message: str = Field(
        default="Registration successful. Please check your email to verify your account.",
        description="Success message",
    )
    access_token: str = Field(
        ...,
        description="JWT access token",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "photographer@example.com",
                "email_verified": False,
                "message": "Registration successful. Please check your email to verify your account.",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }


class EmailCheckRequest(BaseModel):
    """Request schema for email availability check."""

    email: EmailStr = Field(
        ...,
        description="Email address to check",
    )


class EmailCheckResponse(BaseModel):
    """Response schema for email availability check."""

    available: bool = Field(
        ...,
        description="Whether the email is available",
    )
    message: str = Field(
        ...,
        description="Availability message",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "available": True,
                    "message": "Email is available",
                },
                {
                    "available": False,
                    "message": "An account with this email already exists",
                },
            ]
        }
