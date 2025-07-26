"""FastAPI application for salary scraper control"""

import os
import asyncio
import tempfile
import uuid
import requests
import time
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime
from dataclasses import asdict
import concurrent.futures

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
import uvicorn

from src.settings import Settings
from src.database import PostgresRepository
from src.scraper import HabrApiClient, SalaryScraper
from src.config_parser import CsvConfigParser, DefaultConfigParser
from src.core import ScrapingConfig

app = FastAPI(
    title="Salary Scraper API", description="API for controlling Habr Career salary data scraping", version="1.0.0"
)

# Global variables for application state
LOCK_FILE = Path("/tmp/scraper.lock")
current_job_id: Optional[str] = None
keep_alive_active = False

# Configuration: use SQLite for temporary storage (set via env var)
USE_SQLITE_TEMP = os.environ.get("USE_SQLITE_TEMP", "true").lower() == "true"

# Thread pool for blocking operations
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)


def keep_alive_ping():
    """Send periodic requests to keep Render.com service alive"""
    global keep_alive_active
    
    # Get service URL from environment or use localhost
    service_url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")
    ping_url = f"{service_url}/health"
    
    while keep_alive_active:
        try:
            # Wait 10 minutes before next ping
            time.sleep(600)  # 10 minutes
            
            if keep_alive_active:  # Check again after sleep
                requests.get(ping_url, timeout=30)
                print(f"[KEEP-ALIVE] Pinged {ping_url} to prevent sleep")
        except Exception as e:
            print(f"[KEEP-ALIVE] Ping failed: {e}")


def start_keep_alive():
    """Start keep-alive pinger in background thread"""
    global keep_alive_active
    if not keep_alive_active:
        keep_alive_active = True
        thread = threading.Thread(target=keep_alive_ping, daemon=True)
        thread.start()
        print("[KEEP-ALIVE] Started background pinger")


def stop_keep_alive():
    """Stop keep-alive pinger"""
    global keep_alive_active
    if keep_alive_active:
        keep_alive_active = False
        print("[KEEP-ALIVE] Stopped background pinger")


def is_scraping_running() -> bool:
    """Check if scraping is currently running"""
    return os.path.exists(LOCK_FILE)


def create_lock(job_id: str) -> None:
    """Create lock file to prevent concurrent scraping"""
    with open(LOCK_FILE, 'w') as f:
        f.write(f"{job_id}:{os.getpid()}:{datetime.now().isoformat()}")


def remove_lock() -> None:
    """Remove lock file"""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


async def run_scraper_task(config_parser, job_id: str):
    """Background task to run the scraper in separate thread"""
    global current_job_id
    current_job_id = job_id

    print(f"[{job_id}] Received scraping task at {datetime.now()}")
    print(f"[{job_id}] Storage type: {'SQLite' if USE_SQLITE_TEMP else 'PostgreSQL temp tables'}")

    # Start keep-alive to prevent Render.com sleep during long-running tasks
    start_keep_alive()

    try:
        # Run blocking scraper in thread pool
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(executor, run_scraper_sync, config_parser, job_id)

        if success:
            print(f"[{job_id}] Scraping completed successfully")
        else:
            print(f"[{job_id}] Scraping failed")

    except Exception as e:
        print(f"[{job_id}] Scraping error: {str(e)}")
    finally:
        stop_keep_alive()  # Stop keep-alive when task completes
        remove_lock()
        current_job_id = None


