"""
Auth routes
============
Public endpoints for user registration and JWT login.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.common import SuccessResponse
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _svc(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post(
    "/signup",
    response_model=SuccessResponse[UserRead],
    status_code=201,
    summary="Register a new user account",
)
async def signup(
    payload: UserCreate,
    svc: AuthService = Depends(_svc),
):
    """
    Create a new user with the **viewer** role by default.
    The email address must be unique.
    """
    user = await svc.register(payload)
    return SuccessResponse(data=user)


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    summary="Obtain a JWT access token",
)
async def login(
    payload: UserLogin,
    svc: AuthService = Depends(_svc),
):
    """
    Authenticate with email and password to receive a Bearer token.
    Include the token in the ``Authorization: Bearer <token>`` header for
    all subsequent requests.
    """
    token_data = await svc.login(payload)
    return SuccessResponse(data=token_data)


# ── OAuth2 token endpoint (for Swagger "Authorize" button) ────────────────────
from fastapi.security import OAuth2PasswordRequestForm  # noqa: E402


@router.post(
    "/login/token",
    response_model=TokenResponse,
    include_in_schema=False,  # Hidden — only used by swagger's auth dialog
)
async def login_token(
    form: OAuth2PasswordRequestForm = Depends(),
    svc: AuthService = Depends(_svc),
):
    """OAuth2 compatible login for Swagger UI."""
    from app.schemas.user import UserLogin as _UL  # noqa: PLC0415

    token_data = await svc.login(_UL(email=form.username, password=form.password))
    return token_data
