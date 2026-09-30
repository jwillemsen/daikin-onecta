"""Tests for typed Daikin Onecta models using real API fixtures."""

import json
from pathlib import Path

import pytest
from syrupy import SnapshotAssertion

from daikin_onecta import GatewayDevice
from daikin_onecta.models import Characteristic

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
    } == snapshot


def test_characteristic_aliases(snapshot: SnapshotAssertion) -> None:
    """Deserialize Daikin camel-case characteristic metadata."""
    characteristic = Characteristic.from_dict(
        {
            "value": 21.5,
            "settable": True,
            "values": [18.0, 21.5, 25.0],
            "minValue": 10,
            "maxValue": 30,
            "stepValue": 0.5,
        }
    )

    assert characteristic.to_dict() == snapshot


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
    } == snapshot


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
    ] == snapshot
