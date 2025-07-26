#!/usr/bin/env python3
"""
Startup script for Salary Scraper API
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    # Get configuration from environment or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    print(f"Starting Salary Scraper API on {host}:{port}")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("Status: http://localhost:8000/api/status")

    # Run the API
    uvicorn.run("src.api.app:app", host=host, port=port, reload=False, log_level="info")  # Set to True for development
