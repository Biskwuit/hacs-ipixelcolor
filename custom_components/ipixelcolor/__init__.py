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
    SERVICE_SEND_MEDIA_COVER,
    SERVICE_SEND_TEXT,
    SERVICE_SEND_TEXT_ADVANCED,
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

SEND_MEDIA_COVER_SCHEMA = vol.Schema(
    {
        vol.Required("ipixel_entity_id"): cv.entity_id,
        vol.Required("media_player_entity_id"): cv.entity_id,
        vol.Optional("save_slot", default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=9)
        ),
    }
)

SEND_TEXT_ADVANCED_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("text"): cv.string,
        vol.Optional("x", default=0): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional("y", default=0): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional("max_width", default=4): vol.All(vol.Coerce(int), vol.Range(min=1, max=32)),
        vol.Optional("max_height", default=7): vol.All(vol.Coerce(int), vol.Range(min=1, max=32)),
        vol.Optional("text_color", default="ffffff"): cv.string,
        vol.Optional("bg_color", default="000000"): cv.string,
        vol.Optional("font_size"): vol.All(vol.Coerce(int), vol.Range(min=5, max=64)),
        vol.Optional("matrix_width", default=32): vol.All(vol.Coerce(int), vol.Range(min=8)),
        vol.Optional("matrix_height", default=32): vol.All(vol.Coerce(int), vol.Range(min=8)),
        vol.Optional("save_slot", default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=9)
        ),
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


async def _fetch_and_save_media_cover(
    hass: HomeAssistant, media_player_entity_id: str
) -> str:
    """
    Fetch the cover art from a media player and save it locally.
    
    Returns the path to the saved file on disk.
    Raises ServiceValidationError if cover can't be found or downloaded.
    """
    import asyncio
    import aiohttp
    import tempfile
    from pathlib import Path
    
    state = hass.states.get(media_player_entity_id)
    if state is None:
        raise ServiceValidationError(
            f"Media player entity '{media_player_entity_id}' not found."
        )

    entity_picture = state.attributes.get("entity_picture")
    if not entity_picture:
        raise ServiceValidationError(
            f"No cover art found for '{media_player_entity_id}'. "
            "Is music currently playing?"
        )

    # Build absolute URL if it's a relative path
    if entity_picture.startswith("/"):
        # Get HA's configured external URL or fallback to localhost
        base_url = hass.config.external_url or "http://localhost:8123"
        cover_url = f"{base_url}{entity_picture}"
    else:
        cover_url = entity_picture

    # Download the cover image
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(cover_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    raise ServiceValidationError(
                        f"Failed to download cover (HTTP {resp.status})"
                    )
                image_data = await resp.read()
    except aiohttp.ClientError as ex:
        raise ServiceValidationError(f"Failed to download cover: {ex}")

    # Save to a temporary file in the config directory
    config_dir = Path(hass.config.config_dir)
    cache_dir = config_dir / ".ipixelcolor_covers"
    cache_dir.mkdir(exist_ok=True)

    # Use title or timestamp as filename
    title = state.attributes.get("media_title", "unknown")
    filename = f"{title.replace(' ', '_')[:50]}.jpg"
    filepath = cache_dir / filename

    filepath.write_bytes(image_data)
    _LOGGER.info(f"Saved media cover to {filepath}")

    return str(filepath)


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
        for svc in (SERVICE_SEND_TEXT, SERVICE_SEND_TEXT_ADVANCED, SERVICE_SEND_IMAGE, SERVICE_SEND_MEDIA_COVER, SERVICE_SET_CLOCK, SERVICE_SET_PIXEL):
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

    async def handle_send_media_cover(call: ServiceCall) -> None:
        ipixel_entity = call.data["ipixel_entity_id"]
        media_player_entity = call.data["media_player_entity_id"]
        save_slot = call.data["save_slot"]
        
        # Fetch and download the cover from Music Assistant
        cover_path = await _fetch_and_save_media_cover(hass, media_player_entity)
        
        # Send the cover to the iPixel device
        coord = _coordinator_for_entity(hass, ipixel_entity)
        await coord.async_send_image(path=cover_path, save_slot=save_slot)
        
        _LOGGER.info(f"Sent media cover to {ipixel_entity}")

    async def handle_send_text_advanced(call: ServiceCall) -> None:
        from .text_renderer import render_text_advanced
        
        entity_id = call.data["entity_id"]
        text = call.data["text"]
        x = call.data.get("x", 0)
        y = call.data.get("y", 0)
        max_width = call.data.get("max_width", 4)
        max_height = call.data.get("max_height", 7)
        text_color = call.data.get("text_color", "ffffff")
        bg_color = call.data.get("bg_color", "000000")
        font_size = call.data.get("font_size")
        matrix_width = call.data.get("matrix_width", 32)
        matrix_height = call.data.get("matrix_height", 32)
        
        # Render text to pixel data
        pixel_data = render_text_advanced(
            text=text,
            x=x,
            y=y,
            max_width=max_width,
            max_height=max_height,
            text_color=text_color,
            bg_color=bg_color,
            font_size=font_size,
            matrix_width=matrix_width,
            matrix_height=matrix_height,
        )
        
        coord = _coordinator_for_entity(hass, entity_id)
        
        # Set background color first
        bg_hex = pixel_data["bg_color"]
        for py in range(matrix_height):
            for px in range(matrix_width):
                await coord.async_set_pixel(px, py, bg_hex)
        
        # Set text pixels
        for px, py, color_hex in pixel_data["pixels"]:
            await coord.async_set_pixel(px, py, color_hex)
        
        _LOGGER.info(f"Sent advanced text to {entity_id}: '{text}'")

    hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT, handle_send_text, schema=SEND_TEXT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_TEXT_ADVANCED, handle_send_text_advanced, schema=SEND_TEXT_ADVANCED_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_IMAGE, handle_send_image, schema=SEND_IMAGE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_MEDIA_COVER, handle_send_media_cover, schema=SEND_MEDIA_COVER_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_CLOCK, handle_set_clock, schema=SET_CLOCK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_PIXEL, handle_set_pixel, schema=SET_PIXEL_SCHEMA)
