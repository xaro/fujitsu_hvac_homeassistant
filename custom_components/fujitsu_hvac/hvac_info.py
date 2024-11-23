"""Model for HVAC data."""

from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any, TypeVar

TMode = TypeVar("TMode", bound="Mode")


class Mode(Enum):
    """Mode of heating/cooling."""

    Cool = "Cool"
    Dry = "Dry"
    Heat = "Heat"
    Off = "Off"


class FanSpeed(StrEnum):
    """Speed of the fan of an individual unit."""

    Min = "Min"
    Mid = "Mid"
    Max = "Max"
    Auto = "Auto"
    Off = "Off"


@dataclass
class HvacInfo:
    """Value class for information of an individual unit."""

    circuit: int
    sub_id: int
    powered: bool
    mode: Mode
    target_temp: float
    fan_speed: FanSpeed
    louver: int

    @staticmethod
    def from_json(data: dict[str, Any]) -> Any:
        """Create an HvacInfo object from the data coming from the info API."""
        circuit = data["circuit"]
        sub_id = data["sub_id"]
        powered = data["powered"]
        mode = Mode[data["mode"]]
        target_temp = data["target_temp"]
        fan_speed = FanSpeed[data["fan_speed"]]
        louver = data["louver"]

        return HvacInfo(circuit, sub_id, powered, mode, target_temp, fan_speed, louver)
