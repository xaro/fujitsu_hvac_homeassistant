"""Climate entity definition for Fujitsu HVAC."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    PRESET_NONE,
    PRESET_SLEEP,
    SWING_OFF,
    SWING_ON,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    TEMP_CELSIUS,
)
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import FujitsuCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Add entities for passed config_entry in HA."""
    coordinator: FujitsuCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        FujitsuEntity(coordinator, idx) for idx, _ in enumerate(coordinator.data)
    )


class FujitsuEntity(CoordinatorEntity[FujitsuCoordinator], ClimateEntity):
    """Fujitsu HVAC Unit controls."""

    def __init__(self, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        self._attr_unique_id = self.coordinator.data[self.idx].get_id()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_current_temperature = self.coordinator.data[self.idx].temp
        self.async_write_ha_state()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        features: int = 0

        features |= ClimateEntityFeature.TARGET_TEMPERATURE

        return features

    @property
    def icon(self) -> str | None:
        return "mdi:hvac"

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_HALVES

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        return [HVACMode.COOL, HVACMode.DRY, HVACMode.HEAT]

    @property
    def hvac_mode(self) -> HVACMode | str | None:
        """Return hvac operation ie. heat, cool mode."""
        return HVACMode.HEAT
