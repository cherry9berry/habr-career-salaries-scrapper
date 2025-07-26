"""Tests for AsyncHabrApiClient"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from src.async_api import AsyncHabrApiClient


@pytest.mark.asyncio
async def test_async_fetch_success():
    client = AsyncHabrApiClient("https://api.test.com", delay_min=0, delay_max=0, retry_attempts=1)

    # Create mock response that will be returned by the context manager
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"groups": [{"title": "ok"}]})
    mock_response.raise_for_status = Mock()

    # Create mock context manager
    mock_get_context = AsyncMock()
    mock_get_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_context.__aexit__ = AsyncMock(return_value=None)

    # Mock ClientSession.get to return our context manager
    with patch("aiohttp.ClientSession.get", return_value=mock_get_context) as mock_get:
        result = await client.fetch_salary_data(spec_alias="backend")

        # Verify the result
        assert result is not None
        assert result == {"groups": [{"title": "ok"}]}

        # Verify calls
        mock_get.assert_called_once()
        mock_get_context.__aenter__.assert_called_once()
        mock_response.json.assert_called_once()


@pytest.mark.asyncio
async def test_async_fetch_empty():
    client = AsyncHabrApiClient("https://api.test.com", delay_min=0, delay_max=0, retry_attempts=1)

    # Create mock response that will be returned by the context manager
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"groups": []})
    mock_response.raise_for_status = Mock()

    # Create mock context manager
    mock_get_context = AsyncMock()
    mock_get_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_context.__aexit__ = AsyncMock(return_value=None)

    # Mock ClientSession.get to return our context manager
    with patch("aiohttp.ClientSession.get", return_value=mock_get_context):
        result = await client.fetch_salary_data(spec_alias="backend")

        # Should return None for empty groups
        assert result is None
