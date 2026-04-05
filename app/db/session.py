"""
Async database session
========================
Creates an async SQLAlchemy engine and session factory from the
DATABASE_URL in settings.  The ``get_db`` dependency is injected into
every route that needs a database session.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,     # Log every SQL statement in debug mode
    future=True,
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects usable after commit
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields one ``AsyncSession`` per request and
    guarantees it is closed afterwards.
    """
    async with AsyncSessionLocal() as session:
        yield session
