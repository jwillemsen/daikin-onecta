"""Tests for typed Daikin Onecta models using real API fixtures."""

import json
from pathlib import Path

import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from daikin_onecta import GatewayDevice
from daikin_onecta.models import (
    Characteristic,
    ClimateControl,
    DomesticHotWater,
    EnergyData,
    Firmware,
    ManagementPoint,
    Schedule,
    ScheduleOption,
    ScheduleSelection,
    ScheduleState,
    TemperatureControl,
)

FIXTURES = Path(__file__).parent / "fixtures"
DEVICE_FIXTURES = sorted(path.name for path in FIXTURES.glob("*.json"))


def load_devices(name: str) -> list[GatewayDevice]:
    """Load gateway devices from a fixture from the Home Assistant integration."""
    data = json.loads((FIXTURES / name).read_text())
    return [GatewayDevice.from_dict(device) for device in data]


def test_homehub_model(snapshot: SnapshotAssertion) -> None:
    """Deserialize stable HomeHub metadata into typed models."""
    device = load_devices("homehub.json")[0]

    assert {
        "id": device.id,
        "device_model": device.device_model,
        "device_type": device.device_type,
        "available": device.available,
        "embedded_id": device.embedded_id,
        "management_points": [
            {
                "embedded_id": point.embedded_id,
                "type": point.management_point_type,
                "category": point.management_point_category,
                "software_version": point.software_version.value if point.software_version else None,
            }
            for point in device.management_points
        ],
    } == snapshot(extension_class=SingleFileAmberSnapshotExtension)


def test_characteristic_aliases(snapshot: SnapshotAssertion) -> None:
    """Deserialize Daikin camel-case characteristic metadata."""
    characteristic: Characteristic[float] = Characteristic.from_dict(
        {
            "value": 21.5,
            "settable": True,
            "values": [18.0, 21.5, 25.0],
            "minValue": 10,
            "maxValue": 30,
            "stepValue": 0.5,
        }
    )

    assert characteristic.to_dict() == snapshot(extension_class=SingleFileAmberSnapshotExtension)


def test_temperature_control_model(snapshot: SnapshotAssertion) -> None:
    """Deserialize nested temperature-control setpoints into typed models."""
    devices = load_devices("altherma.json")
    climate = next(
        point
        for device in devices
        for point in device.management_points
        if point.management_point_type == "climateControl" and point.temperature_control is not None
    )
    temperature_control = climate.temperature_control
    assert temperature_control is not None

    heating = temperature_control.value.operation_modes["heating"]
    room = heating.setpoints["roomTemperature"]

    assert {
        "value": room.value,
        "settable": room.settable,
        "min_value": room.min_value,
        "max_value": room.max_value,
        "step_value": room.step_value,
        "operation_modes": sorted(temperature_control.value.operation_modes),
    } == snapshot(extension_class=SingleFileAmberSnapshotExtension)


def test_schedule_selections(snapshot: SnapshotAssertion) -> None:
    """Expose only configured schedule selection, not schedule actions."""
    devices = load_devices("altherma.json")
    climate = next(
        point
        for device in devices
        for point in device.management_points
        if point.management_point_type == "climateControl" and point.schedule is not None
    )
    schedule = climate.schedule
    assert schedule is not None

    assert [selection.to_dict() for selection in schedule.value.selections] == snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    )


def test_schedule_selection_current_option() -> None:
    """Return the selected schedule name only when scheduling is enabled."""
    options = [ScheduleOption(id="0", name="Weekday")]
    disabled = ScheduleSelection(
        mode="heating",
        selected="0",
        options=options,
        enabled=False,
        enabled_settable=True,
    )
    enabled = ScheduleSelection(
        mode="heating",
        selected="0",
        options=options,
        enabled=True,
        enabled_settable=True,
    )
    missing = ScheduleSelection(
        mode="heating",
        selected="1",
        options=options,
        enabled=True,
        enabled_settable=True,
    )

    assert disabled.current_option is None
    assert enabled.current_option == "Weekday"
    assert missing.current_option == "1"


