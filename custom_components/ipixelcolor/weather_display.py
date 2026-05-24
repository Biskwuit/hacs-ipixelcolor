"""Generate weather display with temperature and icon for iPixel Color."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import tempfile
from pathlib import Path


def generate_weather_display(
    condition: str,
    temperature: float,
    show_time: bool = False,
    time_str: str = "",
) -> str:
    """
    Generate a compact weather display image for 32x32 LED matrix.
    
    Args:
        condition: Weather condition (sunny, rainy, cloudy, snowy, stormy, etc.)
        temperature: Temperature in Celsius or Fahrenheit
        show_time: Whether to show time
        time_str: Time string to display (HH:MM)
    
    Returns:
        Path to the generated PNG file
    """
    # 32x32 image for the LED matrix
    width, height = 32, 32
    img = Image.new("RGB", (width, height), color="#000000")
    draw = ImageDraw.Draw(img)
    
    # Try to load small fonts
    try:
        # Large font for temperature (16-18px)
        font_temp = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14
        )
        # Small font for time/text (8-10px)
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 7
        )
    except (OSError, IOError):
        # Fallback: use bitmap font
        font_temp = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw small weather icon (12x12) in top-left corner
    _draw_small_weather_icon(draw, condition, x=1, y=2, size=10)
    
    # Draw temperature large (right side)
    # Format: "26°" or "26°\nC" depending on space
    temp_text = f"{int(temperature)}°"
    draw.text((14, 6), temp_text, fill="#ffff00", font=font_temp)
    
    # Draw time or secondary info (bottom)
    if show_time and time_str:
        draw.text((14, 22), time_str, fill="#00ff00", font=font_small)
    else:
        # Draw condition abbreviation (short)
        condition_short = _get_condition_abbreviation(condition)
        draw.text((14, 22), condition_short, fill="#cccccc", font=font_small)
    
    # Save to temp file
    temp_dir = Path(tempfile.gettempdir()) / "ipixelcolor_weather"
    temp_dir.mkdir(exist_ok=True)
    filepath = temp_dir / "weather_display.png"
    img.save(filepath, "PNG")
    
    return str(filepath)


def _get_condition_abbreviation(condition: str) -> str:
    """Get short text for weather condition."""
    condition_lower = condition.lower().strip()
    
    if any(c in condition_lower for c in ["sunny", "clear"]):
        return "SUN"
    elif any(c in condition_lower for c in ["cloud", "overcast"]):
        return "CLO"
    elif any(c in condition_lower for c in ["rain", "pouring"]):
        return "RAN"
    elif any(c in condition_lower for c in ["snow"]):
        return "SNW"
    elif any(c in condition_lower for c in ["thunder", "lightning"]):
        return "STM"
    elif any(c in condition_lower for c in ["fog", "mist"]):
        return "FOG"
    elif any(c in condition_lower for c in ["wind"]):
        return "WND"
    else:
        return "..."


def _draw_small_weather_icon(draw, condition: str, x: int = 1, y: int = 2, size: int = 10) -> None:
    """Draw a small weather icon (10x10 pixels)."""
    condition_lower = condition.lower().strip()
    
    if any(c in condition_lower for c in ["sunny", "clear"]):
        _draw_small_sun(draw, x, y, size)
    elif any(c in condition_lower for c in ["cloud", "overcast"]):
        _draw_small_cloud(draw, x, y, size)
    elif any(c in condition_lower for c in ["rain", "pouring"]):
        _draw_small_rain(draw, x, y, size)
    elif any(c in condition_lower for c in ["snow"]):
        _draw_small_snow(draw, x, y, size)
    elif any(c in condition_lower for c in ["thunder", "lightning"]):
        _draw_small_storm(draw, x, y, size)
    elif any(c in condition_lower for c in ["fog", "mist"]):
        _draw_small_fog(draw, x, y, size)
    else:
        _draw_small_cloud(draw, x, y, size)


def _draw_small_sun(draw, x: int, y: int, size: int) -> None:
    """Draw a small sun (3px diameter)."""
    cx = x + size // 2
    cy = y + size // 2
    r = 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#ffff00")


def _draw_small_cloud(draw, x: int, y: int, size: int) -> None:
    """Draw a small cloud."""
    cx = x + size // 2
    cy = y + size // 2
    # Three overlapping small circles
    draw.ellipse([cx - 3, cy - 1, cx - 1, cy + 1], fill="#cccccc")
    draw.ellipse([cx - 1, cy - 2, cx + 1, cy], fill="#cccccc")
    draw.ellipse([cx + 1, cy - 1, cx + 3, cy + 1], fill="#cccccc")


def _draw_small_rain(draw, x: int, y: int, size: int) -> None:
    """Draw a small rain cloud."""
    cx = x + size // 2
    cy = y + size // 2
    # Cloud
    draw.ellipse([cx - 3, cy - 2, cx - 1, cy], fill="#6666ff")
    draw.ellipse([cx - 1, cy - 3, cx + 1, cy], fill="#6666ff")
    draw.ellipse([cx + 1, cy - 2, cx + 3, cy], fill="#6666ff")
    # Rain drops
    draw.point((cx - 2, cy + 1), fill="#0000ff")
    draw.point((cx + 1, cy + 1), fill="#0000ff")


def _draw_small_snow(draw, x: int, y: int, size: int) -> None:
    """Draw a small snow cloud."""
    cx = x + size // 2
    cy = y + size // 2
    # Cloud
    draw.ellipse([cx - 3, cy - 2, cx - 1, cy], fill="#ffffff")
    draw.ellipse([cx - 1, cy - 3, cx + 1, cy], fill="#ffffff")
    draw.ellipse([cx + 1, cy - 2, cx + 3, cy], fill="#ffffff")
    # Snow
    draw.point((cx - 2, cy + 1), fill="#ffffff")
    draw.point((cx + 1, cy + 1), fill="#ffffff")


def _draw_small_storm(draw, x: int, y: int, size: int) -> None:
    """Draw a small dark cloud with lightning."""
    cx = x + size // 2
    cy = y + size // 2
    # Dark cloud
    draw.ellipse([cx - 3, cy - 2, cx - 1, cy], fill="#444444")
    draw.ellipse([cx - 1, cy - 3, cx + 1, cy], fill="#444444")
    draw.ellipse([cx + 1, cy - 2, cx + 3, cy], fill="#444444")
    # Lightning
    draw.line([(cx, cy + 1), (cx - 1, cy + 2)], fill="#ffff00", width=1)
    draw.line([(cx - 1, cy + 2), (cx + 1, cy + 3)], fill="#ffff00", width=1)


def _draw_small_fog(draw, x: int, y: int, size: int) -> None:
    """Draw a small fog."""
    cx = x + size // 2
    cy = y + size // 2
    # Horizontal lines
    draw.line([cx - 4, cy - 1, cx + 2, cy - 1], fill="#999999", width=1)
    draw.line([cx - 4, cy + 1, cx + 2, cy + 1], fill="#999999", width=1)
