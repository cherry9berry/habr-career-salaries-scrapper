import typer
import asyncio
from typing import Optional
from pathlib import Path
from src.settings import Settings
from src.database import PostgresRepository
from src.scraper import HabrApiClient, SalaryScraper
from src.async_api import AsyncHabrApiClient
from src.async_scraper import AsyncSalaryScraper
from scripts.update_references import update_reference
from scripts.clean_db import drop_test_table

app = typer.Typer(help="Salary scraper CLI")


def _load_repo() -> PostgresRepository:
    settings = Settings.load("config.yaml")
    return PostgresRepository(settings.database.model_dump())


@app.command()
def scrape(async_mode: bool = typer.Option(False, "--async", help="Use async scraper")):
    """Run scraping with current config.yaml"""
    settings = Settings.load("config.yaml")
    repo = _load_repo()
    if async_mode:
        client = AsyncHabrApiClient(**settings.api.model_dump())
        scraper = AsyncSalaryScraper(repo, client)
        asyncio.run(scraper.scrape(settings.to_scraping_config()))
    else:
        client = HabrApiClient(**settings.api.model_dump())
        scraper = SalaryScraper(repo, client)
        scraper.scrape(settings.to_scraping_config())


@app.command()
def update(table: str, file: Path):
    """Update reference table from Excel"""
    repo = _load_repo()
    update_reference(table, str(file), repo.config)


@app.command()
def clean():
    """Drop test_table from DB"""
    repo_cfg = _load_repo().config
    drop_test_table(repo_cfg)


if __name__ == "__main__":
    app() 