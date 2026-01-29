"""
Main FastAPI application entry point for Solana Meme Coin Trend Dashboard.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db, close_db
from .api import trends, acceleration, history
from .tasks.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    print(f"Starting {settings.app_name}...")
    await init_db()
    print("Database initialized successfully.")

    # Start background scheduler
    scheduler = await start_scheduler()
    app.state.scheduler = scheduler
    print("Background scheduler started.")

    yield

    # Shutdown
    print("Shutting down...")
    await stop_scheduler(app.state.scheduler)
    print("Scheduler stopped.")
    await close_db()
    print("Database connections closed.")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Backend API for tracking Solana meme coin trends and detecting breakout metas",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS - allows both common dev server ports (3000 and 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint returning API status."""
    return {
        "status": "online",
        "app": settings.app_name,
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "moralis_configured": settings.has_moralis_key,
    }


# Include API routers
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(acceleration.router, prefix="/api/acceleration", tags=["acceleration"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
