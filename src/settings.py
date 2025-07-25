"""Application settings using Pydantic BaseSettings"""

from pathlib import Path
from typing import Any, Dict
from pydantic import BaseSettings, Field
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
    def load(cls, yaml_path: Path | str = "config.yaml", env_file: str = ".env") -> "Settings":
        load_dotenv(env_file)
        path = Path(yaml_path)
        if path.exists():
            data: Dict[str, Any] = yaml.safe_load(path.read_text())
        else:
            raise FileNotFoundError(f"Config YAML not found: {yaml_path}")
        return cls.model_validate(data)
