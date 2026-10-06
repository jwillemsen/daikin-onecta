"""Models returned by the Daikin Onecta API."""

from dataclasses import dataclass, field
from typing import Any

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


class OnectaModel(DataClassDictMixin):
    """Base model using Daikin API field aliases."""

    class Config(BaseConfig):
        """Mashumaro configuration."""

        omit_none = True


@dataclass(slots=True)
class Characteristic[T](OnectaModel):
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
    """Fan controls grouped by HVAC or air-purification operation mode."""

    operation_modes: dict[str, FanOperationMode] | None = None
    air_purification_modes: dict[str, FanOperationMode] | None = None

    class Config(OnectaModel.Config):
        """Mashumaro configuration."""

        aliases = {
            "operation_modes": "operationModes",
            "air_purification_modes": "airPurificationModes",
        }


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
    """Energy data grouped by energy source."""

    electrical: ConsumptionSource | None = None
    gas: ConsumptionSource | None = None
    thermal: ConsumptionSource | None = None


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
    eeprom_version: Characteristic[str] | None = None
    model_info: Characteristic[str] | None = None
    serial_number: Characteristic[str] | None = None
    error_code: Characteristic[str] | None = None
    is_in_error_state: Characteristic[bool] | None = None
    is_in_warning_state: Characteristic[bool] | None = None
    is_in_caution_state: Characteristic[bool] | None = None
    is_firmware_update_supported: Characteristic[bool] | None = None
    firmware_update: Characteristic[dict[str, Any]] | None = None
    firmware_update_status: Characteristic[str] | None = None
    temperature_control: Characteristic[TemperatureControl] | None = None
    sensory_data: Characteristic[SensoryData] | None = None
    fan_control: Characteristic[FanControl] | None = None
    schedule: Characteristic[Schedule] | None = None
    consumption_data: Characteristic[ConsumptionData] | None = None
    output_data: Characteristic[ConsumptionData] | None = None
    holiday_mode: Characteristic[HolidayMode] | None = None
    characteristics: dict[str, Characteristic[Any]] = field(default_factory=dict)

    @classmethod
    def __pre_deserialize__(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Collect unmodeled simple characteristics before deserialization."""
        data = dict(data)
        known = {
            "embeddedId",
            "managementPointType",
            "managementPointCategory",
            "managementPointSubType",
            "name",
            "operationMode",
            "onOffMode",
            "softwareVersion",
            "firmwareVersion",
            "eepromVersion",
            "modelInfo",
            "serialNumber",
            "errorCode",
            "isInErrorState",
            "isInWarningState",
            "isInCautionState",
            "isFirmwareUpdateSupported",
            "firmwareUpdate",
            "firmwareUpdateStatus",
            "temperatureControl",
            "sensoryData",
            "fanControl",
            "schedule",
            "consumptionData",
            "outputData",
            "holidayMode",
        }
        data["characteristics"] = {
            name: value
            for name, value in data.items()
            if name not in known
            and isinstance(value, dict)
            and "value" in value
            and not isinstance(value["value"], dict)
        }
        return data

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
            "eeprom_version": "eepromVersion",
            "model_info": "modelInfo",
            "serial_number": "serialNumber",
            "error_code": "errorCode",
            "is_in_error_state": "isInErrorState",
            "is_in_warning_state": "isInWarningState",
            "is_in_caution_state": "isInCautionState",
            "is_firmware_update_supported": "isFirmwareUpdateSupported",
            "firmware_update": "firmwareUpdate",
            "firmware_update_status": "firmwareUpdateStatus",
            "temperature_control": "temperatureControl",
            "sensory_data": "sensoryData",
            "fan_control": "fanControl",
            "consumption_data": "consumptionData",
            "output_data": "outputData",
            "holiday_mode": "holidayMode",
        }

    def characteristic(self, name: str) -> Characteristic[Any] | None:
        """Return a characteristic by its Daikin API name."""
        modeled = {
            "name": self.name,
            "operationMode": self.operation_mode,
            "onOffMode": self.on_off_mode,
            "softwareVersion": self.software_version,
            "firmwareVersion": self.firmware_version,
            "eepromVersion": self.eeprom_version,
            "modelInfo": self.model_info,
            "serialNumber": self.serial_number,
            "errorCode": self.error_code,
            "isInErrorState": self.is_in_error_state,
            "isInWarningState": self.is_in_warning_state,
            "isInCautionState": self.is_in_caution_state,
            "isFirmwareUpdateSupported": self.is_firmware_update_supported,
            "firmwareUpdateStatus": self.firmware_update_status,
        }
        return modeled.get(name) or self.characteristics.get(name)

    def simple_characteristics(self) -> dict[str, Characteristic[Any]]:
        """Return scalar/list-valued characteristics for entity discovery."""
        result = dict(self.characteristics)
        for name in (
            "name",
            "operationMode",
            "onOffMode",
            "softwareVersion",
            "firmwareVersion",
            "eepromVersion",
            "modelInfo",
            "serialNumber",
            "errorCode",
            "isInErrorState",
            "isInWarningState",
            "isInCautionState",
            "isFirmwareUpdateSupported",
            "firmwareUpdateStatus",
        ):
            characteristic = self.characteristic(name)
            if characteristic is not None:
                result[name] = characteristic
        return result

    @property
    def model(self) -> str | None:
        """Return the management point's model identifier, when reported."""
        return self.model_info.value if self.model_info is not None else None

    @property
    def serial(self) -> str | None:
        """Return the management point's serial number, when reported."""
        return self.serial_number.value if self.serial_number is not None else None

    @property
    def version(self) -> str | None:
        """Return the best available software version for the management point."""
        for characteristic in (
            self.software_version,
            self.firmware_version,
            self.eeprom_version,
        ):
            if characteristic is not None and characteristic.value:
                return characteristic.value
        return None

    @property
    def climate_control(self) -> ClimateControl | None:
        """Return the typed climate-control view for this management point."""
        if self.management_point_type != "climateControl":
            return None
        return ClimateControl(self)

    @property
    def domestic_hot_water(self) -> DomesticHotWater | None:
        """Return the typed domestic-hot-water view for this management point."""
        if self.management_point_type not in {
            "domesticHotWaterTank",
            "domesticHotWaterFlowThrough",
        }:
            return None
        return DomesticHotWater(self)

    @property
    def schedule_state(self) -> ScheduleState | None:
        """Return the typed schedule state when the point exposes schedules."""
        return ScheduleState(self) if self.schedule is not None else None

    @property
    def firmware(self) -> Firmware | None:
        """Return typed firmware state when the point exposes firmware data."""
        if not any(
            (
                self.firmware_version,
                self.software_version,
                self.is_firmware_update_supported,
                self.firmware_update,
                self.firmware_update_status,
            )
        ):
            return None
        return Firmware(self)


@dataclass(frozen=True, slots=True)
class ClimateControl:
    """Read typed climate-control state from a management point.

    This view exposes Daikin's native capabilities. Consumers remain
    responsible for mapping those values to their own domain models.
    """

    management_point: ManagementPoint

    @property
    def operation_mode(self) -> Characteristic[str] | None:
        """Return the native operation-mode characteristic."""
        return self.management_point.operation_mode

    @property
    def on_off_mode(self) -> Characteristic[str] | None:
        """Return the power characteristic."""
        return self.management_point.on_off_mode

    @property
    def native_operation_mode(self) -> str | None:
        """Return the current native operation mode."""
        operation_mode = self.operation_mode
        return operation_mode.value if operation_mode is not None else None

    @property
    def native_operation_modes(self) -> list[str]:
        """Return all advertised native operation modes, including the current mode."""
        operation_mode = self.operation_mode
        if operation_mode is None:
            return []
        modes = list(operation_mode.values or [])
        if operation_mode.value not in modes:
            modes.append(operation_mode.value)
        return modes

    def setpoint(self, target: str, operation_mode: str | None = None) -> Setpoint | None:
        """Return a temperature target for a native operation mode."""
        temperature_control = self.management_point.temperature_control
        if temperature_control is None:
            return None
        mode = operation_mode or self.native_operation_mode
        if mode is None:
            return None
        mode_setpoints = temperature_control.value.operation_modes.get(mode)
        if mode_setpoints is None:
            return None
        return mode_setpoints.setpoints.get(target)

    @property
    def setpoint_types(self) -> list[str]:
        """Return the distinct target names advertised across operation modes."""
        temperature_control = self.management_point.temperature_control
        if temperature_control is None:
            return []
        return list(
            dict.fromkeys(
                target for mode in temperature_control.value.operation_modes.values() for target in mode.setpoints
            )
        )

    def sensory_data(self, target: str) -> Characteristic[int | float] | None:
        """Return a sensory characteristic by its native target name."""
        sensory_data = self.management_point.sensory_data
        if sensory_data is None:
            return None
        attributes = {
            "roomTemperature": "room_temperature",
            "outdoorTemperature": "outdoor_temperature",
            "leavingWaterTemperature": "leaving_water_temperature",
            "tankTemperature": "tank_temperature",
            "roomHumidity": "room_humidity",
            "pm1Concentration": "pm1_concentration",
            "pm25Concentration": "pm25_concentration",
            "pm10Concentration": "pm10_concentration",
        }
        attribute = attributes.get(target)
        return getattr(sensory_data.value, attribute) if attribute is not None else None

    def current_temperature(self, target: str) -> int | float | None:
        """Return the sensed temperature corresponding to a target.

        ONECTA reports the current leaving-water temperature for the
        ``leavingWaterOffset`` target rather than a separate offset sensor.
        """
        sensory_data = self.sensory_data(target)
        if sensory_data is None and target == "leavingWaterOffset":
            sensory_data = self.sensory_data("leavingWaterTemperature")
        return sensory_data.value if sensory_data is not None else None

    def fan_operation(self, operation_mode: str | None = None) -> FanOperationMode | None:
        """Return fan controls for a native operation mode."""
        fan_control = self.management_point.fan_control
        mode = operation_mode or self.native_operation_mode
        if fan_control is None or mode is None:
            return None
        return (fan_control.value.operation_modes or {}).get(mode)

    def preset(self, name: str) -> Characteristic[Any] | None:
        """Return a native preset characteristic by its API name."""
        if name == "holidayMode":
            return self.management_point.holiday_mode
        return self.management_point.characteristic(name)


@dataclass(frozen=True, slots=True)
class DomesticHotWater:
    """Read typed domestic-hot-water state from a management point."""

    management_point: ManagementPoint

    @property
    def power(self) -> Characteristic[str] | None:
        """Return the on/off characteristic."""
        return self.management_point.on_off_mode

    @property
    def powerful_mode(self) -> Characteristic[Any] | None:
        """Return the optional powerful-mode characteristic."""
        return self.management_point.characteristic("powerfulMode")

    @property
    def temperature(self) -> Setpoint | None:
        """Return the domestic-hot-water heating target."""
        control = self.management_point.temperature_control
        if control is None:
            return None
        heating = control.value.operation_modes.get("heating")
        return heating.setpoints.get("domesticHotWaterTemperature") if heating is not None else None

    @property
    def current_temperature(self) -> int | float | None:
        """Return the tank temperature when it is reported."""
        sensory = self.management_point.sensory_data
        tank = sensory.value.tank_temperature if sensory is not None else None
        return tank.value if tank is not None else None


@dataclass(frozen=True, slots=True)
class ScheduleState:
    """Read typed schedule state from a management point."""

    management_point: ManagementPoint

    @property
    def selections(self) -> list[ScheduleSelection]:
        """Return all configured schedule selections."""
        schedule = self.management_point.schedule
        return schedule.value.selections if schedule is not None else []

    @property
    def active_selection(self) -> ScheduleSelection | None:
        """Return the selection for the active schedule mode."""
        schedule = self.management_point.schedule
        if schedule is None or schedule.value.current_mode is None:
            return None
        mode = schedule.value.current_mode.value
        return next((item for item in self.selections if item.mode == mode), None)


@dataclass(frozen=True, slots=True)
class Firmware:
    """Read typed firmware-update state from a management point."""

    management_point: ManagementPoint

    @property
    def installed_version(self) -> str | None:
        """Return the installed firmware or software version."""
        installed = self.management_point.firmware_version or self.management_point.software_version
        return installed.value if installed is not None else None

    @property
    def update_supported(self) -> bool:
        """Return whether the cloud allows firmware installation."""
        supported = self.management_point.is_firmware_update_supported
        return bool(supported.value) if supported is not None else False

    @property
    def offered_update(self) -> dict[str, Any] | None:
        """Return the optional offered firmware metadata."""
        update = self.management_point.firmware_update
        return update.value if update is not None else None

    @property
    def firmware_id(self) -> str | None:
        """Return the install target ID for the offered update."""
        update = self.offered_update
        firmware_id = update.get("id") if update is not None else None
        return firmware_id if isinstance(firmware_id, str) else None

    @property
    def in_progress(self) -> bool:
        """Return whether a firmware installation is in progress."""
        status = self.management_point.firmware_update_status
        return status is not None and status.value == "in-progress"


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

    def management_point(self, embedded_id: str) -> ManagementPoint | None:
        """Return a management point by its embedded ID."""
        return next((point for point in self.management_points if point.embedded_id == embedded_id), None)

    def management_points_by_type(self, management_point_type: str) -> list[ManagementPoint]:
        """Return all management points of a type."""
        return [point for point in self.management_points if point.management_point_type == management_point_type]

    def management_point_by_type(self, management_point_type: str) -> ManagementPoint | None:
        """Return the first management point of a type."""
        return next(iter(self.management_points_by_type(management_point_type)), None)

    @property
    def gateway_management_point(self) -> ManagementPoint | None:
        """Return the gateway management point, when provided by the cloud."""
        return self.management_point_by_type("gateway")

    @property
    def gateway_embedded_id(self) -> str | None:
        """Return the embedded ID used to address the gateway management point."""
        gateway = self.gateway_management_point
        return gateway.embedded_id if gateway is not None else None

    @property
    def display_name(self) -> str:
        """Return the cloud-provided climate name or the gateway model name."""
        for point in self.management_points_by_type("climateControl"):
            if point.name is not None and point.name.value:
                return point.name.value
        return self.device_model

    @property
    def mac_address(self) -> str | None:
        """Return the gateway MAC address, when provided by the cloud."""
        gateway = self.gateway_management_point
        mac_address = gateway.characteristic("macAddress") if gateway is not None else None
        return mac_address.value if mac_address is not None else None

    @property
    def available(self) -> bool:
        """Return whether the gateway is connected to the Daikin cloud."""
        return self.cloud_connection.value
