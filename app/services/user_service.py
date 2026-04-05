"""
User management service
========================
Admin-only operations for listing and managing user accounts.
"""

from app.core.exceptions import NotFoundError
from app.models.user import UserRole
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserRead, UserRoleUpdate


class UserService:
    """Business logic for user account management (admin use)."""

    def __init__(self, repo: UserRepository):
        self._repo = repo

    async def list_users(self) -> list[UserRead]:
        """Return all registered users (admin only)."""
        users = await self._repo.get_all()
        return [UserRead.model_validate(u) for u in users]

    async def update_role(self, user_id: str, payload: UserRoleUpdate) -> UserRead:
        """
        Change a user's role.

        Raises
        ------
        NotFoundError
            If no user with *user_id* exists.
        """
        user = await self._repo.get(user_id)
        if not user:
            raise NotFoundError(f"User '{user_id}' not found.")
        updated = await self._repo.update(user, {"role": payload.role})
        return UserRead.model_validate(updated)

    async def delete_user(self, user_id: str) -> None:
        """
        Permanently remove a user and all their transactions (cascade).

        Raises
        ------
        NotFoundError
            If no user with *user_id* exists.
        """
        user = await self._repo.get(user_id)
        if not user:
            raise NotFoundError(f"User '{user_id}' not found.")
        await self._repo.delete(user)
