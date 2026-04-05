"""
Export service
==============
Generates CSV and JSON exports of transaction data.
Uses only the Python standard library — no extra dependencies.
"""

import csv
import io
import json
from typing import Literal

from app.repositories.transaction_repo import TransactionRepository
from app.schemas.transaction import TransactionFilter


class ExportService:
    """Handles CSV and JSON export of user transactions."""

    def __init__(self, repo: TransactionRepository):
        self._repo = repo

    async def export(
        self,
        user_id: str,
        filters: TransactionFilter,
        fmt: Literal["csv", "json"] = "csv",
    ) -> tuple[str, str]:
        """
        Export matching transactions in the requested format.

        Returns
        -------
        (content, media_type)
            The serialised string and its MIME type.
        """
        # Always export all matching rows (no pagination)
        export_filter = filters.model_copy(update={"page": 1, "page_size": 10_000})
        records, _ = await self._repo.get_filtered(user_id, export_filter)

        if fmt == "json":
            data = [
                {
                    "id": r.id,
                    "amount": float(r.amount),
                    "type": r.type.value,
                    "category": r.category,
                    "date": r.date,
                    "description": r.description,
                }
                for r in records
            ]
            return json.dumps(data, indent=2), "application/json"

        # Default: CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "amount", "type", "category", "date", "description"],
        )
        writer.writeheader()
        for r in records:
            writer.writerow(
                {
                    "id": r.id,
                    "amount": float(r.amount),
                    "type": r.type.value,
                    "category": r.category,
                    "date": r.date,
                    "description": r.description or "",
                }
            )
        return output.getvalue(), "text/csv"