def test_schedule_selections_ignore_invalid_data() -> None:
    """Ignore malformed schedule modes and invalid schedule identifiers."""
    schedule = Schedule(
        modes={
            "missing": {},
            "invalid-current": {"currentSchedule": "invalid"},
            "invalid-selected": {"currentSchedule": {"value": 0, "values": ["0"]}},
            "invalid-values": {"currentSchedule": {"value": "0", "values": "invalid"}},
            "valid": {
                "currentSchedule": {"value": "0", "values": ["0", 1]},
                "enabled": {"value": True, "settable": True},
                "schedules": {"0": {"name": {"value": "Weekday"}}},
            },
        }
    )

    selections = schedule.selections

    assert len(selections) == 1
    assert selections[0].mode == "valid"
    assert selections[0].options == [ScheduleOption(id="0", name="Weekday")]


def test_holiday_mode(snapshot: SnapshotAssertion) -> None:
    """Deserialize the small holiday-mode value structure."""
    devices = load_devices("gas.json")
    climate = next(
        point
        for device in devices
        for point in device.management_points
        if point.management_point_type == "climateControl" and point.holiday_mode is not None
    )
    holiday = climate.holiday_mode
    assert holiday is not None

    assert holiday.value.to_dict() == snapshot(extension_class=SingleFileAmberSnapshotExtension)


def test_sensory_data_model(snapshot: SnapshotAssertion) -> None:
    """Deserialize all known sensory data types."""
    device = load_devices("mc80z.json")[0]
    point = next(point for point in device.management_points if point.sensory_data is not None)
    sensory = point.sensory_data
    assert sensory is not None

    assert sensory.value.to_dict() == snapshot(extension_class=SingleFileAmberSnapshotExtension)


def test_fan_control_model(snapshot: SnapshotAssertion) -> None:
    """Deserialize fan speed and direction controls by operation mode."""
    device = load_devices("climate_floorheatingairflow.json")[0]
    point = next(point for point in device.management_points if point.fan_control is not None)
    fan_control = point.fan_control
    assert fan_control is not None
    assert fan_control.value.operation_modes is not None

    heating = fan_control.value.operation_modes["heating"]
    assert heating.fan_speed is not None
    assert heating.fan_direction is not None

    assert {
        "speed_mode": heating.fan_speed.current_mode.value,
        "speed_modes": heating.fan_speed.current_mode.values,
        "fixed_speed": heating.fan_speed.modes["fixed"].value if heating.fan_speed.modes else None,
        "horizontal": (
            heating.fan_direction.horizontal.current_mode.to_dict() if heating.fan_direction.horizontal else None
        ),
        "vertical": (heating.fan_direction.vertical.current_mode.to_dict() if heating.fan_direction.vertical else None),
    } == snapshot(extension_class=SingleFileAmberSnapshotExtension)


def test_climate_control_view() -> None:
    """Expose native climate state without consumers traversing API trees."""
    device = load_devices("climate_floorheatingairflow.json")[0]
    point = next(
        point
        for point in device.management_points
        if point.management_point_type == "climateControl" and point.fan_control is not None
    )

    climate = point.climate_control

    assert isinstance(climate, ClimateControl)
    assert point.operation_mode is not None
    assert climate.management_point is point
    assert climate.operation_mode is point.operation_mode
    assert climate.on_off_mode is point.on_off_mode
    assert climate.native_operation_mode == point.operation_mode.value
    assert climate.native_operation_modes == point.operation_mode.values
    assert climate.setpoint_types == ["roomTemperature"]
    setpoint = climate.setpoint("roomTemperature")
    assert setpoint is not None
    assert setpoint.value == 23.5
    assert climate.setpoint("roomTemperature", "missing") is None
    assert climate.current_temperature("roomTemperature") == 18
    assert climate.current_temperature("leavingWaterOffset") is None
    assert climate.sensory_data("missing") is None
    assert climate.fan_operation() is not None
    assert climate.fan_operation("missing") is None
    assert climate.preset("powerfulMode") is point.characteristic("powerfulMode")
    assert climate.preset("holidayMode") is point.holiday_mode


