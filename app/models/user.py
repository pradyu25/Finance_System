"""
User ORM model
==============
Maps to the ``users`` table.  Passwords are stored only as bcrypt hashes
and the plain-text password is never persisted.
"""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, String
from sqlalchemy import Enum as SaEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRole(str, PyEnum):
    """Three-tier role hierarchy for access control."""
    viewer = "viewer"       # Read-only access
    analyst = "analyst"     # Filters + analytics
    admin = "admin"         # Full CRUD + user management


class User(Base, TimestampMixin):
    """Represents a registered user of the Finance Intelligence System."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SaEnum(UserRole), default=UserRole.viewer, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # One-to-many: each user owns many transactions
    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        "Transaction", back_populates="owner", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r} role={self.role}>"
