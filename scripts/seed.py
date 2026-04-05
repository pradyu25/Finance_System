"""
Database seed script
======================
Creates system users (admin, analyst, viewer) and a year's worth of
realistic financial transactions to demonstrate all analytics features.

Usage::

    python scripts/seed.py
"""

import asyncio
import random
import sys
import os

# Allow running from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.models.transaction import Transaction, TransactionType
from app.models.user import User, UserRole

# ── Seed data configuration ───────────────────────────────────────────────────

USERS = [
    {"email": settings.FIRST_ADMIN_EMAIL, "password": settings.FIRST_ADMIN_PASSWORD,
     "full_name": settings.FIRST_ADMIN_NAME, "role": UserRole.admin},
    {"email": "analyst@finance.io", "password": "Analyst@1234",
     "full_name": "Finance Analyst", "role": UserRole.analyst},
    {"email": "viewer@finance.io", "password": "Viewer@1234",
     "full_name": "Read-Only Viewer", "role": UserRole.viewer},
]

INCOME_CATEGORIES = ["Salary", "Freelance", "Investments", "Rental Income", "Bonus"]
EXPENSE_CATEGORIES = [
    "Rent", "Food & Groceries", "Utilities", "Transport", "Entertainment",
    "Healthcare", "Shopping", "Education", "Insurance", "Travel",
]


def _random_transactions(user_id: str) -> list[Transaction]:
    """Generate ~12 months of realistic transactions for a user."""
    transactions = []

    for month in range(1, 13):
        # Monthly salary
        transactions.append(Transaction(
            user_id=user_id,
            amount=round(random.uniform(45000, 65000), 2),
            type=TransactionType.income,
            category="Salary",
            date=f"2024-{month:02d}-01",
            description="Monthly salary credit",
        ))

        # Optional side income
        if random.random() > 0.5:
            transactions.append(Transaction(
                user_id=user_id,
                amount=round(random.uniform(2000, 15000), 2),
                type=TransactionType.income,
                category=random.choice(["Freelance", "Investments", "Bonus"]),
                date=f"2024-{month:02d}-{random.randint(5, 28):02d}",
                description="Additional income",
            ))

        # Fixed monthly expenses
        transactions.append(Transaction(
            user_id=user_id,
            amount=round(random.uniform(12000, 18000), 2),
            type=TransactionType.expense,
            category="Rent",
            date=f"2024-{month:02d}-02",
            description="Monthly rent",
        ))

        # Variable expenses (4-8 per month)
        for _ in range(random.randint(4, 8)):
            transactions.append(Transaction(
                user_id=user_id,
                amount=round(random.uniform(200, 5000), 2),
                type=TransactionType.expense,
                category=random.choice(EXPENSE_CATEGORIES[1:]),
                date=f"2024-{month:02d}-{random.randint(1, 28):02d}",
                description=None,
            ))

    return transactions


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        for user_data in USERS:
            # Skip if user already exists
            from sqlalchemy import select
            existing = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            if existing.scalars().first():
                print(f"  ℹ️  User {user_data['email']} already exists — skipping.")
                continue

            user = User(
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
            )
            db.add(user)
            await db.flush()  # Get the user.id before creating transactions

            txns = _random_transactions(user.id)
            db.add_all(txns)
            print(f"  ✅  Created {user_data['role'].value} user: {user_data['email']} "
                  f"with {len(txns)} transactions.")

        await db.commit()

    await engine.dispose()
    print("\n🌱  Seed complete! Login credentials:")
    for u in USERS:
        print(f"   {u['role'].value:8s}  →  {u['email']}  /  {u['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
