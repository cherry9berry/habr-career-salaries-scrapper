"""Tests for AsyncHabrApiClient"""
import pytest
import asyncio
from unittest.mock import patch, Mock
from src.async_api import AsyncHabrApiClient

pytestmark = pytest.mark.asyncio


async def test_async_fetch_success(monkeypatch):
    client = AsyncHabrApiClient("https://api.test.com", delay_min=0, delay_max=0, retry_attempts=1)

    async def fake_get(*args, **kwargs):
        class FakeResp:
            status = 200
            async def json(self):
                return {"groups": [{"title": "ok"}]}
            def raise_for_status(self):
                pass
        return FakeResp()

    with patch("aiohttp.ClientSession.get", new=fake_get):
        result = await client.fetch_salary_data(spec_alias="backend")
        assert result is not None


async def test_async_fetch_empty(monkeypatch):
    client = AsyncHabrApiClient("https://api.test.com", delay_min=0, delay_max=0, retry_attempts=1)

    async def fake_get(*args, **kwargs):
        class FakeResp:
            status = 200
            async def json(self):
                return {"groups": []}
            def raise_for_status(self):
                pass
        return FakeResp()

    with patch("aiohttp.ClientSession.get", new=fake_get):
        result = await client.fetch_salary_data(skill_aliases=["python"])
        assert result is None 