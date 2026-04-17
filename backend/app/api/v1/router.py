"""
API V1 Router Configuration

Aggregates all v1 API endpoints into a single router
for clean inclusion in the main application.
"""

from fastapi import APIRouter

from app.api.v1 import analytics, auth, transactions, upload, users

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Transaction CRUD endpoints
api_router.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["Transactions"]
)

# File upload endpoints
api_router.include_router(
    upload.router,
    prefix="/upload",
    tags=["Upload"]
)

# Analytics and insights endpoints
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)

# User profile endpoints
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)
