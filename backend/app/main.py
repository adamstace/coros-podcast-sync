"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from .config import settings, ensure_directories
from .database import init_db
from .tasks.scheduler import task_scheduler
from .tasks.auto_download import auto_download_task, check_for_new_episodes
from .tasks.auto_cleanup import auto_cleanup_task


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Coros Podcast Sync application...")
    ensure_directories()
    init_db()
    logger.info("Database initialized")

    # Start background task scheduler
    task_scheduler.start()

    # Add auto-download task if enabled
    if settings.auto_download:
        check_interval = settings.check_interval_minutes
        task_scheduler.add_interval_job(
            func=auto_download_task,
            minutes=check_interval,
            job_id="auto_download",
            description=f"Auto-download new episodes (every {check_interval} minutes)"
        )
        logger.info(f"Auto-download task scheduled (interval: {check_interval} minutes)")

    # Add auto-cleanup task if enabled
    if settings.auto_cleanup_enabled:
        cleanup_interval = settings.cleanup_interval_hours
        task_scheduler.add_interval_job(
            func=auto_cleanup_task,
            hours=cleanup_interval,
            job_id="auto_cleanup",
            description=f"Auto-cleanup storage (every {cleanup_interval} hours)"
        )
        logger.info(f"Auto-cleanup task scheduled (interval: {cleanup_interval} hours)")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    task_scheduler.shutdown()
    logger.info("Task scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title="Coros Podcast Sync",
    description="Podcast synchronization application for Coros running watches",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": "development" if settings.debug else "production"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Coros Podcast Sync API",
        "docs": "/docs",
        "health": "/api/health"
    }


# Import and include routers
from .api import podcasts, episodes, websocket, sync, storage, settings as settings_api

app.include_router(podcasts.router, prefix="/api/podcasts", tags=["podcasts"])
app.include_router(episodes.router, prefix="/api/episodes", tags=["episodes"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])
app.include_router(storage.router, prefix="/api/storage", tags=["storage"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(websocket.router, tags=["websocket"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
