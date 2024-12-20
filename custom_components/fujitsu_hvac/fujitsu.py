"""Client for communicating with Fujitsu API."""

import json
import logging
from urllib.parse import urljoin

import aiohttp

from .hvac_info import HvacInfo, Mode

_LOGGER: logging.Logger = logging.getLogger(__package__)


class FujitsuHvac:
    """Client for the Fujitsu HVAC API."""

    def __init__(self, base_url: str) -> None:
        """Initialize."""
        self.base_url = base_url

    async def get_all_info(self, session: aiohttp.ClientSession) -> list[HvacInfo]:
        """Return the info of all devices from the API."""
        _LOGGER.info("Fujitsu: Gathering all data")

        async with session.get(self.url("data")) as response:
            body = await response.text()
            data = json.loads(body)

            _LOGGER.info("Fujitsu data gathered successfully")

            return [HvacInfo.from_json(x) for x in data]

    async def set_mode(
        self, session: aiohttp.ClientSession, circuit: int, sub_id: int, mode: Mode
    ) -> None:
        """Call the API to set a mode."""
        _LOGGER.info("Starting set_mode")

        async with session.post(
            self.url("set_mode"),
            json={"circuit": circuit, "sub_id": sub_id, "mode": mode},
        ) as response:
            response_body = await response.text()
            _LOGGER.info("Received response %s", response_body)

    async def set_temperature(
        self, session: aiohttp.ClientSession, circuit: int, sub_id: int, temp: float
    ) -> None:
        """Call the API to set a temperature."""
        _LOGGER.info("Starting set_temp")

        async with session.post(
            self.url("set_temperature"),
            json={"circuit": circuit, "sub_id": sub_id, "new_temp_c": temp},
        ) as response:
            response_body = await response.text()
            _LOGGER.info("Received response %s", response_body)

    def url(self, path: str) -> str:
        """Return the concatenated absolute URL."""
        return urljoin(self.base_url, path)
