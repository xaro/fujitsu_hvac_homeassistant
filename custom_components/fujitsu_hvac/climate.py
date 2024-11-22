"""Climate entity definition for Fujitsu HVAC."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_HALVES,
    TEMP_CELSIUS,
)
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coordinator import FujitsuCoordinator
from .fujitsu import Mode, HvacInfo
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Add entities for passed config_entry in HA."""
    coordinator: FujitsuCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    session = async_get_clientsession(hass)

    async_add_entities(
        FujitsuEntity(session, coordinator, idx)
        for idx, _ in enumerate(coordinator.data)
    )


class FujitsuEntity(CoordinatorEntity[FujitsuCoordinator], ClimateEntity):
    """Fujitsu HVAC Unit controls."""

    def __init__(self, session, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.session = session
        self.idx = idx
        self._attr_unique_id = str(self.coordinator.data[self.idx].circuit) + str(self.coordinator.data[self.idx].sub_id)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_current_temperature = self.coordinator.data[self.idx].target_temp
        self._attr_target_temperature = self.coordinator.data[self.idx].target_temp
        self._attr_hvac_mode = hvac_mode
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
        """Temperature of the API is always celsius."""
        return TEMP_CELSIUS

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        return [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.DRY]

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        if self.coordinator.data[self.idx].powered:
            if self.coordinator.data[self.idx].mode == Mode.Cool:
                return HVACMode.COOL
            elif self.coordinator.data[self.idx].mode == Mode.Heat:
                return HVACMode.HEAT
            elif self.coordinator.data[self.idx].mode == Mode.Dry:
                return HVACMode.DRY
            else:
                return None
        else:
            return HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:

        if hvac_mode == HVACMode.OFF:
            self.coordinator.data[self.idx].powered = False

            await self.coordinator.client.set_mode(
                self.session,
                self.coordinator.data[self.idx].circuit,
                self.coordinator.data[self.idx].sub_id,
                mode=Mode.Off
            )
        else:
            if hvac_mode == HVACMode.COOL:
                fujitsu_mode = Mode.Cool
            elif hvac_mode == HVACMode.HEAT:
                fujitsu_mode = Mode.Heat
            elif hvac_mode == HVACMode.DRY:
                fujitsu_mode = Mode.Dry
            else:
                raise Exception("Invalid hvac mode: " + hvac_mode)

            self.coordinator.data[self.idx].power_status = True
            self.coordinator.data[self.idx].mode = fujitsu_mode

            await self.coordinator.client.set_settings(
                self.session,
                self.coordinator.data[self.idx].circuit,
                self.coordinator.data[self.idx].sub_id,
                fujitsu_mode
            )

        self._attr_hvac_mode = hvac_mode

        self.coordinator.async_update_listeners()
        await self.async_update_ha_state(force_refresh=True)

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        await self.coordinator.client.set_temperature(
            self.session,
            self.coordinator.data[self.idx].circuit,
            self.coordinator.data[self.idx].sub_id,
            temperature
        )

        self._attr_target_temperature = temperature

        self.coordinator.async_update_listeners()
        await self.async_update_ha_state(force_refresh=True)
