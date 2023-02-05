import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

import fujitsu.fujitsu as lib


class FujitsuCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Fujitsu data"""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        client: lib.FujitsuHvac,
        name: str,
        update_interval: timedelta,
    ):
        self.client = client

        super().__init__(hass, logger, name=name, update_interval=update_interval)

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        await self.client.login()
        results = await self.client.get_all_info()
        await self.client.logout()

        return results
