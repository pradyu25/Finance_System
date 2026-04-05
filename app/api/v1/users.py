"""
User management routes
=======================
Admin-only endpoints to list, update roles, and delete users.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.common import SuccessResponse
from app.schemas.user import UserRead, UserRoleUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["User Management"])


def _svc(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get(
    "",
    response_model=SuccessResponse[list[UserRead]],
    summary="List all users (admin only)",
)
async def list_users(
    current_user: User = Depends(require_admin),
    svc: UserService = Depends(_svc),
):
    """Return a list of all registered users. **Admin only.**"""
    users = await svc.list_users()
    return SuccessResponse(data=users)


@router.put(
    "/{user_id}/role",
    response_model=SuccessResponse[UserRead],
    summary="Change a user's role (admin only)",
)
async def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    current_user: User = Depends(require_admin),
    svc: UserService = Depends(_svc),
):
    """Update the role of any user. **Admin only.**"""
    updated = await svc.update_role(user_id, payload)
    return SuccessResponse(data=updated)


@router.delete(
    "/{user_id}",
    status_code=204,
    summary="Delete a user (admin only)",
)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    svc: UserService = Depends(_svc),
):
    """Permanently delete a user and all their transactions. **Admin only.**"""
    await svc.delete_user(user_id)
