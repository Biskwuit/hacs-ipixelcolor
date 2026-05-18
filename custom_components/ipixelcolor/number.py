"""Number platform for iPixel Color LED Matrix."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up number entities."""
    coordinator: IPixelColorCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([IPixelColorBrightnessNumber(coordinator, config_entry)])


class IPixelColorBrightnessNumber(CoordinatorEntity, NumberEntity):
    """Number entity for device brightness (0-100)."""

    _attr_has_entity_name = True
    _attr_name = "Brightness"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:brightness-6"
    _attr_native_unit_of_measurement = "%"

    def __init__(
        self,
        coordinator: IPixelColorCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the brightness number."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._attr_unique_id = f"{config_entry.entry_id}_brightness"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=coordinator.device_name,
            manufacturer=MANUFACTURER,
        )

    @property
    def native_value(self) -> float:
        """Return the current brightness level."""
        return float(self._coordinator.brightness)

    @property
    def available(self) -> bool:
        return self._coordinator.is_connected

    async def async_set_native_value(self, value: float) -> None:
        """Set the brightness level."""
        await self._coordinator.async_set_brightness(int(value))

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
