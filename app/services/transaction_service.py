"""
Transaction service
====================
All business logic for CRUD operations on transactions.  The service
layer validates business rules that Pydantic cannot (e.g. ownership
checks) and orchestrates repository calls.
"""

import math

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.transaction import Transaction
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilter,
    TransactionRead,
    TransactionUpdate,
)


class TransactionService:
    """Business logic for financial transaction management."""

    def __init__(self, repo: TransactionRepository):
        self._repo = repo

    # ── Create ─────────────────────────────────────────────────────────────

    async def create(self, user_id: str, payload: TransactionCreate) -> TransactionRead:
        """Create a new transaction owned by *user_id*."""
        txn = Transaction(
            user_id=user_id,
            amount=payload.amount,
            type=payload.type,
            category=payload.category,
            date=payload.date,
            description=payload.description,
        )
        created = await self._repo.create(txn)
        return TransactionRead.model_validate(created)

    # ── Read ───────────────────────────────────────────────────────────────

    async def get_one(self, user_id: str, transaction_id: str) -> TransactionRead:
        """
        Fetch a single transaction.

        Raises
        ------
        NotFoundError
            If the transaction does not exist or does not belong to *user_id*.
        """
        txn = await self._repo.get_by_user_and_id(user_id, transaction_id)
        if not txn:
            raise NotFoundError(f"Transaction '{transaction_id}' not found.")
        return TransactionRead.model_validate(txn)

    async def get_list(
        self, user_id: str, filters: TransactionFilter
    ) -> PaginatedResponse[TransactionRead]:
        """Return a paginated, filtered, sorted list of transactions."""
        records, total = await self._repo.get_filtered(user_id, filters)
        total_pages = math.ceil(total / filters.page_size) if total else 1

        return PaginatedResponse(
            data=[TransactionRead.model_validate(r) for r in records],
            meta=PaginationMeta(
                total=total,
                page=filters.page,
                page_size=filters.page_size,
                total_pages=total_pages,
            ),
        )

    # ── Update ─────────────────────────────────────────────────────────────

    async def update(
        self, user_id: str, transaction_id: str, payload: TransactionUpdate
    ) -> TransactionRead:
        """
        Update a transaction.

        Raises
        ------
        NotFoundError
            If the record doesn't exist or belongs to another user.
        """
        txn = await self._repo.get_by_user_and_id(user_id, transaction_id)
        if not txn:
            raise NotFoundError(f"Transaction '{transaction_id}' not found.")

        updates = payload.model_dump(exclude_none=True)
        updated = await self._repo.update(txn, updates)
        return TransactionRead.model_validate(updated)

    # ── Delete ─────────────────────────────────────────────────────────────

    async def delete(self, user_id: str, transaction_id: str) -> None:
        """
        Delete a transaction.

        Raises
        ------
        NotFoundError
            If the record doesn't exist or belongs to another user.
        """
        txn = await self._repo.get_by_user_and_id(user_id, transaction_id)
        if not txn:
            raise NotFoundError(f"Transaction '{transaction_id}' not found.")
        await self._repo.delete(txn)