def test_platform_state_views() -> None:
    """Expose hot-water, schedule, and firmware state without API-tree traversal."""
    points = [point for device in load_devices("altherma_firmwareupdate.json") for point in device.management_points]

    hot_water = next(point.domestic_hot_water for point in points if point.domestic_hot_water)
    assert isinstance(hot_water, DomesticHotWater)
    assert hot_water.temperature is not None
    assert hot_water.current_temperature is not None

    schedule_points = [point for device in load_devices("altherma_schedule.json") for point in device.management_points]
    schedule = next(point.schedule_state for point in schedule_points if point.schedule_state)
    assert isinstance(schedule, ScheduleState)
    assert schedule.active_selection is not None

    firmware = next(point.firmware for point in points if point.firmware)
    assert isinstance(firmware, Firmware)
    assert firmware.installed_version is not None


def test_scalar_and_energy_views() -> None:
    """Expose generic scalar and rolling energy values through typed helpers."""
    point = next(
        point
        for device in load_devices("altherma.json")
        for point in device.management_points
        if point.consumption is not None
    )

    assert point.scalar_characteristic("operationMode") is point.operation_mode
    assert point.scalar_characteristics() == point.simple_characteristics()
    assert isinstance(point.consumption, EnergyData)
    assert point.consumption.values("electrical", "heating", "day") is not None
    assert point.consumption.current_total("electrical", "heating", "day") is not None
    assert point.consumption.current_total("electrical", "heating", "month") is None


def test_climate_control_view_handles_optional_data() -> None:
    """Keep unavailable climate data and non-climate points absent."""
    device = GatewayDevice.from_dict(
        {
            "id": "gateway-1",
            "deviceModel": "Daikin Model",
            "isCloudConnectionUp": {"value": True},
            "managementPoints": [
                {"embeddedId": "gateway", "managementPointType": "gateway"},
                {
                    "embeddedId": "climateControl",
                    "managementPointType": "climateControl",
                    "operationMode": {"value": "cooling"},
                    "temperatureControl": {
                        "value": {
                            "operationModes": {
                                "cooling": {
                                    "setpoints": {
                                        "leavingWaterOffset": {"value": 2},
                                    }
                                }
                            }
                        }
                    },
                    "sensoryData": {
                        "value": {
                            "leavingWaterTemperature": {"value": 31.5},
                        }
                    },
                },
            ],
        }
    )

    assert device.gateway_management_point is not None
    assert device.gateway_management_point.climate_control is None
    climate_point = device.management_point_by_type("climateControl")
    assert climate_point is not None
    climate = climate_point.climate_control
    assert climate is not None
    assert climate.operation_mode is climate_point.operation_mode
    assert climate.on_off_mode is None
    assert climate.native_operation_mode == "cooling"
    assert climate.native_operation_modes == ["cooling"]
    assert climate.setpoint_types == ["leavingWaterOffset"]
    assert climate.setpoint("roomTemperature") is None
    assert climate.setpoint("leavingWaterOffset") is not None
    assert climate.sensory_data("roomTemperature") is None
    assert climate.current_temperature("roomTemperature") is None
    assert climate.current_temperature("leavingWaterOffset") == 31.5
    assert climate.fan_operation() is None
    assert climate.preset("powerfulMode") is None

    empty = ManagementPoint(
        embedded_id="emptyClimateControl",
        management_point_type="climateControl",
    ).climate_control
    assert empty is not None
    assert empty.native_operation_modes == []
    assert empty.setpoint("roomTemperature") is None
    assert empty.setpoint_types == []
    assert empty.sensory_data("roomTemperature") is None

    no_mode = ManagementPoint(
        embedded_id="noModeClimateControl",
        management_point_type="climateControl",
        temperature_control=Characteristic(value=TemperatureControl(operation_modes={})),
    ).climate_control
    assert no_mode is not None
    assert no_mode.setpoint("roomTemperature") is None


def test_consumption_data_model(snapshot: SnapshotAssertion) -> None:
    """Deserialize electrical and gas consumption into normalized series."""
    device = load_devices("gas.json")[0]
    point = next(point for point in device.management_points if point.consumption_data is not None)
    consumption = point.consumption_data
    assert consumption is not None
    assert consumption.value.electrical is not None
    assert consumption.value.gas is not None
    assert consumption.value.electrical.heating is not None
    assert consumption.value.gas.heating is not None

    assert {
        "electrical_unit": consumption.value.electrical.unit,
        "gas_unit": consumption.value.gas.unit,
        "electrical_heating": consumption.value.electrical.heating.to_dict(),
        "gas_heating": consumption.value.gas.heating.to_dict(),
    } == snapshot(extension_class=SingleFileAmberSnapshotExtension)


