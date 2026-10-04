"""Client for the Daikin Onecta cloud API."""

import json
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp
from mashumaro.exceptions import MissingField

from .exceptions import (
    OnectaApiError,
    OnectaAuthenticationError,
    OnectaConnectionError,
    OnectaRateLimitError,
    OnectaRequestError,
    OnectaResponseError,
)
from .models import GatewayDevice
from .rate_limit import RateLimit

ONECTA_API_URL = "https://api.onecta.daikineurope.com"


class OnectaClient:
    """Async client for the Daikin Onecta cloud API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        token_provider: Callable[[], Awaitable[str]],
        *,
        base_url: str = ONECTA_API_URL,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._token_provider = token_provider
        self._base_url = base_url.rstrip("/")
        self.rate_limit = RateLimit()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_data: Any = None,
    ) -> Any:
        """Perform an authenticated request to the Daikin Onecta API."""
        token = await self._token_provider()
        headers = {
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with self._session.request(
                method,
                f"{self._base_url}{path}",
                headers=headers,
                json=json_data,
            ) as response:
                self.rate_limit = RateLimit.from_headers(response.headers)
                response_text = await response.text()

                if response.status in (401, 403):
                    raise OnectaAuthenticationError(response.status, method=method, path=path)

                if response.status == 429:
                    raise OnectaRateLimitError(self.rate_limit, method=method, path=path)

                if response.status >= 400:
                    raise OnectaApiError(response.status, response_text, method=method, path=path)

                if response.status == 204 or not response_text:
                    return None

                try:
                    return json.loads(response_text)
                except json.JSONDecodeError as err:
                    raise OnectaResponseError(
                        response.status,
                        "Invalid JSON response",
                        method=method,
                        path=path,
                    ) from err
        except OnectaRequestError:
            raise
        except (TimeoutError, aiohttp.ClientError) as err:
            raise OnectaConnectionError(str(err), method=method, path=path) from err

    async def get_gateway_devices(self) -> list[GatewayDevice]:
        """Return all gateway devices available to the account."""
        data = await self._request("GET", "/v1/gateway-devices")
        if not isinstance(data, list):
            raise OnectaResponseError(
                200,
                "Expected a list of gateway devices",
                method="GET",
                path="/v1/gateway-devices",
            )
        try:
            return [GatewayDevice.from_dict(device) for device in data]
        except (MissingField, TypeError, ValueError) as err:
            raise OnectaResponseError(
                200,
                "Invalid gateway device data",
                method="GET",
                path="/v1/gateway-devices",
            ) from err

    async def set_schedule(
        self,
        gateway_id: str,
        management_point_id: str,
        mode: str,
        schedule: str,
        *,
        enabled: bool = True,
    ) -> None:
        """Select or disable a configured schedule for a management-point mode."""
        await self.put_management_point(
            gateway_id,
            management_point_id,
            f"schedule/{mode}/current",
            {"scheduleId": schedule, "enabled": enabled},
        )

    async def patch_characteristic(
        self,
        gateway_id: str,
        management_point_id: str,
        characteristic: str,
        value: Any,
        *,
        path: str | None = None,
    ) -> None:
        """Set a management-point characteristic."""
        body: dict[str, Any] = {"value": value}
        if path:
            body["path"] = path
        await self._request(
            "PATCH",
            f"/v1/gateway-devices/{gateway_id}/management-points/{management_point_id}"
            f"/characteristics/{characteristic}",
            json_data=body,
        )

    async def post_management_point(
        self,
        gateway_id: str,
        management_point_id: str,
        resource: str,
        value: Any,
    ) -> Any:
        """POST data to a management-point resource."""
        return await self._request(
            "POST",
            f"/v1/gateway-devices/{gateway_id}/management-points/{management_point_id}/{resource}",
            json_data=value,
        )

    async def put_management_point(
        self,
        gateway_id: str,
        management_point_id: str,
        resource: str,
        value: Any = None,
    ) -> Any:
        """PUT data to a management-point resource."""
        return await self._request(
            "PUT",
            f"/v1/gateway-devices/{gateway_id}/management-points/{management_point_id}/{resource}",
            json_data=value,
        )
