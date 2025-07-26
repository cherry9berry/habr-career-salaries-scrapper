"""FastAPI application for salary scraper control"""

import os
import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime
from dataclasses import asdict

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from src.settings import Settings
from src.database import PostgresRepository
from src.scraper import HabrApiClient, SalaryScraper
from src.config_parser import CsvConfigParser, DefaultConfigParser

app = FastAPI(
    title="Salary Scraper API",
    description="API for controlling Habr Career salary data scraping",
    version="1.0.0"
)

# Global variables for application state
LOCK_FILE = "/tmp/scraper.lock"
current_job_id: Optional[str] = None


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
    """Background task to run the scraper"""
    global current_job_id
    current_job_id = job_id
    
    try:
        # Load settings
        settings = Settings.load("config.yaml")
        
        # Create components
        repository = PostgresRepository(asdict(settings.database))
        api_client = HabrApiClient(
            url=settings.api.url,
            delay_min=settings.api.delay_min,
            delay_max=settings.api.delay_max,
            retry_attempts=settings.api.retry_attempts
        )
        scraper = SalaryScraper(repository, api_client)
        
        # Parse configuration
        config = config_parser.parse()
        
        print(f"Starting scraper job {job_id} at {datetime.now()}")
        
        # Run scraping
        success = scraper.scrape(config)
        
        if success:
            print(f"Scraper job {job_id} completed successfully")
        else:
            print(f"Scraper job {job_id} failed")
            
    except Exception as e:
        print(f"Scraper job {job_id} error: {str(e)}")
    finally:
        # Always cleanup
        remove_lock()
        current_job_id = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Salary Scraper API", "version": "1.0.0"}


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
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/api/status")
async def get_status():
    """Get current scraping status"""
    if is_scraping_running():
        return {
            "status": "running",
            "job_id": current_job_id,
            "message": "Scraping in progress"
        }
    else:
        return {
            "status": "idle",
            "message": "No scraping in progress"
        }


@app.post("/api/scrape")
async def start_full_scraping(background_tasks: BackgroundTasks):
    """Start full scraping (all reference types)"""
    if is_scraping_running():
        raise HTTPException(
            status_code=409, 
            detail="Scraping already in progress"
        )
    
    job_id = str(uuid.uuid4())
    create_lock(job_id)
    
    # Create default config parser
    config_parser = DefaultConfigParser()
    
    # Start background task
    background_tasks.add_task(run_scraper_task, config_parser, job_id)
    
    return {
        "status": "started",
        "job_id": job_id,
        "message": "Full scraping initiated",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/scrape/upload")
async def start_custom_scraping(
    background_tasks: BackgroundTasks,
    config: UploadFile = File(..., description="CSV configuration file")
):
    """Start scraping with uploaded CSV configuration"""
    if is_scraping_running():
        raise HTTPException(
            status_code=409,
            detail="Scraping already in progress"
        )
    
    # Validate file type
    if not config.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )
    
    job_id = str(uuid.uuid4())
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
        
        # Schedule cleanup of temp file
        background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return {
            "status": "started",
            "job_id": job_id,
            "message": f"Custom scraping initiated with {config.filename}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        remove_lock()  # Remove lock on error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process configuration file: {str(e)}"
        )


async def cleanup_temp_file(file_path: str):
    """Clean up temporary file after some delay"""
    await asyncio.sleep(10)  # Wait 10 seconds
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass  # Ignore cleanup errors


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 