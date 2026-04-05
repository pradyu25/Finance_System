"""
Analytics computation engine
==============================
Pure functions that derive financial metrics from a list of Transaction
ORM objects.  No database calls happen here — keeping this layer
stateless and fully unit-testable.
"""

import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Optional

from app.models.transaction import Transaction, TransactionType
from app.schemas.analytics import CategoryBreakdown, MonthlyEntry, SummaryResponse


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(d: str) -> date:
    return date.fromisoformat(d)


def _round2(v: float) -> float:
    return round(v, 2)


# ── Core aggregations ─────────────────────────────────────────────────────────

def compute_totals(transactions: list[Transaction]) -> dict:
    """
    Compute total income, total expense, and current balance.

    Returns
    -------
    dict with keys: total_income, total_expense, current_balance
    """
    income = sum(float(t.amount) for t in transactions if t.type == TransactionType.income)
    expense = sum(float(t.amount) for t in transactions if t.type == TransactionType.expense)
    return {
        "total_income": _round2(income),
        "total_expense": _round2(expense),
        "current_balance": _round2(income - expense),
    }


def compute_savings_rate(total_income: float, total_expense: float) -> float:
    """
    Savings rate = (income - expense) / income × 100.
    Returns 0 when income is zero to avoid division by zero.
    """
    if total_income == 0:
        return 0.0
    return _round2(max(0.0, (total_income - total_expense) / total_income * 100))


# ── Category breakdown ────────────────────────────────────────────────────────

def compute_category_breakdown(
    transactions: list[Transaction],
    transaction_type: TransactionType,
) -> list[CategoryBreakdown]:
    """
    Group transactions of *transaction_type* by category and compute
    totals, counts, and percentage share of the overall type total.
    """
    filtered = [t for t in transactions if t.type == transaction_type]
    total = sum(float(t.amount) for t in filtered)

    grouped: dict[str, list[Transaction]] = defaultdict(list)
    for t in filtered:
        grouped[t.category].append(t)

    breakdown = []
    for category, items in grouped.items():
        cat_total = sum(float(t.amount) for t in items)
        breakdown.append(
            CategoryBreakdown(
                category=category,
                total=_round2(cat_total),
                percentage=_round2(cat_total / total * 100) if total else 0.0,
                transaction_count=len(items),
            )
        )

    return sorted(breakdown, key=lambda x: x.total, reverse=True)


# ── Monthly summaries ─────────────────────────────────────────────────────────

def compute_monthly_summary(transactions: list[Transaction]) -> list[MonthlyEntry]:
    """
    Aggregate transactions into calendar months, sorted from oldest to newest.
    """
    monthly: dict[tuple[int, int], dict] = defaultdict(
        lambda: {"income": 0.0, "expense": 0.0}
    )

    for t in transactions:
        d = _parse_date(t.date)
        key = (d.year, d.month)
        if t.type == TransactionType.income:
            monthly[key]["income"] += float(t.amount)
        else:
            monthly[key]["expense"] += float(t.amount)

    entries: list[MonthlyEntry] = []
    for (year, month), vals in sorted(monthly.items()):
        income = _round2(vals["income"])
        expense = _round2(vals["expense"])
        balance = _round2(income - expense)
        savings_rate = compute_savings_rate(income, expense)
        entries.append(
            MonthlyEntry(
                year=year,
                month=month,
                month_name=calendar.month_name[month],
                income=income,
                expense=expense,
                balance=balance,
                savings_rate=savings_rate,
            )
        )

    return entries


# ── Spending trend ────────────────────────────────────────────────────────────

def compute_spending_trend(monthly: list[MonthlyEntry]) -> dict:
    """
    Compare the current month's expenses to the previous month's.

    Returns
    -------
    dict with keys: trend ("increased" | "decreased" | "stable"), change_pct
    """
    if len(monthly) < 2:
        return {"trend": "stable", "change_pct": 0.0}

    current = monthly[-1].expense
    previous = monthly[-2].expense

    if previous == 0:
        change_pct = 100.0 if current > 0 else 0.0
        trend = "increased" if current > 0 else "stable"
    else:
        change_pct = _round2((current - previous) / previous * 100)
        if abs(change_pct) < 1:
            trend = "stable"
        elif change_pct > 0:
            trend = "increased"
        else:
            trend = "decreased"

    return {"trend": trend, "change_pct": change_pct}


# ── Top categories ────────────────────────────────────────────────────────────

def top_category(breakdown: list[CategoryBreakdown]) -> Optional[str]:
    """Return the name of the category with the highest total, or None."""
    return breakdown[0].category if breakdown else None


# ── Recent transactions count ─────────────────────────────────────────────────

def count_recent(transactions: list[Transaction], days: int = 30) -> int:
    """Return how many transactions occurred within the last *days* days."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    return sum(1 for t in transactions if t.date >= cutoff)


# ── Composite summary ─────────────────────────────────────────────────────────

def build_summary(transactions: list[Transaction]) -> SummaryResponse:
    """
    Produce the full financial summary from a list of transactions.
    This is the primary entry-point used by the summary endpoint.
    """
    totals = compute_totals(transactions)
    income_breakdown = compute_category_breakdown(transactions, TransactionType.income)
    expense_breakdown = compute_category_breakdown(transactions, TransactionType.expense)

    return SummaryResponse(
        total_income=totals["total_income"],
        total_expense=totals["total_expense"],
        current_balance=totals["current_balance"],
        savings_rate=compute_savings_rate(totals["total_income"], totals["total_expense"]),
        transaction_count=len(transactions),
        top_expense_category=top_category(expense_breakdown),
        top_income_category=top_category(income_breakdown),
        recent_transactions_count=count_recent(transactions),
    )
