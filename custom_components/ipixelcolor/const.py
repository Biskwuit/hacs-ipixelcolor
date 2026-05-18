"""Constants for the iPixel Color LED Matrix integration."""

DOMAIN = "ipixelcolor"
MANUFACTURER = "iPixel Color"

# Config entry keys
CONF_ADDRESS = "address"
CONF_NAME = "name"

# Default values
DEFAULT_BRIGHTNESS = 50
DEFAULT_ANIMATION = 0
DEFAULT_SPEED = 80
DEFAULT_COLOR = "ffffff"
DEFAULT_FONT = "CUSONG"
DEFAULT_ORIENTATION = 0

# Platforms
PLATFORMS = ["light", "select", "number", "button"]

# Services
SERVICE_SEND_TEXT = "send_text"
SERVICE_SEND_IMAGE = "send_image"
SERVICE_SET_CLOCK = "set_clock"
SERVICE_SET_PIXEL = "set_pixel"

# BLE scan settings
BLE_SCAN_TIMEOUT = 10
BLE_DEVICE_PREFIXES = ["iPixel", "Pixel"]

# Orientations
ORIENTATIONS = {
    "Normal (0°)": 0,
    "90°": 1,
    "180°": 2,
    "270°": 3,
}

# Clock styles
CLOCK_STYLES = {
    "Style 1": 1,
    "Style 2": 2,
    "Style 3": 3,
    "Style 4": 4,
    "Style 5": 5,
}

# Text animations
TEXT_ANIMATIONS = {
    "Static": 0,
    "Scroll left": 1,
    "Scroll right": 2,
    "Scroll up": 3,
    "Scroll down": 4,
}
