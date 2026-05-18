"""Select platform for iPixel Color LED Matrix."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, ORIENTATIONS
from .coordinator import IPixelColorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    coordinator: IPixelColorCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([IPixelColorOrientationSelect(coordinator, config_entry)])


class IPixelColorOrientationSelect(CoordinatorEntity, SelectEntity):
    """Select entity for device orientation."""

    _attr_has_entity_name = True
    _attr_name = "Orientation"
    _attr_options = list(ORIENTATIONS.keys())

    def __init__(
        self,
        coordinator: IPixelColorCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._attr_unique_id = f"{config_entry.entry_id}_orientation"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=coordinator.device_name,
            manufacturer=MANUFACTURER,
        )
        # Reverse map: int -> label
        self._reverse_map = {v: k for k, v in ORIENTATIONS.items()}

    @property
    def current_option(self) -> str:
        """Return the current orientation label."""
        return self._reverse_map.get(self._coordinator.orientation, "Normal (0°)")

    @property
    def available(self) -> bool:
        return self._coordinator.is_connected

    async def async_select_option(self, option: str) -> None:
        """Change the orientation."""
        orientation_value = ORIENTATIONS.get(option, 0)
        await self._coordinator.async_set_orientation(orientation_value)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
