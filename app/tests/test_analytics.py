"""
Unit tests for the analytics engine
=====================================
Pure function tests — no database required.

We use ``types.SimpleNamespace`` instead of ORM objects to avoid the
SQLAlchemy instrumentation issues that arise when constructing models
outside of a session.  The analytics engine only reads duck-typed
attributes, so this works perfectly.
"""

from types import SimpleNamespace

import pytest

from app.analytics.engine import (
    build_summary,
    compute_category_breakdown,
    compute_monthly_summary,
    compute_savings_rate,
    compute_spending_trend,
    compute_totals,
)
from app.models.transaction import TransactionType


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _txn(amount: float, ttype: str, category: str, date: str) -> SimpleNamespace:
    """Return a lightweight fake transaction that satisfies the engine's interface."""
    return SimpleNamespace(
        id="fake-id",
        user_id="fake-user",
        amount=amount,
        type=TransactionType(ttype),
        category=category,
        date=date,
        description=None,
    )


SAMPLE = [
    _txn(5000, "income", "Salary", "2024-01-05"),
    _txn(1200, "expense", "Rent", "2024-01-10"),
    _txn(300, "expense", "Food", "2024-01-15"),
    _txn(5500, "income", "Salary", "2024-02-05"),
    _txn(1500, "expense", "Rent", "2024-02-10"),
    _txn(600, "expense", "Food", "2024-02-18"),
    _txn(200, "expense", "Entertainment", "2024-02-22"),
]


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_compute_totals():
    totals = compute_totals(SAMPLE)
    assert totals["total_income"] == 10500.0
    assert totals["total_expense"] == 3800.0
    assert totals["current_balance"] == 6700.0


def test_savings_rate_normal():
    rate = compute_savings_rate(10000, 4000)
    assert rate == 60.0


def test_savings_rate_zero_income():
    """Zero income → savings rate is 0, not a division error."""
    rate = compute_savings_rate(0, 500)
    assert rate == 0.0


def test_savings_rate_expense_exceeds_income():
    """Rate is clamped to 0 when expenses exceed income."""
    rate = compute_savings_rate(1000, 1500)
    assert rate == 0.0


def test_category_breakdown_expense():
    breakdown = compute_category_breakdown(SAMPLE, TransactionType.expense)
    categories = [b.category for b in breakdown]
    # Rent is the highest single-month expense
    assert "Rent" in categories
    assert "Food" in categories
    # Percentages sum to 100
    total_pct = sum(b.percentage for b in breakdown)
    assert abs(total_pct - 100.0) < 0.1


def test_monthly_summary_count():
    monthly = compute_monthly_summary(SAMPLE)
    assert len(monthly) == 2  # January and February
    jan = monthly[0]
    assert jan.year == 2024
    assert jan.month == 1
    assert jan.income == 5000.0
    assert jan.expense == 1500.0


def test_spending_trend_increased():
    monthly = compute_monthly_summary(SAMPLE)
    # Feb expense (2300) > Jan expense (1500) → increased
    trend = compute_spending_trend(monthly)
    assert trend["trend"] == "increased"
    assert trend["change_pct"] > 0


def test_spending_trend_stable_with_one_month():
    single_month = [t for t in SAMPLE if t.date.startswith("2024-01")]
    monthly = compute_monthly_summary(single_month)
    trend = compute_spending_trend(monthly)
    assert trend["trend"] == "stable"


def test_build_summary_empty():
    summary = build_summary([])
    assert summary.total_income == 0.0
    assert summary.total_expense == 0.0
    assert summary.current_balance == 0.0
    assert summary.savings_rate == 0.0
    assert summary.transaction_count == 0
