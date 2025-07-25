"""Async API client using aiohttp"""
import aiohttp
import asyncio
import random
import urllib.parse
from typing import Dict, Any, Optional

class AsyncHabrApiClient:
    """Асинхронный клиент Habr Career API"""

    def __init__(self, url: str, delay_min: float = 1.5, delay_max: float = 2.5, retry_attempts: int = 3, *, timeout: int = 10):
        self.url = url
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.retry_attempts = retry_attempts
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def fetch_salary_data(self, **params) -> Optional[Dict[str, Any]]:
        """Запрос данных о зарплатах (асинхронно)"""
        api_params = {"employment_type": 0}
        if "spec_alias" in params:
            api_params["spec_aliases[]"] = params["spec_alias"]
        if "skill_aliases" in params:
            api_params["skills[]"] = params["skill_aliases"]
        if "region_alias" in params:
            api_params["region_aliases[]"] = params["region_alias"]
        if "company_alias" in params:
            api_params["company_alias"] = params["company_alias"]

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for attempt in range(self.retry_attempts):
                try:
                    async with session.get(self.url, params=api_params, ssl=False) as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        if not data.get("groups"):
                            print("Warning: Empty response", api_params)
                            return None
                        return data
                except Exception as e:
                    print(f"Async API error (attempt {attempt+1}/{self.retry_attempts}): {e}")
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self.delay_max)
        return None 