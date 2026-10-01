"""Tests for the Daikin Onecta client."""

import aiohttp
import pytest
from aioresponses import aioresponses
from yarl import URL

from daikin_onecta import (
    OnectaApiError,
    OnectaAuthenticationError,
    OnectaClient,
    OnectaConnectionError,
    OnectaRateLimitError,
)

BASE_URL = "https://api.onecta.daikineurope.com"


async def token_provider() -> str:
    """Return a test access token."""
    return "token"


@pytest.mark.asyncio
async def test_get_gateway_devices() -> None:
    """Return gateway devices from the API."""
    payload = [
        {
            "id": "gateway-1",
            "deviceModel": "test",
            "isCloudConnectionUp": {"value": True, "settable": False},
            "managementPoints": [],
        }
    ]

    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(
                f"{BASE_URL}/v1/gateway-devices",
                payload=payload,
                headers={"X-RateLimit-Remaining-day": "123"},
            )
            client = OnectaClient(session, token_provider)

            devices = await client.get_gateway_devices()

            assert len(devices) == 1
            assert devices[0].id == "gateway-1"
            assert devices[0].device_model == "test"
            assert devices[0].available is True
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


@pytest.mark.asyncio
async def test_set_schedule() -> None:
    """Select an existing schedule through the schedule endpoint."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            url = f"{BASE_URL}/v1/gateway-devices/gateway-1/management-points/climateControl/schedule/heating/current"
            mocked.put(url, status=204)
            client = OnectaClient(session, token_provider)

            await client.set_schedule("gateway-1", "climateControl", "heating", "scheduleHeatingRT2")

            request = mocked.requests[("PUT", URL(url))][0]
            assert request.kwargs["json"] == {
                "scheduleId": "scheduleHeatingRT2",
                "enabled": True,
            }


@pytest.mark.asyncio
async def test_invalid_json_response() -> None:
    """Translate a successful non-JSON response to an API error."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(f"{BASE_URL}/v1/gateway-devices", status=200, body="not json")
            client = OnectaClient(session, token_provider)

            with pytest.raises(OnectaApiError, match="Invalid JSON response"):
                await client.get_gateway_devices()


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [None, {"id": "gateway-1"}])
async def test_gateway_devices_requires_list(payload: object) -> None:
    """Reject a gateway-device response that is not a list."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(f"{BASE_URL}/v1/gateway-devices", payload=payload)
            client = OnectaClient(session, token_provider)

            with pytest.raises(OnectaApiError, match="Expected a list of gateway devices"):
                await client.get_gateway_devices()


@pytest.mark.asyncio
async def test_invalid_gateway_device() -> None:
    """Translate invalid gateway-device data to an API error."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(f"{BASE_URL}/v1/gateway-devices", payload=[{"id": "gateway-1"}])
            client = OnectaClient(session, token_provider)

            with pytest.raises(OnectaApiError, match="Invalid gateway device data"):
                await client.get_gateway_devices()


@pytest.mark.asyncio
async def test_connection_error() -> None:
    """Translate aiohttp connection failures to a dedicated exception."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            mocked.get(f"{BASE_URL}/v1/gateway-devices", exception=aiohttp.ClientConnectionError("offline"))
            client = OnectaClient(session, token_provider)

            with pytest.raises(OnectaConnectionError, match="offline"):
                await client.get_gateway_devices()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (None, {"value": "heating"}),
        ("/operationModes/heating", {"value": 21.5, "path": "/operationModes/heating"}),
    ],
)
async def test_patch_characteristic(path: str | None, expected: dict[str, object]) -> None:
    """Patch a characteristic with an optional nested path."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            url = (
                f"{BASE_URL}/v1/gateway-devices/gateway-1/management-points/climateControl"
                "/characteristics/operationMode"
            )
            mocked.patch(url, status=204)
            client = OnectaClient(session, token_provider)

            value = "heating" if path is None else 21.5
            await client.patch_characteristic("gateway-1", "climateControl", "operationMode", value, path=path)

            request = mocked.requests[("PATCH", URL(url))][0]
            assert request.kwargs["json"] == expected


@pytest.mark.asyncio
async def test_post_management_point() -> None:
    """Return JSON data from a management-point POST."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            url = f"{BASE_URL}/v1/gateway-devices/gateway-1/management-points/climateControl/refresh"
            mocked.post(url, payload={"status": "accepted"})
            client = OnectaClient(session, token_provider)

            result = await client.post_management_point("gateway-1", "climateControl", "refresh", {"force": True})

            assert result == {"status": "accepted"}
            request = mocked.requests[("POST", URL(url))][0]
            assert request.kwargs["json"] == {"force": True}


@pytest.mark.asyncio
async def test_put_management_point_custom_base_url() -> None:
    """Normalize a custom base URL and return PUT response data."""
    base_url = "https://example.test/"
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            url = "https://example.test/v1/gateway-devices/gateway-1/management-points/climateControl/resource"
            mocked.put(url, payload={"updated": True})
            client = OnectaClient(session, token_provider, base_url=base_url)

            result = await client.put_management_point("gateway-1", "climateControl", "resource")

            assert result == {"updated": True}
            request = mocked.requests[("PUT", URL(url))][0]
            assert request.kwargs["json"] is None


@pytest.mark.asyncio
async def test_disable_schedule() -> None:
    """Disable a configured schedule."""
    async with aiohttp.ClientSession() as session:
        with aioresponses() as mocked:
            url = f"{BASE_URL}/v1/gateway-devices/gateway-1/management-points/climateControl/schedule/heating/current"
            mocked.put(url, status=204)
            client = OnectaClient(session, token_provider)

            await client.set_schedule(
                "gateway-1",
                "climateControl",
                "heating",
                "scheduleHeatingRT2",
                enabled=False,
            )

            request = mocked.requests[("PUT", URL(url))][0]
            assert request.kwargs["json"] == {
                "scheduleId": "scheduleHeatingRT2",
                "enabled": False,
            }
