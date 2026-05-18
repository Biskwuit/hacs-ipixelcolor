"""Config flow for iPixel Color LED Matrix integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.data_entry_flow import FlowResult

from .const import BLE_DEVICE_PREFIXES, BLE_SCAN_TIMEOUT, CONF_ADDRESS, CONF_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS): str,
        vol.Optional(CONF_NAME, default="iPixel Color"): str,
    }
)


def _is_ipixel_device(name: str | None) -> bool:
    """Check if a BLE device name matches known iPixel patterns."""
    if not name:
        return False
    return any(name.startswith(prefix) for prefix in BLE_DEVICE_PREFIXES)


class IPixelColorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iPixel Color LED Matrix."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, str] = {}  # address -> name
        self._discovery_info: BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle a Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        name = discovery_info.name or "iPixel Color"
        self._discovery_info = discovery_info

        self.context["title_placeholders"] = {
            "name": name,
            "address": discovery_info.address,
        }

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm Bluetooth discovery."""
        assert self._discovery_info is not None
        info = self._discovery_info

        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, info.name or "iPixel Color"),
                data={
                    CONF_ADDRESS: info.address,
                    CONF_NAME: user_input.get(CONF_NAME, info.name or "iPixel Color"),
                },
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": info.name or "iPixel Color",
                "address": info.address,
            },
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME, default=info.name or "iPixel Color"
                    ): str,
                }
            ),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step — scan and list devices or enter manually."""
        errors: dict[str, str] = {}

        # Scan for devices
        await self._async_scan_devices()

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            name = user_input.get(CONF_NAME) or self._discovered_devices.get(address, "iPixel Color")

            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=name,
                data={CONF_ADDRESS: address, CONF_NAME: name},
            )

        # Build options list for the dropdown
        if self._discovered_devices:
            device_options = {
                addr: f"{dname} ({addr})"
                for addr, dname in self._discovered_devices.items()
            }
            schema = vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(device_options),
                    vol.Optional(CONF_NAME, default="iPixel Color"): str,
                }
            )
            return self.async_show_form(
                step_id="user",
                data_schema=schema,
                description_placeholders={
                    "device_count": str(len(self._discovered_devices))
                },
                errors=errors,
            )

        # No devices found — fall back to manual entry
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            description_placeholders={"device_count": "0"},
            errors={"base": "no_devices_found"} if not user_input else errors,
        )

    async def _async_scan_devices(self) -> None:
        """Scan for BLE devices and filter iPixel candidates."""
        self._discovered_devices = {}

        # First try HA's built-in Bluetooth service info (no extra scan needed)
        try:
            discovered = async_discovered_service_info(self.hass, connectable=True)
            for info in discovered:
                if _is_ipixel_device(info.name):
                    self._discovered_devices[info.address] = info.name or "iPixel Color"
        except Exception:
            pass  # Not available in all HA versions

        # If nothing found via HA bluetooth, do a raw BleakScanner scan
        if not self._discovered_devices:
            try:
                devices: list[BLEDevice] = await BleakScanner.discover(
                    timeout=BLE_SCAN_TIMEOUT
                )
                for device in devices:
                    if _is_ipixel_device(device.name):
                        self._discovered_devices[device.address] = (
                            device.name or "iPixel Color"
                        )
            except Exception as ex:
                _LOGGER.warning("BLE scan failed: %s", ex)
