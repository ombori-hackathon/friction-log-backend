"""
Main FastAPI application for Friction Log backend.

This module initializes the FastAPI app, configures CORS, and defines
the health check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db

# Create FastAPI app
app = FastAPI(
    title="Friction Log API",
    version="1.0.0",
    description=(
        "REST API for tracking daily life friction items and "
        "measuring progress in eliminating them."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for macOS app
# Allow requests from localhost during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server (if ever used)
        "http://127.0.0.1:3000",
        "*",  # Allow all for local development
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    init_db()


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Status indicating the server is healthy

    Example:
        >>> GET /health
        {"status": "ok"}
    """
    return {"status": "ok"}


# Root endpoint
@app.get("/", tags=["health"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API name, version, and documentation link
    """
    return {
        "name": "Friction Log API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
