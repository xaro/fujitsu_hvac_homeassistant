"""
Custom integration to integrate Fujitsu HVAC systems with Home Assistant.
"""
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .fujitsu import FujitsuHvac
from .coordinator import FujitsuCoordinator
from .climate import FujitsuEntity
from .const import (
    CONF_URL,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    STARTUP_MESSAGE,
)

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    url = entry.data.get(CONF_URL)
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)

    client = FujitsuHvac(base_url=url, username=username, password=password)
    coordinator = create_coordinator(hass, client)

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setup(entry, "climate")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platform(entry, "climate"):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def create_coordinator(hass: HomeAssistant, client: FujitsuHvac) -> FujitsuCoordinator:
    """Creates a new Fujitsu coordinator"""
    coordinator = FujitsuCoordinator(
        hass, _LOGGER, client, name=DOMAIN, update_interval=SCAN_INTERVAL
    )
    return coordinator
