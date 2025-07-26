"""Application settings using Pydantic BaseSettings"""

from pathlib import Path
from typing import Any, Dict, Union, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field
import yaml
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    database: str = "scraping_db"
    user: str = "scraper"
    password: str = "password"


class ApiSettings(BaseSettings):
    url: str
    delay_min: float = 1.5
    delay_max: float = 2.5
    retry_attempts: int = 3


class Settings(BaseSettings):
    database: DatabaseSettings
    api: ApiSettings
    max_references: int = 2000

    def to_scraping_config(self):
        """Convert Settings to ScrapingConfig instance"""
        from src.core import ScrapingConfig

        return ScrapingConfig(
            reference_types=["specializations", "skills", "regions", "companies"],
            combinations=None,
        )

    @classmethod
    def load(cls, yaml_path: Union[Path, str] = "config.yaml", env_file: str = ".env") -> "Settings":
        load_dotenv(env_file)
        path = Path(yaml_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
        
        with open(path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Convert nested dicts to settings objects
        db_data = config_data.get('database', {})
        api_data = config_data.get('api', {})
        
        return cls(
            database=DatabaseSettings(**db_data),
            api=ApiSettings(**api_data),
            max_references=config_data.get('max_references', 2000)
        )
