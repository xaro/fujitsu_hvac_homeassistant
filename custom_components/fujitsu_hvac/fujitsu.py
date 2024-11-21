"""Client for communicating with Fujitsu API"""
from urllib.parse import urljoin, urlparse
import datetime
import aiohttp
from .hvac_info import HvacInfo, Mode, FanSpeed
import logging
import json

_LOGGER: logging.Logger = logging.getLogger(__package__)


class FujitsuHvac:
    """Client for the Fujitsu HVAC API"""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    async def get_all_info(self, session: aiohttp.ClientSession):
        """Returns the info of all devices from the API"""
        _LOGGER.info("Fujitsu: Gathering all data")

        async with client.get(self.url("data")) as response:
            body = await response.text()
            data = json.loads(body)

            _LOGGER.info("Fujitsu data gathered successfully")

            infos = []
            for info in data:
                infos.append(HvacInfo.from_json(info))
            return infos

    async def set_mode(self, session: aiohttp.ClientSession, circuit: int, sub_id: int, mode: Mode):
        _LOGGER.info("Starting set_mode")

        async with client.post(self.url("set_mode"), json={
            "circuit": circuit,
	        "sub_id": sub_id,
	        "mode": mode.value
        }) as response:
            response_body = await response.text()
            _LOGGER.info("Received response " + response_body)
    
    async def set_temp(self, session: aiohttp.ClientSession, circuit: int, sub_id: int, temp: float):
        _LOGGER.info("Starting set_temp")

        async with client.post(self.url("set_temperature"), json={
            "circuit": circuit,
	        "sub_id": sub_id,
	        "new_temp_c": temp
        }) as response:
            response_body = await response.text()
            _LOGGER.info("Received response " + response_body)
    
    def url(self, path: str) -> str:
        """Returns the concatenated absolute URL"""
        return urljoin(self.base_url, path)