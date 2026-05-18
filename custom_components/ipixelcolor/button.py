"""Button platform for iPixel Color LED Matrix."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER
from .coordinator import IPixelColorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    coordinator: IPixelColorCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            IPixelColorClearButton(coordinator, config_entry),
            IPixelColorClockButton(coordinator, config_entry),
        ]
    )


class IPixelColorClearButton(ButtonEntity):
    """Button to clear the device EEPROM."""

    _attr_has_entity_name = True
    _attr_name = "Clear Display"
    _attr_icon = "mdi:delete-sweep"

    def __init__(
        self,
        coordinator: IPixelColorCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{config_entry.entry_id}_clear"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=coordinator.device_name,
            manufacturer=MANUFACTURER,
        )

    @property
    def available(self) -> bool:
        return self._coordinator.is_connected

    async def async_press(self) -> None:
        """Clear the device EEPROM."""
        await self._coordinator.async_clear()


class IPixelColorClockButton(ButtonEntity):
    """Button to switch the device to clock mode."""

    _attr_has_entity_name = True
    _attr_name = "Show Clock"
    _attr_icon = "mdi:clock-digital"

    def __init__(
        self,
        coordinator: IPixelColorCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{config_entry.entry_id}_clock"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=coordinator.device_name,
            manufacturer=MANUFACTURER,
        )

    @property
    def available(self) -> bool:
        return self._coordinator.is_connected

    async def async_press(self) -> None:
        """Activate clock mode with defaults."""
        await self._coordinator.async_set_clock(style=1, show_date=True, format_24=True)
