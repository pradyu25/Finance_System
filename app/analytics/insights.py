"""
Intelligent insights generator
================================
Takes pre-computed analytics structures and translates them into
human-readable insight strings and actionable alerts — the "smart" layer
of the finance system.
"""

from typing import Optional

from app.analytics.engine import compute_spending_trend
from app.schemas.analytics import InsightsResponse, MonthlyEntry
from app.models.transaction import Transaction, TransactionType


def generate_insights(
    transactions: list[Transaction],
    monthly: list[MonthlyEntry],
    total_income: float,
    total_expense: float,
    savings_rate: float,
    top_expense_category: Optional[str],
) -> InsightsResponse:
    """
    Generate a rich set of human-readable insights from analytics data.

    Parameters
    ----------
    transactions   : All user transactions used to build a big picture.
    monthly        : Pre-computed monthly breakdown list.
    total_income   : Aggregate income across all time.
    total_expense  : Aggregate expense across all time.
    savings_rate   : Pre-computed savings rate percentage.
    top_expense_category : Name of the top expense category.

    Returns
    -------
    InsightsResponse containing trend, insights list, and alerts list.
    """

    insight_messages: list[str] = []
    alert_messages: list[str] = []

    # ── Spending trend ─────────────────────────────────────────────────────
    trend_data = compute_spending_trend(monthly)
    trend: str = trend_data["trend"]
    change_pct: float = trend_data["change_pct"]

    if len(monthly) >= 2:
        current_month_name = monthly[-1].month_name
        prev_month_name = monthly[-2].month_name

        if trend == "increased":
            insight_messages.append(
                f"⚠️  Spending increased by {abs(change_pct):.1f}% in {current_month_name} "
                f"compared to {prev_month_name}."
            )
        elif trend == "decreased":
            insight_messages.append(
                f"✅  Spending decreased by {abs(change_pct):.1f}% in {current_month_name} "
                f"compared to {prev_month_name} — great job!"
            )
        else:
            insight_messages.append(
                f"📊  Spending remained stable between {prev_month_name} and {current_month_name}."
            )

    # ── Expense vs income this month ───────────────────────────────────────
    if monthly:
        latest = monthly[-1]
        if latest.expense > latest.income and latest.income > 0:
            overspend_pct = round((latest.expense - latest.income) / latest.income * 100, 1)
            alert_messages.append(
                f"🚨  Expenses exceeded income in {latest.month_name} "
                f"(overspent by {overspend_pct}%)."
            )
        elif latest.income > 0 and latest.expense == 0:
            insight_messages.append(
                f"💰  No expenses recorded in {latest.month_name} — "
                "perfect savings month!"
            )

    # ── Savings rate insights ──────────────────────────────────────────────
    if savings_rate >= 30:
        insight_messages.append(
            f"🌟  Excellent savings rate of {savings_rate:.1f}%! "
            "You are on track for strong financial health."
        )
    elif savings_rate >= 10:
        insight_messages.append(
            f"👍  Savings rate is {savings_rate:.1f}%. "
            "Aim for 20%+ for a healthy financial cushion."
        )
    elif savings_rate > 0:
        insight_messages.append(
            f"📉  Savings rate is only {savings_rate:.1f}%. "
            "Consider reducing discretionary expenses."
        )
    elif savings_rate <= 0 and total_income > 0:
        alert_messages.append(
            "🚨  Savings rate is 0% or negative — total expenses meet or exceed total income."
        )

    # ── Top spending category ──────────────────────────────────────────────
    if top_expense_category:
        insight_messages.append(
            f"🏷️  Your top expense category is '{top_expense_category}'. "
            "Review if this aligns with your financial goals."
        )

    # ── Data sparsity notice ───────────────────────────────────────────────
    if not transactions:
        insight_messages.append(
            "ℹ️  No transactions recorded yet. "
            "Add your income and expenses to start seeing insights."
        )
    elif len(transactions) < 5:
        insight_messages.append(
            "ℹ️  Only a few transactions recorded. "
            "Insights will become more accurate as you add more data."
        )

    # ── Best month ────────────────────────────────────────────────────────
    if len(monthly) >= 3:
        best = max(monthly, key=lambda m: m.balance)
        insight_messages.append(
            f"📅  Your best financial month so far was {best.month_name} {best.year} "
            f"with a balance of ₹{best.balance:,.2f}."
        )

    return InsightsResponse(
        spending_trend=trend,
        spending_change_pct=change_pct,
        top_spending_category=top_expense_category,
        savings_rate=savings_rate,
        insights=insight_messages,
        alerts=alert_messages,
    )
