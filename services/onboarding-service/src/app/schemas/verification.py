"""
Email verification schemas.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class VerifyEmailRequest(BaseModel):
    """Request schema for email verification."""

    token: str = Field(
        ...,
        min_length=1,
        description="Email verification token from the link",
    )


class VerificationResponse(BaseModel):
    """Response schema for email verification."""

    user_id: str = Field(
        ...,
        description="UUID of the verified user",
    )
    email: str = Field(
        ...,
        description="User's email address",
    )
    email_verified: bool = Field(
        default=True,
        description="Email verification status",
    )
    message: str = Field(
        default="Email verified successfully",
        description="Success message",
    )
    access_token: str = Field(
        ...,
        description="New JWT access token with updated claims",
    )
    redirect_url: str = Field(
        ...,
        description="URL to redirect user to next step",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "photographer@example.com",
                "email_verified": True,
                "message": "Email verified successfully",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "redirect_url": "/onboarding/workspace",
            }
        }


class ResendVerificationRequest(BaseModel):
    """Request schema for resending verification email."""

    email: EmailStr = Field(
        ...,
        description="Email address to resend verification to",
    )


class ResendVerificationResponse(BaseModel):
    """Response schema for resend verification."""

    message: str = Field(
        default="Verification email sent",
        description="Success message",
    )
    email: str = Field(
        ...,
        description="Email address where verification was sent",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Verification email sent. Please check your inbox.",
                "email": "photographer@example.com",
            }
        }
