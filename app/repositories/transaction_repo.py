"""
Transaction repository
=======================
Handles all database operations for the ``transactions`` table including
advanced filtering, pagination, and sorting.
"""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction, TransactionType
from app.repositories.base import BaseRepository
from app.schemas.transaction import TransactionFilter


class TransactionRepository(BaseRepository[Transaction]):
    """Transaction-specific database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Transaction, db)

    # ── Filtered list with pagination ─────────────────────────────────────────

    async def get_filtered(
        self,
        user_id: str,
        filters: TransactionFilter,
    ) -> tuple[list[Transaction], int]:
        """
        Return a page of transactions matching *filters* plus the total
        count (needed to compute ``total_pages``).

        Returns
        -------
        (records, total_count)
        """
        base_query = select(Transaction).where(Transaction.user_id == user_id)

        # ── Apply filters ──────────────────────────────────────────────────
        if filters.type:
            base_query = base_query.where(Transaction.type == filters.type)
        if filters.category:
            base_query = base_query.where(
                Transaction.category.ilike(f"%{filters.category}%")
            )
        if filters.start_date:
            base_query = base_query.where(Transaction.date >= filters.start_date)
        if filters.end_date:
            base_query = base_query.where(Transaction.date <= filters.end_date)

        # ── Count before pagination ────────────────────────────────────────
        count_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        # ── Sorting ────────────────────────────────────────────────────────
        sort_col = (
            Transaction.date if filters.sort_by == "date" else Transaction.amount
        )
        if filters.sort_order == "desc":
            base_query = base_query.order_by(sort_col.desc())
        else:
            base_query = base_query.order_by(sort_col.asc())

        # ── Pagination ─────────────────────────────────────────────────────
        offset = (filters.page - 1) * filters.page_size
        base_query = base_query.offset(offset).limit(filters.page_size)

        result = await self.db.execute(base_query)
        return list(result.scalars().all()), total

    # ── Analytics helpers ─────────────────────────────────────────────────────

    async def get_all_for_user(self, user_id: str) -> list[Transaction]:
        """Fetch every transaction for a user (used by analytics engine)."""
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.date.asc())
        )
        return list(result.scalars().all())

    async def get_by_user_and_id(
        self, user_id: str, transaction_id: str
    ) -> Optional[Transaction]:
        """Fetch a single transaction belonging to a specific user."""
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id,
            )
        )
        return result.scalars().first()