def test_unmodeled_simple_characteristics(snapshot: SnapshotAssertion) -> None:
    """Keep simple characteristics used for dynamic HA entity discovery."""
    device = load_devices("dx4_firmwareavailable.json")[0]
    gateway = next(point for point in device.management_points if point.management_point_type == "gateway")

    assert {
        name: characteristic.to_dict()
        for name, characteristic in gateway.simple_characteristics().items()
        if name in {"isFirmwareUpdateSupported", "ipAddress", "macAddress", "timeZone"}
    } == snapshot(extension_class=SingleFileAmberSnapshotExtension)


@pytest.mark.parametrize("fixture", DEVICE_FIXTURES)
def test_all_existing_device_fixtures(fixture: str, snapshot: SnapshotAssertion) -> None:
    """Deserialize every existing real-world fixture into the common typed model."""
    devices = load_devices(fixture)

    assert [
        {
            "model": device.device_model,
            "available": device.available,
            "management_points": [
                {
                    "id": point.embedded_id,
                    "type": point.management_point_type,
                    "sub_type": point.management_point_sub_type,
                    "name": point.name.value if point.name else None,
                    "operation_mode": point.operation_mode.value if point.operation_mode else None,
                    "operation_modes": point.operation_mode.values if point.operation_mode else None,
                }
                for point in device.management_points
            ],
        }
        for device in devices
    ] == snapshot(extension_class=SingleFileAmberSnapshotExtension)


def test_management_point_lookup() -> None:
    """Look up management points by embedded ID and type."""
    device = load_devices("altherma.json")[0]

    climate_points = device.management_points_by_type("climateControl")

    assert climate_points
    assert all(point.management_point_type == "climateControl" for point in climate_points)
    assert device.management_point(climate_points[0].embedded_id) is climate_points[0]
    assert device.management_point_by_type("climateControl") is climate_points[0]
    assert device.management_point("missing") is None
    assert device.management_point_by_type("missing") is None
    assert device.management_points_by_type("missing") == []


def test_gateway_derived_metadata() -> None:
    """Expose display and gateway-management-point details from API models."""
    device = load_devices("altherma.json")[0]

    assert device.gateway_management_point is not None
    assert device.gateway_embedded_id == device.gateway_management_point.embedded_id
    mac_address = device.gateway_management_point.characteristic("macAddress")
    assert mac_address is not None
    assert device.mac_address == mac_address.value
    assert device.display_name == next(
        point.name.value
        for point in device.management_points_by_type("climateControl")
        if point.name is not None and point.name.value
    )


def test_management_point_derived_metadata() -> None:
    """Expose API metadata without making consumers inspect envelopes."""
    device = load_devices("altherma_firmwareupdate.json")[0]
    point = device.gateway_management_point

    assert point is not None
    assert point.model_info is not None
    assert point.serial_number is not None
    assert point.model == point.model_info.value
    assert point.serial == point.serial_number.value
    assert point.firmware_version is not None
    assert point.version == point.firmware_version.value


def test_management_point_derived_metadata_is_optional() -> None:
    """Keep absent management-point metadata absent."""
    device = GatewayDevice.from_dict(
        {
            "id": "gateway-1",
            "deviceModel": "Daikin Model",
            "isCloudConnectionUp": {"value": True},
            "managementPoints": [
                {
                    "embeddedId": "gateway",
                    "managementPointType": "gateway",
                }
            ],
        }
    )
    point = device.gateway_management_point

    assert point is not None
    assert point.model is None
    assert point.serial is None
    assert point.version is None


def test_gateway_display_name_falls_back_to_model() -> None:
    """Use the gateway model where the cloud has no named climate point."""
    device = GatewayDevice.from_dict(
        {
            "id": "gateway-1",
            "deviceModel": "Daikin Model",
            "isCloudConnectionUp": {"value": True},
            "managementPoints": [],
        }
    )

    assert device.display_name == "Daikin Model"
