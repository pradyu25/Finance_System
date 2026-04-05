"""
Analytics service
==================
Orchestrates the analytics engine and insights generator, providing a
single interface for all analytics endpoints.
"""

from app.analytics import engine, insights
from app.models.transaction import TransactionType
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.analytics import (
    CategoryBreakdown,
    InsightsResponse,
    MonthlyEntry,
    SummaryResponse,
)


class AnalyticsService:
    """Coordinates analytics computation for a given user."""

    def __init__(self, repo: TransactionRepository):
        self._repo = repo

    async def get_summary(self, user_id: str) -> SummaryResponse:
        """Build and return the top-level financial summary."""
        transactions = await self._repo.get_all_for_user(user_id)
        return engine.build_summary(transactions)

    async def get_monthly(self, user_id: str) -> list[MonthlyEntry]:
        """Return month-by-month income / expense / balance."""
        transactions = await self._repo.get_all_for_user(user_id)
        return engine.compute_monthly_summary(transactions)

    async def get_category_breakdown(
        self, user_id: str, transaction_type: TransactionType
    ) -> list[CategoryBreakdown]:
        """Return category-wise breakdown for the specified transaction type."""
        transactions = await self._repo.get_all_for_user(user_id)
        return engine.compute_category_breakdown(transactions, transaction_type)

    async def get_insights(self, user_id: str) -> InsightsResponse:
        """Generate intelligent financial insights for the user."""
        transactions = await self._repo.get_all_for_user(user_id)

        totals = engine.compute_totals(transactions)
        monthly = engine.compute_monthly_summary(transactions)
        savings_rate = engine.compute_savings_rate(
            totals["total_income"], totals["total_expense"]
        )
        expense_breakdown = engine.compute_category_breakdown(
            transactions, TransactionType.expense
        )
        top_expense_cat = engine.top_category(expense_breakdown)

        return insights.generate_insights(
            transactions=transactions,
            monthly=monthly,
            total_income=totals["total_income"],
            total_expense=totals["total_expense"],
            savings_rate=savings_rate,
            top_expense_category=top_expense_cat,
        )
