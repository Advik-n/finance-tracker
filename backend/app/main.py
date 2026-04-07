"""
AI Personal Finance Tracker - Main Application Entry Point

This module initializes the FastAPI application with all middleware,
routers, and event handlers configured for production use.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import AppException
from app.database import check_db_connection, close_db, engine, init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Handles:
    - Database connection pool initialization
    - Table creation (dev mode only)
    - Cleanup on shutdown
    """
    # Startup
    logger.info("Starting up Finance Tracker API...")
    logger.info(f"Environment: {settings.environment}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Finance Tracker API...")
    await close_db()
    logger.info("Cleanup completed")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
    ## AI-Powered Personal Finance Tracker API

    A comprehensive backend for tracking personal finances with AI-powered insights.

    ### Features
    - **Transaction Management**: CRUD operations for financial transactions
    - **File Upload**: Parse bank statements (PDF, CSV, Excel)
    - **Analytics**: Spending summaries, trends, and breakdowns
    - **AI Insights**: Smart recommendations and pattern detection
    - **Budgeting**: Set and track spending limits

    ### Authentication
    All endpoints (except auth) require JWT Bearer token authentication.
    """,
    version="1.0.0",
    openapi_url="/api/v1/openapi.json" if settings.debug else None,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)


# ====================
# Middleware Configuration
# ====================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# ====================
# Exception Handlers
# ====================


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application-specific exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "detail": exc.detail,
            "errors": exc.errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    if settings.debug:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
            },
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


# ====================
# Include API Routers
# ====================

# Import routers here to avoid circular imports
from app.api.v1 import analytics, auth, transactions, upload

app.include_router(auth.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


# ====================
# Health & Info Endpoints
# ====================


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for container orchestration and monitoring.

    Returns database connection status and service information.
    """
    db_healthy = await check_db_connection()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "version": "1.0.0",
        "service": "finance-tracker-api",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information and links.
    """
    return {
        "message": "Welcome to AI Personal Finance Tracker API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Disabled in production",
        "redoc": "/redoc" if settings.debug else "Disabled in production",
        "health": "/health",
        "api_base": "/api/v1",
    }


@app.get("/api/v1", tags=["API Info"])
async def api_info():
    """
    API version information and available endpoints.
    """
    return {
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "transactions": "/api/v1/transactions",
            "upload": "/api/v1/upload",
            "analytics": "/api/v1/analytics",
        },
        "documentation": "/docs" if settings.debug else None,
    }
