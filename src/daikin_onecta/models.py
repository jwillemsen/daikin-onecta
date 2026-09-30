"""Models returned by the Daikin Onecta API."""

from dataclasses import dataclass
from typing import Any
from typing import Generic
from typing import TypeVar

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig

T = TypeVar("T")


class OnectaModel(DataClassDictMixin):
    """Base model using Daikin API field aliases."""

    class Config(BaseConfig):
        """Mashumaro configuration."""

        omit_none = True


@dataclass(slots=True)
class Characteristic(OnectaModel, Generic[T]):
    """Common envelope used by Daikin management-point characteristics."""

    value: T
    settable: bool = False
    values: list[T] | None = None
    ref: str | None = None
    requires_reboot: bool | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    step_value: int | float | None = None
    max_length: int | None = None
    unit: str | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {
            "requires_reboot": "requiresReboot",
            "min_value": "minValue",
            "max_value": "maxValue",
            "step_value": "stepValue",
            "max_length": "maxLength",
        }


@dataclass(slots=True)
class Setpoint(OnectaModel):
    """Temperature or offset setpoint."""

    value: int | float
    settable: bool = False
    min_value: int | float | None = None
    max_value: int | float | None = None
    step_value: int | float | None = None
    unit: str | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {
            "min_value": "minValue",
            "max_value": "maxValue",
            "step_value": "stepValue",
        }


@dataclass(slots=True)
class OperationModeSetpoints(OnectaModel):
    """Setpoints available for an operation mode."""

    setpoints: dict[str, Setpoint]


@dataclass(slots=True)
class TemperatureControl(OnectaModel):
    """Temperature control grouped by operation mode."""

    operation_modes: dict[str, OperationModeSetpoints]

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {"operation_modes": "operationModes"}


@dataclass(slots=True)
class ScheduleSelection(OnectaModel):
    """A selectable schedule for one Daikin schedule mode."""

    mode: str
    selected: str
    available: list[str]
    settable: bool


@dataclass(slots=True)
class Schedule(OnectaModel):
    """Schedule data used to select a configured schedule."""

    current_mode: Characteristic[str] | None = None
    modes: dict[str, dict[str, Any]] | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {"current_mode": "currentMode"}

    @property
    def selections(self) -> list[ScheduleSelection]:
        """Return selectable schedules without exposing schedule actions."""
        result: list[ScheduleSelection] = []
        for mode, mode_data in (self.modes or {}).items():
            current = mode_data.get("currentSchedule")
            if not isinstance(current, dict):
                continue
            selected = current.get("value")
            available = current.get("values")
            if not isinstance(selected, str) or not isinstance(available, list):
                continue
            result.append(
                ScheduleSelection(
                    mode=mode,
                    selected=selected,
                    available=[value for value in available if isinstance(value, str)],
                    settable=bool(current.get("settable", False)),
                )
            )
        return result


@dataclass(slots=True)
class HolidayMode(OnectaModel):
    """Holiday mode state."""

    enabled: bool
    start_date: str | None = None
    end_date: str | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {"start_date": "startDate", "end_date": "endDate"}


@dataclass(slots=True)
class SensoryData(OnectaModel):
    """Named sensor characteristics exposed by a management point."""

    room_temperature: Characteristic[int | float] | None = None
    outdoor_temperature: Characteristic[int | float] | None = None
    leaving_water_temperature: Characteristic[int | float] | None = None
    tank_temperature: Characteristic[int | float] | None = None
    room_humidity: Characteristic[int | float] | None = None
    pm1_concentration: Characteristic[int | float] | None = None
    pm25_concentration: Characteristic[int | float] | None = None
    pm10_concentration: Characteristic[int | float] | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {
            "room_temperature": "roomTemperature",
            "outdoor_temperature": "outdoorTemperature",
            "leaving_water_temperature": "leavingWaterTemperature",
            "tank_temperature": "tankTemperature",
            "room_humidity": "roomHumidity",
            "pm1_concentration": "pm1Concentration",
            "pm25_concentration": "pm25Concentration",
            "pm10_concentration": "pm10Concentration",
        }


