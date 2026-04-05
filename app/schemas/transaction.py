"""
Transaction Pydantic schemas
=============================
Strict validation ensures business rules (amount > 0, valid type) are
enforced at the API boundary before any service-layer code runs.
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.transaction import TransactionType


# ── Inbound ───────────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    """Payload for creating a new transaction."""

    amount: float = Field(..., gt=0, description="Must be a positive number")
    type: TransactionType
    category: str = Field(..., min_length=1, max_length=100)
    date: str = Field(..., description="ISO date string: YYYY-MM-DD")
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Ensure the date is a valid ISO date string."""
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")
        return v


class TransactionUpdate(BaseModel):
    """Partial update — all fields are optional."""

    amount: Optional[float] = Field(None, gt=0)
    type: Optional[TransactionType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    date: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("date must be in YYYY-MM-DD format")
        return v


# ── Query parameters (filter + paging + sort) ─────────────────────────────────

class TransactionFilter(BaseModel):
    """
    All available query parameters for the transaction list endpoint.
    All fields are optional — omitting a field means "no filter on that field".
    """

    type: Optional[TransactionType] = None
    category: Optional[str] = None
    start_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="YYYY-MM-DD")

    # Pagination
    page: int = Field(1, ge=1, description="1-based page index")
    page_size: int = Field(20, ge=1, le=100, description="Records per page")

    # Sorting
    sort_by: Literal["date", "amount"] = "date"
    sort_order: Literal["asc", "desc"] = "desc"


# ── Outbound ──────────────────────────────────────────────────────────────────

class TransactionRead(BaseModel):
    """Safe read representation of a transaction."""

    id: str
    user_id: str
    amount: float
    type: TransactionType
    category: str
    date: str
    description: Optional[str]

    model_config = {"from_attributes": True}