def run_scraper_sync(config_parser, job_id: str) -> bool:
    """Synchronous scraper execution"""
    try:
        # Load settings
        settings = Settings.load("config.yaml")

        # Choose repository implementation
        if USE_SQLITE_TEMP:
            from src.sqlite_storage import PostgresRepositoryWithSQLite

            repository = PostgresRepositoryWithSQLite(asdict(settings.database))
        else:
            repository = PostgresRepository(asdict(settings.database))

        # Create API client and scraper
        api_client = HabrApiClient(
            url=settings.api.url,
            delay_min=settings.api.delay_min,
            delay_max=settings.api.delay_max,
            retry_attempts=settings.api.retry_attempts,
        )
        scraper = SalaryScraper(repository, api_client)

        # Parse configuration
        config = config_parser.parse()

        print(f"[{job_id}] Starting scraping with config: {config.reference_types}")

        # Run scraping
        return scraper.scrape(config)

    except Exception as e:
        print(f"[{job_id}] Error in scraper: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    storage_type = "SQLite" if USE_SQLITE_TEMP else "PostgreSQL temp tables"

    return {
        "message": "Salary Scraper API",
        "version": "1.0.0",
        "temp_storage": storage_type,
        "documentation": "https://habr-career-salaries-scrapper.onrender.com/docs",
        "redoc": "https://habr-career-salaries-scrapper.onrender.com/redoc",
        "endpoints": {
            "GET /": "This endpoint - API information",
            "GET /health": "Health check and database status",
            "GET /api/status": "Current scraping status",
            "POST /api/scrape": "Start default scraping (all references)",
            "POST /api/scrape/upload": "Start custom scraping with CSV config file upload",
        },
        "examples": {
            "health_check": "curl https://habr-career-salaries-scrapper.onrender.com/health",
            "check_status": "curl https://habr-career-salaries-scrapper.onrender.com/api/status",
            "start_default_scraping": "curl -X POST https://habr-career-salaries-scrapper.onrender.com/api/scrape",
            "upload_config": "curl -X POST -F 'config=@your_config.csv' https://habr-career-salaries-scrapper.onrender.com/api/scrape/upload",
        },
    }


@app.get("/api")
async def api_redirect():
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")


@app.get("/swagger")
async def swagger_redirect():
    """Alternative redirect to API documentation"""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        settings = Settings.load("config.yaml")
        repository = PostgresRepository(asdict(settings.database))

        # Simple connection test
        with repository.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()

        storage_type = "SQLite" if USE_SQLITE_TEMP else "PostgreSQL temp tables"

        return {
            "status": "healthy",
            "database": "connected",
            "temp_storage": storage_type,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return JSONResponse(
            status_code=503, content={"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}
        )


@app.get("/api/status")
async def get_status():
    """Get current scraping status"""
    storage_type = "SQLite" if USE_SQLITE_TEMP else "PostgreSQL temp tables"

    if is_scraping_running():
        return {
            "status": "running",
            "job_id": current_job_id,
            "temp_storage": storage_type,
            "message": "Scraping in progress",
        }
    else:
        return {"status": "idle", "temp_storage": storage_type, "message": "No scraping in progress"}


@app.post("/api/scrape")
async def start_full_scraping(background_tasks: BackgroundTasks):
    """Start full scraping (all reference types)"""
    if is_scraping_running():
        raise HTTPException(status_code=409, detail="Scraping already in progress")

    job_id = str(uuid.uuid4())
    print(f"[API] Received full scraping request, job_id: {job_id}")
    create_lock(job_id)

    # Create default config parser
    config_parser = DefaultConfigParser()

    # Start background task
    background_tasks.add_task(run_scraper_task, config_parser, job_id)
    print(f"[API] Background task started for job {job_id}")

    storage_type = "SQLite" if USE_SQLITE_TEMP else "PostgreSQL temp tables"

    return {
        "status": "started",
        "job_id": job_id,
        "temp_storage": storage_type,
        "message": "Full scraping initiated",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/scrape/upload")
async def start_custom_scraping(
    background_tasks: BackgroundTasks, config: UploadFile = File(..., description="CSV configuration file")
):
    """Start scraping with uploaded CSV configuration"""
    if is_scraping_running():
        raise HTTPException(status_code=409, detail="Scraping already in progress")

    # Validate file type
    if not config.filename or not config.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    job_id = str(uuid.uuid4())
    print(f"[API] Received custom scraping request with file: {config.filename}, job_id: {job_id}")
    create_lock(job_id)

    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as temp_file:
            content = await config.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Create CSV config parser
        config_parser = CsvConfigParser()
        config_parser.csv_path = temp_file_path  # Set the path

        # Start background task
        background_tasks.add_task(run_scraper_task, config_parser, job_id)
        print(f"[API] Background task started for job {job_id} with CSV config")

        # Schedule cleanup of temp file
        background_tasks.add_task(cleanup_temp_file, temp_file_path)

        storage_type = "SQLite" if USE_SQLITE_TEMP else "PostgreSQL temp tables"

        return {
            "status": "started",
            "job_id": job_id,
            "temp_storage": storage_type,
            "message": f"Custom scraping initiated with {config.filename}",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        remove_lock()  # Remove lock on error
        raise HTTPException(status_code=500, detail=f"Failed to process configuration file: {str(e)}")


async def cleanup_temp_file(file_path: str):
    """Clean up temporary file after some delay"""
    await asyncio.sleep(10)  # Wait 10 seconds
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        pass  # Ignore cleanup errors


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
