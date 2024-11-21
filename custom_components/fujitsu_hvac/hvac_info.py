from dataclasses import dataclass
from enum import StrEnum, Enum
from typing import List, TypeVar


TMode = TypeVar("TMode", bound="Mode")


class Mode(StrEnum):
    """Mode of heating/cooling"""

    Cool = auto()
    Dry = auto()
    Heat = auto()


class FanSpeed(StrEnum):
    """Speed of the fan of an individual unit"""

    Min = auto()
    Mid = auto()
    Max = auto()
    Auto = auto()
    Off = auto()


@dataclass
class HvacInfo:
    """Value class for information of an individual unit"""

    circuit: int
    sub_id: int
    powered: bool
    mode: Mode
    target_temp: float
    fan_speed: FanSpeed
    louver: int

    @staticmethod
    def from_json(data: dict):
        """Creates an HvacInfo object from the data coming from the info API"""
        circuit = data["circuit"]
        sub_id = data["sub_id"]
        powered = data["powered"]
        mode = data["mode"]
        target_temp = data["target_temp"]
        fan_speed = data["fan_speed"]
        louver = data["louver"]

        return HvacInfo(circuit, sub_id, powered, mode, temp, fan_speed, louver)
