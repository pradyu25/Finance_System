"""
Generic CRUD base repository
==============================
Provides reusable ``get``, ``get_all``, ``create``, ``update``, and
``delete`` operations that concrete repositories inherit from, avoiding
repetitive boilerplate across the codebase.
"""

from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic async CRUD repository.

    Parameters
    ----------
    model:
        The SQLAlchemy ORM class this repository manages.
    db:
        An open ``AsyncSession`` injected per-request.
    """

    def __init__(self, model: Type[ModelT], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, record_id: str) -> Optional[ModelT]:
        """Return the record with *record_id* or ``None`` if not found."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == record_id)  # type: ignore[attr-defined]
        )
        return result.scalars().first()

    async def get_all(self) -> list[ModelT]:
        """Return every row for this model (use carefully on large tables)."""
        result = await self.db.execute(select(self.model))
        return list(result.scalars().all())

    async def create(self, obj: ModelT) -> ModelT:
        """Persist *obj* and refresh it so generated columns are populated."""
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: ModelT, updates: dict) -> ModelT:
        """Apply *updates* dict to *obj*, commit, and return the refreshed instance."""
        for field, value in updates.items():
            if value is not None:
                setattr(obj, field, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        """Delete *obj* from the database."""
        await self.db.delete(obj)
        await self.db.commit()
