"""
API v1 master router
=====================
Aggregates all sub-routers into one router that is mounted by main.py.
"""

from fastapi import APIRouter

from app.api.v1 import analytics, auth, transactions, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(transactions.router)
api_router.include_router(analytics.router)
api_router.include_router(users.router)
