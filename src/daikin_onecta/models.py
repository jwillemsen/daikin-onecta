"""Models returned by the Daikin Onecta API."""

from dataclasses import dataclass
from typing import Any

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


@dataclass(slots=True)
class Characteristic(DataClassDictMixin):
    """A Daikin management-point characteristic."""

    value: Any
    settable: bool = False
    values: list[Any] | None = None
    ref: str | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    step_value: int | float | None = None
    max_length: int | None = None

    class Config(BaseConfig):
        """Mashumaro configuration."""

        aliases = {
            "min_value": "minValue",
            "max_value": "maxValue",
            "step_value": "stepValue",
            "max_length": "maxLength",
        }


@dataclass(slots=True)
class ManagementPoint(DataClassDictMixin):
    """Stable management-point metadata and commonly used characteristics."""

    embedded_id: str
    management_point_type: str
    management_point_category: str | None = None
    management_point_sub_type: str | None = None
    name: Characteristic | None = None
    operation_mode: Characteristic | None = None
    on_off_mode: Characteristic | None = None
    software_version: Characteristic | None = None
    firmware_version: Characteristic | None = None
    model_info: Characteristic | None = None
    serial_number: Characteristic | None = None

    class Config(BaseConfig):
        """Mashumaro configuration."""

        aliases = {
            "embedded_id": "embeddedId",
            "management_point_type": "managementPointType",
            "management_point_category": "managementPointCategory",
            "management_point_sub_type": "managementPointSubType",
            "operation_mode": "operationMode",
            "on_off_mode": "onOffMode",
            "software_version": "softwareVersion",
            "firmware_version": "firmwareVersion",
            "model_info": "modelInfo",
            "serial_number": "serialNumber",
        }


@dataclass(slots=True)
class GatewayDevice(DataClassDictMixin):
    """A Daikin Onecta gateway device."""

    id: str
    device_model: str
    management_points: list[ManagementPoint]
    cloud_connection: Characteristic
    device_type: str | None = None
    embedded_id: str | None = None
    timestamp: str | None = None

    class Config(BaseConfig):
        """Mashumaro configuration."""

        aliases = {
            "device_model": "deviceModel",
            "management_points": "managementPoints",
            "cloud_connection": "isCloudConnectionUp",
            "device_type": "type",
            "embedded_id": "embeddedId",
        }

    @property
    def available(self) -> bool:
        """Return whether the gateway is connected to the Daikin cloud."""
        return bool(self.cloud_connection.value)
