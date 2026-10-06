"""Async client for the Daikin Onecta cloud API."""

from .auth import get_account_id
from .client import OnectaClient
from .climate import ClimateControlClient
from .domestic_hot_water import DomesticHotWaterClient
from .exceptions import (
    OnectaAccessTokenError,
    OnectaApiError,
    OnectaAuthenticationError,
    OnectaConnectionError,
    OnectaError,
    OnectaRateLimitError,
    OnectaRequestError,
    OnectaResponseError,
)
from .firmware import FirmwareClient
from .models import (
    ClimateControl,
    DomesticHotWater,
    Firmware,
    GatewayDevice,
    ScheduleState,
)
from .rate_limit import RateLimit
from .schedule import ScheduleClient

__all__ = [
    "GatewayDevice",
    "ClimateControl",
    "ClimateControlClient",
    "DomesticHotWater",
    "DomesticHotWaterClient",
    "FirmwareClient",
    "Firmware",
    "OnectaAccessTokenError",
    "OnectaApiError",
    "OnectaAuthenticationError",
    "OnectaClient",
    "OnectaConnectionError",
    "OnectaError",
    "OnectaRateLimitError",
    "OnectaRequestError",
    "OnectaResponseError",
    "RateLimit",
    "ScheduleClient",
    "ScheduleState",
    "get_account_id",
]
