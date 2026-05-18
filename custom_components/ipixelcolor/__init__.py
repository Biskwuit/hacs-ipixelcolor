"""iPixel Color LED Matrix integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import pypixelcolor
from pypixelcolor import AsyncClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    CONF_ADDRESS,
    DEFAULT_ANIMATION,
    DEFAULT_COLOR,
    DEFAULT_FONT,
    DEFAULT_SPEED,
    DOMAIN,
    PLATFORMS,
    SERVICE_SEND_IMAGE,
    SERVICE_SEND_TEXT,
    SERVICE_SET_CLOCK,
    SERVICE_SET_PIXEL,
)
from .coordinator import IPixelColorCoordinator

_LOGGER = logging.getLogger(__name__)

SEND_TEXT_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("text"): cv.string,
        vol.Optional("animation", default=DEFAULT_ANIMATION): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=4)
        ),
        vol.Optional("speed", default=DEFAULT_SPEED): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional("color", default=DEFAULT_COLOR): cv.string,
        vol.Optional("font", default=DEFAULT_FONT): cv.string,
        vol.Optional("rainbow_mode", default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=1)
        ),
        vol.Optional("save_slot", default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=9)
        ),
    }
)

SEND_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("path"): cv.string,
        vol.Optional("save_slot", default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=9)
        ),
    }
)

SET_CLOCK_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("style", default=1): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=5)
        ),
        vol.Optional("show_date", default=True): cv.boolean,
        vol.Optional("format_24", default=True): cv.boolean,
    }
)

SET_PIXEL_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("x"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required("y"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required("color"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iPixel Color from a config entry."""
    address = entry.data[CONF_ADDRESS]

    coordinator = IPixelColorCoordinator(hass, entry)

    try:
        await coordinator.async_connect()
    except Exception as ex:
        raise ConfigEntryNotReady(f"Cannot connect to device at {address}: {ex}") from ex

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_send_text(call: ServiceCall) -> None:
        """Handle send_text service call."""
        entity_id = call.data["entity_id"]
        coord = _get_coordinator_from_entity(hass, entity_id)
        if coord:
            await coord.async_send_text(
                text=call.data["text"],
                animation=call.data.get("animation", DEFAULT_ANIMATION),
                speed=call.data.get("speed", DEFAULT_SPEED),
                color=call.data.get("color", DEFAULT_COLOR),
                font=call.data.get("font", DEFAULT_FONT),
                rainbow_mode=call.data.get("rainbow_mode", 0),
                save_slot=call.data.get("save_slot", 0),
            )

    async def handle_send_image(call: ServiceCall) -> None:
        """Handle send_image service call."""
        entity_id = call.data["entity_id"]
        coord = _get_coordinator_from_entity(hass, entity_id)
        if coord:
            await coord.async_send_image(
                path=call.data["path"],
                save_slot=call.data.get("save_slot", 0),
            )

    async def handle_set_clock(call: ServiceCall) -> None:
        """Handle set_clock service call."""
        entity_id = call.data["entity_id"]
        coord = _get_coordinator_from_entity(hass, entity_id)
        if coord:
            await coord.async_set_clock(
                style=call.data.get("style", 1),
                show_date=call.data.get("show_date", True),
                format_24=call.data.get("format_24", True),
            )

    async def handle_set_pixel(call: ServiceCall) -> None:
        """Handle set_pixel service call."""
        entity_id = call.data["entity_id"]
        coord = _get_coordinator_from_entity(hass, entity_id)
        if coord:
            await coord.async_set_pixel(
                x=call.data["x"],
                y=call.data["y"],
                color=call.data["color"],
            )

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_TEXT):
        hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT, handle_send_text, schema=SEND_TEXT_SCHEMA)
        hass.services.async_register(DOMAIN, SERVICE_SEND_IMAGE, handle_send_image, schema=SEND_IMAGE_SCHEMA)
        hass.services.async_register(DOMAIN, SERVICE_SET_CLOCK, handle_set_clock, schema=SET_CLOCK_SCHEMA)
        hass.services.async_register(DOMAIN, SERVICE_SET_PIXEL, handle_set_pixel, schema=SET_PIXEL_SCHEMA)

    return True


def _get_coordinator_from_entity(hass: HomeAssistant, entity_id: str) -> IPixelColorCoordinator | None:
    """Find the coordinator associated with an entity."""
    for coord in hass.data.get(DOMAIN, {}).values():
        if isinstance(coord, IPixelColorCoordinator):
            if entity_id.startswith(f"{DOMAIN}.") or any(
                entity_id in str(coord.config_entry.entry_id) for _ in [None]
            ):
                return coord
    # Fallback: return first coordinator
    coords = [v for v in hass.data.get(DOMAIN, {}).values() if isinstance(v, IPixelColorCoordinator)]
    return coords[0] if coords else None


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: IPixelColorCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()

    return unload_ok
