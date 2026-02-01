"""
Main FastAPI application entry point for TrendRadar.Sol.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db, close_db
from .api import trends, acceleration, history, search
from .tasks.scheduler import start_scheduler, stop_scheduler, snapshot_job, aggregate_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    try:
        print(f"Starting {settings.app_name}...")
        await init_db()
        print("Database initialized successfully.")

        # Start background scheduler
        scheduler = await start_scheduler()
        app.state.scheduler = scheduler
        print("Background scheduler started.")
        print("Application startup complete - ready to accept requests!")
    except Exception as e:
        print(f"STARTUP ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise

    yield

    # Shutdown
    try:
        print("Shutting down...")
        if hasattr(app.state, 'scheduler'):
            await stop_scheduler(app.state.scheduler)
            print("Scheduler stopped.")
        await close_db()
        print("Database connections closed.")
    except Exception as e:
        print(f"SHUTDOWN ERROR: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Backend API for tracking Solana meme coin trends and detecting breakout metas",
    version="1.0.1",
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
        "version": "1.0.1",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "moralis_configured": settings.has_moralis_key,
    }


@app.post("/api/trigger-snapshot")
async def trigger_snapshot():
    """Manually trigger a snapshot and aggregation job."""
    try:
        await snapshot_job()
        await aggregate_job()
        return {"status": "success", "message": "Snapshot and aggregation completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/recategorize-tokens")
async def recategorize_tokens():
    """Recategorize all existing tokens using the latest categorizer."""
    from .database import async_session_maker
    from .models import Token
    from .services.categorizer import categorize_token
    from sqlalchemy.future import select

    try:
        async with async_session_maker() as session:
            result = await session.execute(select(Token))
            tokens = result.scalars().all()

            updated = 0
            for token in tokens:
                primary_cat, sub_cat, keywords = categorize_token(
                    token.name,
                    token.symbol
                )

                if primary_cat != token.primary_category or sub_cat != token.sub_category:
                    token.primary_category = primary_cat
                    token.sub_category = sub_cat
                    token.detected_keywords = ",".join(keywords) if keywords else None
                    updated += 1

            await session.commit()

            # Re-run aggregation to update trend stats
            await aggregate_job()

            return {
                "status": "success",
                "total_tokens": len(tokens),
                "updated": updated,
                "message": f"Recategorized {updated} tokens"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/debug/moralis-graduated")
async def debug_moralis_graduated():
    """Debug endpoint to check Moralis graduated tokens response."""
    from .services.data_collector import default_client

    try:
        # Fetch graduated tokens
        data = await default_client._make_request(
            "/token/mainnet/exchange/pumpfun/graduated",
            params={"limit": 5}
        )

        # Return first 3 tokens with relevant fields
        result = []
        for item in data.get("result", [])[:3]:
            result.append({
                "tokenAddress": item.get("tokenAddress"),
                "name": item.get("name"),
                "liquidity": item.get("liquidity"),
                "fullyDilutedValuation": item.get("fullyDilutedValuation"),
                "priceUsd": item.get("priceUsd"),
                "graduatedAt": item.get("graduatedAt"),
            })

        return {
            "status": "success",
            "count": len(data.get("result", [])),
            "sample": result,
            "raw_keys": list(data.get("result", [{}])[0].keys()) if data.get("result") else []
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Include API routers
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(acceleration.router, prefix="/api/acceleration", tags=["acceleration"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
