"""iPixel Color LED Matrix integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import entity_registry as er
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

# ---------------------------------------------------------------------------
# Service schemas — entity_id is the light entity of the target device
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coordinator_for_entity(
    hass: HomeAssistant, entity_id: str
) -> IPixelColorCoordinator:
    """
    Resolve an entity_id to its IPixelColorCoordinator.

    Works by looking up the entity in the entity registry to find its
    config_entry_id, then fetching the coordinator from hass.data.

    Raises ServiceValidationError if the entity or coordinator can't be found.
    """
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(entity_id)

    if entry is None:
        raise ServiceValidationError(
            f"Entity '{entity_id}' not found in the entity registry."
        )

    config_entry_id = entry.config_entry_id
    if config_entry_id is None:
        raise ServiceValidationError(
            f"Entity '{entity_id}' is not associated with a config entry."
        )

    coordinator: IPixelColorCoordinator | None = (
        hass.data.get(DOMAIN, {}).get(config_entry_id)
    )
    if coordinator is None:
        raise ServiceValidationError(
            f"No active iPixel Color coordinator found for entity '{entity_id}'. "
            "Is the device configured and connected?"
        )

    return coordinator


# ---------------------------------------------------------------------------
# Setup / teardown
# ---------------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iPixel Color from a config entry."""
    address = entry.data[CONF_ADDRESS]

    coordinator = IPixelColorCoordinator(hass, entry)

    try:
        await coordinator.async_connect()
    except Exception as ex:
        raise ConfigEntryNotReady(
            f"Cannot connect to iPixel Color device at {address}: {ex}"
        ) from ex

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register domain-level services only once (first entry wins)
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_TEXT):
        _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: IPixelColorCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()

    # Remove services when no more entries are loaded
    if not hass.data.get(DOMAIN):
        for svc in (SERVICE_SEND_TEXT, SERVICE_SEND_IMAGE, SERVICE_SET_CLOCK, SERVICE_SET_PIXEL):
            hass.services.async_remove(DOMAIN, svc)

    return unload_ok


# ---------------------------------------------------------------------------
# Service handlers
# ---------------------------------------------------------------------------

def _register_services(hass: HomeAssistant) -> None:
    """Register all iPixel Color services."""

    async def handle_send_text(call: ServiceCall) -> None:
        coord = _coordinator_for_entity(hass, call.data["entity_id"])
        await coord.async_send_text(
            text=call.data["text"],
            animation=call.data["animation"],
            speed=call.data["speed"],
            color=call.data["color"],
            font=call.data["font"],
            rainbow_mode=call.data["rainbow_mode"],
            save_slot=call.data["save_slot"],
        )

    async def handle_send_image(call: ServiceCall) -> None:
        coord = _coordinator_for_entity(hass, call.data["entity_id"])
        await coord.async_send_image(
            path=call.data["path"],
            save_slot=call.data["save_slot"],
        )

    async def handle_set_clock(call: ServiceCall) -> None:
        coord = _coordinator_for_entity(hass, call.data["entity_id"])
        await coord.async_set_clock(
            style=call.data["style"],
            show_date=call.data["show_date"],
            format_24=call.data["format_24"],
        )

    async def handle_set_pixel(call: ServiceCall) -> None:
        coord = _coordinator_for_entity(hass, call.data["entity_id"])
        await coord.async_set_pixel(
            x=call.data["x"],
            y=call.data["y"],
            color=call.data["color"],
        )

    hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT, handle_send_text, schema=SEND_TEXT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_IMAGE, handle_send_image, schema=SEND_IMAGE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_CLOCK, handle_set_clock, schema=SET_CLOCK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_PIXEL, handle_set_pixel, schema=SET_PIXEL_SCHEMA)
