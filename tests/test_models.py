"""Tests for typed Daikin Onecta models using real API fixtures."""

import json
from pathlib import Path

import pytest
from syrupy import SnapshotAssertion

from daikin_onecta import GatewayDevice

FIXTURES = Path(__file__).parent / "fixtures"


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


@pytest.mark.parametrize("fixture", ["gas.json", "ururu.json"])
def test_complex_device_models(fixture: str, snapshot: SnapshotAssertion) -> None:
    """Deserialize different real-world device families without modeling every characteristic."""
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
