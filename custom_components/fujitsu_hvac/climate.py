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
        self._attr_target_temperature = self.coordinator.data[self.idx].temp
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
        return [HVACMode.OFF, HVACMode.COOL, HVACMode.DRY, HVACMode.HEAT]

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        if self.coordinator.data[self.idx].powered:
            if self.coordinator.data[self.idx].mode == Mode.COOL:
                return HVACMode.COOL
            elif self.coordinator.data[self.idx].mode == Mode.HEAT:
                return HVACMode.HEAT
            elif self.coordinator.data[self.idx].mode == Mode.DRY:
                return HVACMode.DRY
            else:
                return None
        else:
            return HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.client.set_settings(
                self.coordinator.data[self.idx].circuit,
                self.coordinator.data[self.idx].sub_id,
                change_power_status=True,
                power_status=False,
                mode=self.coordinator.data[self.idx].mode,
                fan_speed=self.coordinator.data[self.idx].fan_speed,
                temp=self.coordinator.data[self.idx].temp,
            )
        if hvac_mode == HVACMode.COOL:
            await self.coordinator.client.set_settings(
                self.coordinator.data[self.idx].circuit,
                self.coordinator.data[self.idx].sub_id,
                power_status=True,
                mode=Mode.COOL,
                fan_speed=self.coordinator.data[self.idx].fan_speed,
                temp=self.coordinator.data[self.idx].temp,
                change_power_status=True,
                change_mode=True,
            )
        if hvac_mode == HVACMode.HEAT:
            await self.coordinator.client.set_settings(
                self.coordinator.data[self.idx].circuit,
                self.coordinator.data[self.idx].sub_id,
                power_status=True,
                mode=Mode.HEAT,
                fan_speed=self.coordinator.data[self.idx].fan_speed,
                temp=self.coordinator.data[self.idx].temp,
                change_power_status=True,
                change_mode=True,
            )
        if hvac_mode == HVACMode.DRY:
            await self.coordinator.client.set_settings(
                self.coordinator.data[self.idx].circuit,
                self.coordinator.data[self.idx].sub_id,
                power_status=True,
                mode=Mode.DRY,
                fan_speed=self.coordinator.data[self.idx].fan_speed,
                temp=self.coordinator.data[self.idx].temp,
                change_power_status=True,
                change_mode=True,
            )

        self.coordinator.async_update_listeners()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        await self.coordinator.client.set_settings(
            self.coordinator.data[self.idx].circuit,
            self.coordinator.data[self.idx].sub_id,
            power_status=True,
            mode=self.coordinator.data[self.idx].mode,
            fan_speed=self.coordinator.data[self.idx].fan_speed,
            temp=temperature,
            change_temp=True,
        )

        self.coordinator.async_update_listeners()
