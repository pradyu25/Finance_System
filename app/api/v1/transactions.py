"""
Transaction routes
==================
Full CRUD + advanced filtering, pagination, sorting, and export.
"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, require_viewer
from app.db.session import get_db
from app.models.transaction import TransactionType
from app.models.user import User
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilter,
    TransactionRead,
    TransactionUpdate,
)
from app.services.export_service import ExportService
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ── Dependency helpers ────────────────────────────────────────────────────────

def _svc(db: AsyncSession = Depends(get_db)) -> TransactionService:
    return TransactionService(TransactionRepository(db))


def _export_svc(db: AsyncSession = Depends(get_db)) -> ExportService:
    return ExportService(TransactionRepository(db))


def _build_filter(
    type: Optional[TransactionType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
    sort_by: Literal["date", "amount"] = Query("date", description="Sort field"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
) -> TransactionFilter:
    return TransactionFilter(
        type=type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[TransactionRead],
    summary="List transactions with optional filters",
)
async def list_transactions(
    filters: TransactionFilter = Depends(_build_filter),
    current_user: User = Depends(require_viewer),
    svc: TransactionService = Depends(_svc),
):
    """
    Returns a paginated list of transactions.

    **Filters** (all optional):
    - `type` — `income` or `expense`
    - `category` — partial match
    - `start_date` / `end_date` — date range (YYYY-MM-DD)
    - `sort_by` — `date` or `amount`
    - `sort_order` — `asc` or `desc`
    - `page` / `page_size` — pagination
    """
    return await svc.get_list(current_user.id, filters)


@router.post(
    "",
    response_model=SuccessResponse[TransactionRead],
    status_code=201,
    summary="Create a new transaction",
)
async def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(require_admin),
    svc: TransactionService = Depends(_svc),
):
    """Create a new income or expense record. **Admin only.**"""
    txn = await svc.create(current_user.id, payload)
    return SuccessResponse(data=txn)


@router.get(
    "/export",
    summary="Export transactions as CSV or JSON",
)
async def export_transactions(
    fmt: Literal["csv", "json"] = Query("csv", description="Export format"),
    filters: TransactionFilter = Depends(_build_filter),
    current_user: User = Depends(require_viewer),
    export_svc: ExportService = Depends(_export_svc),
):
    """
    Download a full export of matching transactions.
    Pagination is ignored — all matching records are included.
    """
    content, media_type = await export_svc.export(current_user.id, filters, fmt)
    filename = f"transactions.{fmt}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{transaction_id}",
    response_model=SuccessResponse[TransactionRead],
    summary="Retrieve a single transaction",
)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(require_viewer),
    svc: TransactionService = Depends(_svc),
):
    """Fetch details for a specific transaction by its ID."""
    txn = await svc.get_one(current_user.id, transaction_id)
    return SuccessResponse(data=txn)


@router.put(
    "/{transaction_id}",
    response_model=SuccessResponse[TransactionRead],
    summary="Update a transaction",
)
async def update_transaction(
    transaction_id: str,
    payload: TransactionUpdate,
    current_user: User = Depends(require_admin),
    svc: TransactionService = Depends(_svc),
):
    """Partially update a transaction. **Admin only.**"""
    txn = await svc.update(current_user.id, transaction_id, payload)
    return SuccessResponse(data=txn)


@router.delete(
    "/{transaction_id}",
    status_code=204,
    summary="Delete a transaction",
)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(require_admin),
    svc: TransactionService = Depends(_svc),
):
    """Permanently delete a transaction. **Admin only.**"""
    await svc.delete(current_user.id, transaction_id)
