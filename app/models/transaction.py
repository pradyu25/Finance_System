"""
Transaction ORM model
=====================
Maps to the ``transactions`` table.  Each record represents a single
financial event (income or expense) owned by a user.
"""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SaEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class TransactionType(str, PyEnum):
    """The two fundamental types of financial movement."""
    income = "income"
    expense = "expense"


class Transaction(Base, TimestampMixin):
    """A single financial record (income or expense entry)."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[TransactionType] = mapped_column(SaEnum(TransactionType), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # ISO format YYYY-MM-DD
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship back to the owning user
    owner: Mapped["User"] = relationship("User", back_populates="transactions")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id!r} type={self.type} "
            f"amount={self.amount} date={self.date!r}>"
        )
