"""Tests for the Daikin Onecta client."""

import aiohttp
import pytest
from aioresponses import aioresponses

from daikin_onecta import (
    OnectaApiError,
    OnectaAuthenticationError,
    OnectaClient,
    OnectaRateLimitError,
)

BASE_URL = "https://api.onecta.daikineurope.com"


async def token_provider() -> str:
    """Return a test access token."""
    return "token"


@pytest.mark.asyncio
async def test_get_gateway_devices() -> None:
    """Return gateway devices from the API."""
    payload = [{"id": "gateway-1", "deviceModel": "test"}]

    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(
                f"{BASE_URL}/v1/gateway-devices",
                payload=payload,
                headers={"X-RateLimit-Remaining-day": "123"},
            )
            client = OnectaClient(session, token_provider)

            assert await client.get_gateway_devices() == payload
            assert client.rate_limit.day_remaining == 123


@pytest.mark.asyncio
async def test_rate_limit_error() -> None:
    """Expose Daikin retry-after information on HTTP 429."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(
                f"{BASE_URL}/v1/gateway-devices",
                status=429,
                headers={"Retry-After": "60"},
            )
            client = OnectaClient(session, token_provider)

            with pytest.raises(OnectaRateLimitError) as exc_info:
                await client.get_gateway_devices()

            assert exc_info.value.retry_after == 60


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403])
async def test_authentication_error(status: int) -> None:
    """Translate authentication failures to a dedicated exception."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(f"{BASE_URL}/v1/gateway-devices", status=status)
            client = OnectaClient(session, token_provider)

            with pytest.raises(OnectaAuthenticationError):
                await client.get_gateway_devices()


@pytest.mark.asyncio
async def test_unexpected_api_error() -> None:
    """Raise an API error instead of returning an empty device list."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(f"{BASE_URL}/v1/gateway-devices", status=500, body="server error")
            client = OnectaClient(session, token_provider)

            with pytest.raises(OnectaApiError) as exc_info:
                await client.get_gateway_devices()

            assert exc_info.value.status == 500
