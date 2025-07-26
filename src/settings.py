"""Application settings using dataclasses"""

from pathlib import Path
from typing import Any, Dict, Union, Optional
from dataclasses import dataclass

try:
    import yaml
except ImportError:
    yaml = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda x: None

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
        if load_dotenv:
            load_dotenv(env_file)

        path = Path(yaml_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        if yaml is None:
            raise ImportError("PyYAML is required to load configuration from YAML files")

        with open(path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Convert nested dicts to settings objects
        db_data = config_data.get('database', {})
        api_data = config_data.get('api', {})

        return cls(
            database=DatabaseSettings(**db_data),
            api=ApiSettings(**api_data),
            max_references=config_data.get('max_references', 2000),
        )
