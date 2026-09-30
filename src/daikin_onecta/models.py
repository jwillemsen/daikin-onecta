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
class ScheduleOption(OnectaModel):
    """A configured schedule that can be selected."""

    id: str
    name: str


@dataclass(slots=True)
class ScheduleSelection(OnectaModel):
    """Schedule selection state for one Daikin schedule mode."""

    mode: str
    selected: str
    options: list[ScheduleOption]
    enabled: bool
    enabled_settable: bool

    @property
    def current_option(self) -> str | None:
        """Return the readable name of the selected schedule."""
        if not self.enabled:
            return None
        return next((option.name for option in self.options if option.id == self.selected), self.selected)


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
            enabled = mode_data.get("enabled", {})
            schedules = mode_data.get("schedules", {})
            if not isinstance(selected, str) or not isinstance(available, list):
                continue
            options: list[ScheduleOption] = []
            for schedule_id in available:
                if not isinstance(schedule_id, str):
                    continue
                schedule_data = schedules.get(schedule_id, {})
                name_data = schedule_data.get("name", {})
                name = name_data.get("value") if isinstance(name_data, dict) else None
                options.append(ScheduleOption(id=schedule_id, name=name or schedule_id))
            result.append(
                ScheduleSelection(
                    mode=mode,
                    selected=selected,
                    options=options,
                    enabled=bool(enabled.get("value", False)),
                    enabled_settable=bool(enabled.get("settable", False)),
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
class ConsumptionSeries(OnectaModel):
    """Consumption values for the API day, week, and month buckets."""

    day: list[int | float | None] | None = None
    week: list[int | float | None] | None = None
    month: list[int | float | None] | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {"day": "d", "week": "w", "month": "m"}


@dataclass(slots=True)
class ConsumptionByPurpose(OnectaModel):
    """Consumption series split by heating and cooling."""

    heating: ConsumptionSeries | None = None
    cooling: ConsumptionSeries | None = None


@dataclass(slots=True)
class ConsumptionSource(ConsumptionByPurpose):
    """Consumption for one energy source."""

    unit: str | None = None


@dataclass(slots=True)
class ConsumptionData(OnectaModel):
    """Consumption grouped by energy source."""

    electrical: ConsumptionSource | None = None
    gas: ConsumptionSource | None = None


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
    consumption_data: Characteristic[ConsumptionData] | None = None
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

    def characteristic(self, name: str) -> Characteristic[Any] | None:
        """Return any simple characteristic by its Daikin API name.

        This supports entity discovery for characteristics that don't need a
        dedicated semantic model while keeping complex values explicitly typed.
        """
        data = self.to_dict(by_alias=True)
        value = data.get(name)
        if not isinstance(value, dict) or "value" not in value:
            return None
        if isinstance(value["value"], dict):
            return None
        return Characteristic[Any].from_dict(value)

    def simple_characteristics(self) -> dict[str, Characteristic[Any]]:
        """Return all scalar/list-valued characteristics on this management point."""
        metadata = {
            "embeddedId",
            "managementPointType",
            "managementPointCategory",
            "managementPointSubType",
        }
        result: dict[str, Characteristic[Any]] = {}
        for name, value in self.to_dict(by_alias=True).items():
            if name in metadata or not isinstance(value, dict) or "value" not in value:
                continue
            if isinstance(value["value"], dict):
                continue
            result[name] = Characteristic[Any].from_dict(value)
        return result



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
