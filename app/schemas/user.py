"""
User Pydantic schemas
======================
Separate schemas for creation, reading, and updates avoid over-posting
(consumers can never supply ``hashed_password`` or ``id`` directly).
"""

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


# ── Inbound ───────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Payload required to register a new user."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=1, max_length=120)


class UserLogin(BaseModel):
    """Credentials for obtaining a JWT access token."""
    email: EmailStr
    password: str


class UserRoleUpdate(BaseModel):
    """Admin-only schema to change a user's role."""
    role: UserRole


# ── Outbound ──────────────────────────────────────────────────────────────────

class UserRead(BaseModel):
    """Safe representation of a user — never includes the password hash."""
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


# ── Token ─────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """Returned by the login endpoint."""
    access_token: str
    token_type: str = "bearer"
    user: UserRead
