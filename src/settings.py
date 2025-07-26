"""Application settings using dataclasses"""

import os
from pathlib import Path
from typing import Any, Dict, Union, Optional
from dataclasses import dataclass

# Flag to check if dotenv is available
HAS_DOTENV = True
try:
    from dotenv import load_dotenv
except ImportError:
    HAS_DOTENV = False
    load_dotenv = None

# Flag to check if yaml is available
HAS_YAML = True
try:
    import yaml
except ImportError:
    HAS_YAML = False
    yaml = None

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class DatabaseSettings:
    host: str = "localhost"
    port: int = 5432
    database: str = "scraping_db"
    user: str = "scraper"
    password: str = "password"


@dataclass
class ApiSettings:
    url: str
    delay_min: float = 1.5
    delay_max: float = 2.5
    retry_attempts: int = 3


@dataclass
class Settings:
    database: DatabaseSettings
    api: ApiSettings
    max_references: int = 2000

    @classmethod
    def load(cls, yaml_path: Union[Path, str] = "config.yaml", env_file: str = ".env") -> "Settings":
        if HAS_DOTENV:
            load_dotenv(env_file)  # type: ignore

        # Try to load from environment variables first
        if os.environ.get("DATABASE_HOST"):
            # Env vars take precedence
            db_settings = DatabaseSettings(
                host=os.environ.get("DATABASE_HOST", "localhost"),
                port=int(os.environ.get("DATABASE_PORT", "5432")),
                database=os.environ.get("DATABASE_NAME", "scraping_db"),
                user=os.environ.get("DATABASE_USER", "scraper"),
                password=os.environ.get("DATABASE_PASSWORD", "password")
            )
            
            api_settings = ApiSettings(
                url=os.environ.get("API_URL", "https://career.habr.com/api/frontend_v1/salary_calculator/general_graph"),
                delay_min=float(os.environ.get("API_DELAY_MIN", "1.5")),
                delay_max=float(os.environ.get("API_DELAY_MAX", "2.5")),
                retry_attempts=int(os.environ.get("API_RETRY_ATTEMPTS", "3"))
            )
            
            max_refs = int(os.environ.get("MAX_REFERENCES", "2000"))
            
            return cls(
                database=db_settings,
                api=api_settings,
                max_references=max_refs
            )
            
        # Fall back to YAML file
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        if not HAS_YAML:
            raise ImportError("PyYAML is required to load configuration from YAML files")

        with open(path, "r") as f:
            config_data = yaml.safe_load(f)

        # Convert nested dicts to settings objects
        db_data = config_data.get("database", {})
        api_data = config_data.get("api", {})

        return cls(
            database=DatabaseSettings(**db_data),
            api=ApiSettings(**api_data),
            max_references=config_data.get("max_references", 2000),
        )
