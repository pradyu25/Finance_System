"""
Analytics Pydantic schemas
===========================
These response models define exactly what each analytics endpoint returns,
making the contract explicit and self-documenting in Swagger.
"""

from typing import Optional

from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    """Income or expense total for a single category."""
    category: str
    total: float
    percentage: float          # % of total income or total expense
    transaction_count: int


class MonthlyEntry(BaseModel):
    """Aggregated figures for a single calendar month."""
    year: int
    month: int
    month_name: str
    income: float
    expense: float
    balance: float
    savings_rate: float        # (income - expense) / income × 100


class SummaryResponse(BaseModel):
    """Top-level financial summary returned by /analytics/summary."""
    total_income: float
    total_expense: float
    current_balance: float
    savings_rate: float        # percentage
    transaction_count: int
    top_expense_category: Optional[str]
    top_income_category: Optional[str]
    recent_transactions_count: int  # Transactions in last 30 days


class InsightsResponse(BaseModel):
    """Intelligent text insights returned by /analytics/insights."""
    spending_trend: str              # "increased" | "decreased" | "stable"
    spending_change_pct: float       # e.g. 12.5 or -8.3
    top_spending_category: Optional[str]
    savings_rate: float
    insights: list[str]             # Human-readable insight strings
    alerts: list[str]               # Warnings (e.g. expenses exceed income)
