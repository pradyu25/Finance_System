"""
FastAPI dependencies
=====================
Shared dependencies for authentication and role-based access control.
Injected into route handlers via ``Depends()``.
"""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository

# Tells FastAPI where to look for the bearer token in the request
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the JWT, fetch the user from the DB, and return them.
    Raises ``UnauthorizedError`` for any invalid token.
    """
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Token subject missing.")
    except JWTError:
        raise UnauthorizedError("Invalid or expired token.")

    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise UnauthorizedError("User not found.")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled.")
    return user


# ── Role-specific dependency factories ───────────────────────────────────────

def require_role(*roles: UserRole):
    """
    Return a dependency that checks the current user has one of *roles*.

    Usage::

        @router.get("/admin-only")
        async def admin_only(user = Depends(require_role(UserRole.admin))):
            ...
    """
    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError(
                f"Required role: {', '.join(r.value for r in roles)}. "
                f"Your role: {user.role.value}."
            )
        return user

    return _check


# Convenience shortcuts
require_viewer = require_role(UserRole.viewer, UserRole.analyst, UserRole.admin)
require_analyst = require_role(UserRole.analyst, UserRole.admin)
require_admin = require_role(UserRole.admin)
