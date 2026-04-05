"""
Analytics routes
=================
Expose financial summaries, monthly breakdowns, category analysis,
and intelligent insights via dedicated endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_analyst, require_viewer
from app.db.session import get_db
from app.models.transaction import TransactionType
from app.models.user import User
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.analytics import (
    CategoryBreakdown,
    InsightsResponse,
    MonthlyEntry,
    SummaryResponse,
)
from app.schemas.common import SuccessResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _svc(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(TransactionRepository(db))


@router.get(
    "/summary",
    response_model=SuccessResponse[SummaryResponse],
    summary="Overall financial summary",
)
async def get_summary(
    current_user: User = Depends(require_viewer),
    svc: AnalyticsService = Depends(_svc),
):
    """
    Returns total income, total expense, current balance, savings rate,
    and top categories across all time.
    """
    summary = await svc.get_summary(current_user.id)
    return SuccessResponse(data=summary)


@router.get(
    "/monthly",
    response_model=SuccessResponse[list[MonthlyEntry]],
    summary="Month-by-month income and expense breakdown",
)
async def get_monthly(
    current_user: User = Depends(require_analyst),
    svc: AnalyticsService = Depends(_svc),
):
    """
    Aggregated income, expense, balance, and savings rate for each
    calendar month in which the user has recorded transactions.
    """
    monthly = await svc.get_monthly(current_user.id)
    return SuccessResponse(data=monthly)


@router.get(
    "/category",
    response_model=SuccessResponse[list[CategoryBreakdown]],
    summary="Category-wise breakdown",
)
async def get_category_breakdown(
    type: TransactionType = Query(
        TransactionType.expense,
        description="Transaction type to analyse (income or expense)",
    ),
    current_user: User = Depends(require_analyst),
    svc: AnalyticsService = Depends(_svc),
):
    """
    Returns categories ranked by total amount for the given transaction
    type, including percentage share and transaction count per category.
    """
    breakdown = await svc.get_category_breakdown(current_user.id, type)
    return SuccessResponse(data=breakdown)


@router.get(
    "/insights",
    response_model=SuccessResponse[InsightsResponse],
    summary="Intelligent spending insights and alerts",
)
async def get_insights(
    current_user: User = Depends(require_analyst),
    svc: AnalyticsService = Depends(_svc),
):
    """
    Generates human-readable financial insights such as:
    - Spending trend vs. last month
    - Savings rate assessment
    - Alerts when expenses exceed income
    - Best financial month
    """
    result = await svc.get_insights(current_user.id)
    return SuccessResponse(data=result)
