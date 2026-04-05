"""
Common response schemas
========================
These generic wrappers enforce a consistent JSON envelope across every
endpoint so consumers always receive ``status`` + ``data`` or ``message``.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope."""
    status: str = "success"
    data: T


class ErrorResponse(BaseModel):
    """Standard error envelope (matches the global exception handler)."""
    status: str = "error"
    message: str
    code: int


class PaginationMeta(BaseModel):
    """Pagination metadata attached to list responses."""
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Success response for paginated collections."""
    status: str = "success"
    data: list[T]
    meta: PaginationMeta
