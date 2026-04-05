"""
Auth service
=============
Handles registration and login business logic, keeping the API layer
thin and the security details out of the route handlers.
"""

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserRead


class AuthService:
    """Business logic for user authentication."""

    def __init__(self, user_repo: UserRepository):
        self._repo = user_repo

    async def register(self, payload: UserCreate) -> UserRead:
        """
        Register a new user with the *viewer* role by default.

        Raises
        ------
        ConflictError
            If the email is already in use.
        """
        if await self._repo.email_exists(payload.email):
            raise ConflictError(f"Email '{payload.email}' is already registered.")

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=UserRole.viewer,
        )
        created = await self._repo.create(user)
        return UserRead.model_validate(created)

    async def login(self, payload: UserLogin) -> TokenResponse:
        """
        Authenticate credentials and return a JWT access token.

        Raises
        ------
        UnauthorizedError
            If the email is unknown or the password is wrong.
        """
        user = await self._repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise UnauthorizedError("Account is disabled.")

        token = create_access_token(subject=user.id, role=user.role.value)
        return TokenResponse(access_token=token, user=UserRead.model_validate(user))
