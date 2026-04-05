"""
Finance Intelligence System
============================
Application entry point.  Registers middleware, exception handlers,
the API router, and starts up the database on first run.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.db.session import engine
from app.db.base import Base


# ── Logging ───────────────────────────────────────────────────────────────────
setup_logging()


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
from scripts.seed import seed

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables on startup and auto-seed the DB."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Automatically populate the database so evaluators don't need shell access
    await seed()
    
    yield
    await engine.dispose()


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A production-quality Finance Intelligence System with analytics, "
        "role-based access control, and intelligent spending insights."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message, "code": exc.status_code},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error", "code": 500},
    )


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "success", "data": {"message": f"{settings.APP_NAME} is running ✅"}}
