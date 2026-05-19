"""Coordinator for iPixel Color LED Matrix."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from pypixelcolor import AsyncClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_ADDRESS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class IPixelColorCoordinator(DataUpdateCoordinator):
    """Manages the connection and state of an iPixel Color device."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
        )
        self.config_entry = config_entry
        self.address: str = config_entry.data[CONF_ADDRESS]
        self.device_name: str = config_entry.data.get("name", "iPixel Color")

        self._client: AsyncClient | None = None
        self._connected: bool = False
        self._power: bool = True
        self._brightness: int = 50
        self._orientation: int = 0
        self._device_info_data: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def power(self) -> bool:
        return self._power

    @property
    def brightness(self) -> int:
        return self._brightness

    @property
    def orientation(self) -> int:
        return self._orientation

    @property
    def device_info_data(self) -> dict[str, Any]:
        return self._device_info_data

    async def async_connect(self) -> None:
        """Connect to the BLE device."""
        async with self._lock:
            if self._connected:
                return

            _LOGGER.info("Connecting to iPixel Color at %s", self.address)
            self._client = AsyncClient(self.address)
            await self._client.connect()
            self._connected = True

            # Retrieve device info
            try:
                info = self._client.get_device_info()
                if info:
                    self._device_info_data = {
                        "model": getattr(info, "model", "iPixel Color"),
                        "firmware": getattr(info, "firmware", "Unknown"),
                        "width": getattr(info, "width", 32),
                        "height": getattr(info, "height", 8),
                    }
            except Exception as ex:
                _LOGGER.warning("Could not retrieve device info: %s", ex)

            _LOGGER.info("Connected to iPixel Color at %s", self.address)

    async def async_disconnect(self) -> None:
        """Disconnect from the BLE device."""
        async with self._lock:
            if not self._connected or self._client is None:
                return
            try:
                await self._client.disconnect()
            except Exception as ex:
                _LOGGER.warning("Error disconnecting: %s", ex)
            finally:
                self._connected = False
                self._client = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data - no polling needed for BLE devices."""
        return {
            "power": self._power,
            "brightness": self._brightness,
            "orientation": self._orientation,
            "connected": self._connected,
        }

    async def _execute_with_reconnect(self, coro_func) -> Any:
        """
        Execute a command. If it fails with a connection error,
        reconnect and retry once.
        """
        try:
            async with self._lock:
                return await coro_func()
        except (ConnectionError, BrokenPipeError, OSError, RuntimeError) as ex:
            _LOGGER.warning("Connection error during command: %s. Attempting reconnect...", ex)
            self._connected = False
            self._client = None

            # Try to reconnect
            try:
                await self.async_connect()
                async with self._lock:
                    return await coro_func()
            except Exception as retry_ex:
                _LOGGER.error("Command failed after reconnect: %s", retry_ex)
                raise retry_ex

    async def async_set_power(self, on: bool) -> None:
        """Set device power state."""
        await self._execute_with_reconnect(
            lambda: self._client.set_power(on)
        )
        self._power = on
        self.async_update_listeners()

    async def async_set_brightness(self, level: int) -> None:
        """Set device brightness (0-100)."""
        await self._execute_with_reconnect(
            lambda: self._client.set_brightness(level)
        )
        self._brightness = level
        self.async_update_listeners()

    async def async_set_orientation(self, orientation: int) -> None:
        """Set device orientation (0-3)."""
        await self._execute_with_reconnect(
            lambda: self._client.set_orientation(orientation)
        )
        self._orientation = orientation
        self.async_update_listeners()

    async def async_send_text(
        self,
        text: str,
        animation: int = 0,
        speed: int = 80,
        color: str = "ffffff",
        font: str = "CUSONG",
        rainbow_mode: int = 0,
        save_slot: int = 0,
    ) -> None:
        """Send text to the device."""
        await self._execute_with_reconnect(
            lambda: self._client.send_text(
                text=text,
                animation=animation,
                speed=speed,
                color=color,
                font=font,
                rainbow_mode=rainbow_mode,
                save_slot=save_slot,
            )
        )

    async def async_send_image(self, path: str, save_slot: int = 0) -> None:
        """Send an image or GIF to the device."""
        await self._execute_with_reconnect(
            lambda: self._client.send_image(path=path, save_slot=save_slot)
        )

    async def async_set_clock(
        self,
        style: int = 1,
        show_date: bool = True,
        format_24: bool = True,
    ) -> None:
        """Set clock mode."""
        await self._execute_with_reconnect(
            lambda: self._client.set_clock_mode(
                style=style,
                show_date=show_date,
                format_24=format_24,
            )
        )

    async def async_set_pixel(self, x: int, y: int, color: str) -> None:
        """Set an individual pixel color."""
        await self._execute_with_reconnect(
            lambda: self._client.set_pixel(x=x, y=y, color=color)
        )

    async def async_clear(self) -> None:
        """Clear the device EEPROM."""
        await self._execute_with_reconnect(
            lambda: self._client.clear()
        )
