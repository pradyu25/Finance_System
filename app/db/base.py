"""
SQLAlchemy Declarative Base + shared mixins
===========================================
All ORM models import ``Base`` from here so that Alembic and the
``create_all`` call in ``main.py`` discover every table automatically.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide declarative base."""
    pass


class TimestampMixin:
    """
    Adds ``created_at`` and ``updated_at`` columns to any model that
    inherits from it.  Both are stored in UTC.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
