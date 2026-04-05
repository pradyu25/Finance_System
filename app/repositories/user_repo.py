"""
User repository
================
Handles all database operations related to the ``users`` table.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User-specific database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Look up a user by their unique email address."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    async def email_exists(self, email: str) -> bool:
        """Return True if the email address is already registered."""
        return await self.get_by_email(email) is not None
