"""Light platform for iPixel Color LED Matrix."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import IPixelColorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up iPixel Color light from a config entry."""
    coordinator: IPixelColorCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([IPixelColorLight(coordinator, config_entry)])


class IPixelColorLight(CoordinatorEntity, LightEntity):
    """Represents the iPixel Color LED matrix as a light entity."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_supported_features = LightEntityFeature(0)
    _attr_has_entity_name = True
    _attr_name = None  # Use device name as entity name

    def __init__(
        self,
        coordinator: IPixelColorCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the light entity."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._attr_unique_id = f"{config_entry.entry_id}_light"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=coordinator.device_name,
            manufacturer=MANUFACTURER,
            model=coordinator.device_info_data.get("model", "iPixel Color LED Matrix"),
            sw_version=coordinator.device_info_data.get("firmware"),
            connections={("bluetooth", coordinator.address)},
        )

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        return self._coordinator.power

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        # pypixelcolor uses 0-100, HA uses 0-255
        return round(self._coordinator.brightness * 255 / 100)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.is_connected

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        if ATTR_BRIGHTNESS in kwargs:
            # Convert HA 0-255 to pypixelcolor 0-100
            level = round(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            await self._coordinator.async_set_brightness(level)

        if not self._coordinator.power:
            await self._coordinator.async_set_power(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._coordinator.async_set_power(False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