@dataclass(slots=True)
class FanSpeedMode(OnectaModel):
    """Numeric fan-speed mode."""

    value: int | float
    settable: bool = False
    min_value: int | float | None = None
    max_value: int | float | None = None
    step_value: int | float | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {
            "min_value": "minValue",
            "max_value": "maxValue",
            "step_value": "stepValue",
        }


@dataclass(slots=True)
class FanSpeed(OnectaModel):
    """Fan-speed selection for an operation mode."""

    current_mode: Characteristic[str]
    modes: dict[str, FanSpeedMode] | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {"current_mode": "currentMode"}


@dataclass(slots=True)
class FanDirectionAxis(OnectaModel):
    """Fan-direction selection for one axis."""

    current_mode: Characteristic[str]

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {"current_mode": "currentMode"}


@dataclass(slots=True)
class FanDirection(OnectaModel):
    """Horizontal and vertical fan-direction controls."""

    horizontal: FanDirectionAxis | None = None
    vertical: FanDirectionAxis | None = None


@dataclass(slots=True)
class FanOperationMode(OnectaModel):
    """Fan controls for one HVAC operation mode."""

    fan_speed: FanSpeed | None = None
    fan_direction: FanDirection | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {"fan_speed": "fanSpeed", "fan_direction": "fanDirection"}


@dataclass(slots=True)
class FanControl(OnectaModel):
    """Fan controls grouped by HVAC operation mode."""

    operation_modes: dict[str, FanOperationMode]

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {"operation_modes": "operationModes"}


@dataclass(slots=True)
class ManagementPoint(OnectaModel):
    """A Daikin management point.

    Simple characteristics use the common typed envelope. Complex trees are
    modeled separately when their structure is stable across device families.
    """

    embedded_id: str
    management_point_type: str
    management_point_category: str | None = None
    management_point_sub_type: str | None = None
    name: Characteristic[str] | None = None
    operation_mode: Characteristic[str] | None = None
    on_off_mode: Characteristic[str] | None = None
    software_version: Characteristic[str] | None = None
    firmware_version: Characteristic[str] | None = None
    model_info: Characteristic[str] | None = None
    serial_number: Characteristic[str] | None = None
    error_code: Characteristic[str] | None = None
    is_in_error_state: Characteristic[bool] | None = None
    is_in_warning_state: Characteristic[bool] | None = None
    is_in_caution_state: Characteristic[bool] | None = None
    temperature_control: Characteristic[TemperatureControl] | None = None
    sensory_data: Characteristic[SensoryData] | None = None
    fan_control: Characteristic[FanControl] | None = None
    schedule: Characteristic[Schedule] | None = None
    consumption_data: Characteristic[dict[str, Any]] | None = None
    holiday_mode: Characteristic[HolidayMode] | None = None

    class Config(OnectaModel.Config):
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
            "error_code": "errorCode",
            "is_in_error_state": "isInErrorState",
            "is_in_warning_state": "isInWarningState",
            "is_in_caution_state": "isInCautionState",
            "temperature_control": "temperatureControl",
            "sensory_data": "sensoryData",
            "fan_control": "fanControl",
            "consumption_data": "consumptionData",
            "holiday_mode": "holidayMode",
        }


@dataclass(slots=True)
class GatewayDevice(OnectaModel):
    """A Daikin Onecta gateway device."""

    id: str
    device_model: str
    management_points: list[ManagementPoint]
    cloud_connection: Characteristic[bool]
    device_type: str | None = None
    embedded_id: str | None = None
    timestamp: str | None = None
    last_update_received: str | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {
            "device_model": "deviceModel",
            "management_points": "managementPoints",
            "cloud_connection": "isCloudConnectionUp",
            "device_type": "type",
            "embedded_id": "embeddedId",
            "last_update_received": "lastUpdateReceived",
        }

    @property
    def available(self) -> bool:
        """Return whether the gateway is connected to the Daikin cloud."""
        return self.cloud_connection.value
