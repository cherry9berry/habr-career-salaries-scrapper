"""Async version of SalaryScraper"""

import asyncio
from typing import List
from src.core import IRepository, ScrapingConfig, Reference, SalaryData
from src.async_api import AsyncHabrApiClient


class AsyncSalaryScraper:
    """Асинхронный скрапер с параллельными запросами"""

    def __init__(
        self, repository: IRepository, api_client: AsyncHabrApiClient, concurrency: int = 10
    ):
        self.repository = repository
        self.api_client = api_client
        self.semaphore = asyncio.Semaphore(concurrency)

    async def scrape(self, config: ScrapingConfig) -> bool:
        transaction_id = "async-transaction"
        tasks: List[asyncio.Task] = []

        for ref_type in config.reference_types:
            refs = self.repository.get_references(ref_type)
            for ref in refs:
                tasks.append(asyncio.create_task(self._process_ref(ref_type, ref, transaction_id)))

        if tasks:
            await asyncio.gather(*tasks)

        self.repository.commit_transaction(transaction_id)
        return True

    async def _process_ref(self, ref_type: str, ref: Reference, transaction_id: str):
        async with self.semaphore:
            params = self._build_params(ref_type, ref)
            data = await self.api_client.fetch_salary_data(**params)
            if data:
                salary_data = SalaryData(data=data, reference_id=ref.id, reference_type=ref_type)
                self.repository.save_report(salary_data, transaction_id)

    @staticmethod
    def _build_params(ref_type: str, ref: Reference):
        mapping = {
            "specializations": ("spec_alias", ref.alias),
            "skills": ("skill_aliases", [ref.alias]),
            "regions": ("region_alias", ref.alias),
            "companies": ("company_alias", ref.alias),
        }
        key, value = mapping.get(ref_type, (None, None))
        return {key: value} if key else {}
