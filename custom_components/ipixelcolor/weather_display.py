"""Generate weather display with temperature and icon for iPixel Color."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import tempfile
from pathlib import Path


def generate_weather_display(
    condition: str,
    temperature: float,
    location: str = "",
    show_location: bool = False,
) -> str:
    """
    Generate a weather display image with temperature and weather icon.
    
    Args:
        condition: Weather condition (sunny, rainy, cloudy, snowy, stormy, etc.)
        temperature: Temperature in Celsius or Fahrenheit
        location: Optional location name
        show_location: Whether to show the location text
    
    Returns:
        Path to the generated PNG file
    """
    # Image size for 32x8 LED matrix (4:1 ratio, 256x64)
    width, height = 256, 64
    img = Image.new("RGB", (width, height), color="#000000")
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fallback to default
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except (OSError, IOError):
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw weather icon on the left (32x32 area)
    _draw_weather_icon(draw, condition, x=4, y=16)
    
    # Draw temperature on the right (large text)
    temp_str = f"{int(temperature)}°"
    draw.text((100, 8), temp_str, fill="#ffffff", font=font_large)
    
    # Draw condition text (smaller)
    condition_text = condition.replace("-", " ").title()[:20]
    draw.text((100, 56), condition_text, fill="#cccccc", font=font_small)
    
    # Optional: Draw location
    if show_location and location:
        location_text = location[:15]
        draw.text((100, 36), location_text, fill="#aaaaaa", font=font_small)
    
    # Save to temp file
    temp_dir = Path(tempfile.gettempdir()) / "ipixelcolor_weather"
    temp_dir.mkdir(exist_ok=True)
    filepath = temp_dir / "weather_display.png"
    img.save(filepath, "PNG")
    
    return str(filepath)


def _draw_weather_icon(draw, condition: str, x: int = 4, y: int = 16, size: int = 32) -> None:
    """Draw a small weather icon at position (x, y)."""
    condition_lower = condition.lower().strip()
    
    if any(c in condition_lower for c in ["sunny", "clear"]):
        _draw_sun(draw, x, y, size)
    elif any(c in condition_lower for c in ["cloud", "overcast"]):
        _draw_cloud(draw, x, y, size)
    elif any(c in condition_lower for c in ["rain", "pouring"]):
        _draw_rain(draw, x, y, size)
    elif any(c in condition_lower for c in ["snow"]):
        _draw_snow(draw, x, y, size)
    elif any(c in condition_lower for c in ["thunder", "lightning"]):
        _draw_storm(draw, x, y, size)
    elif any(c in condition_lower for c in ["fog", "mist"]):
        _draw_fog(draw, x, y, size)
    elif any(c in condition_lower for c in ["wind"]):
        _draw_wind(draw, x, y, size)
    else:
        _draw_cloud(draw, x, y, size)  # Default to cloud


def _draw_sun(draw, x: int, y: int, size: int) -> None:
    """Draw a sun icon."""
    cx = x + size // 2
    cy = y + size // 2
    radius = size // 4
    
    # Sun circle
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill="#ffff00",
        outline="#ffaa00",
        width=1,
    )
    
    # Rays
    ray_len = size // 5
    import math
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        rad = math.radians(angle)
        x1 = cx + (radius + 2) * math.cos(rad)
        y1 = cy + (radius + 2) * math.sin(rad)
        x2 = cx + (radius + ray_len) * math.cos(rad)
        y2 = cy + (radius + ray_len) * math.sin(rad)
        draw.line([(x1, y1), (x2, y2)], fill="#ffff00", width=2)


def _draw_cloud(draw, x: int, y: int, size: int) -> None:
    """Draw a cloud icon."""
    cx = x + size // 2
    cy = y + size // 2
    scale = size / 32  # Scale from 32px base
    
    # Cloud shape (multiple overlapping circles)
    draw.ellipse(
        [cx - 12 * scale, cy - 4 * scale, cx - 4 * scale, cy + 4 * scale],
        fill="#cccccc",
        outline="#999999",
        width=1,
    )
    draw.ellipse(
        [cx - 6 * scale, cy - 8 * scale, cx + 6 * scale, cy + 4 * scale],
        fill="#cccccc",
        outline="#999999",
        width=1,
    )
    draw.ellipse(
        [cx + 4 * scale, cy - 4 * scale, cx + 12 * scale, cy + 4 * scale],
        fill="#cccccc",
        outline="#999999",
        width=1,
    )


def _draw_rain(draw, x: int, y: int, size: int) -> None:
    """Draw a rain icon (cloud with drops)."""
    cx = x + size // 2
    cy = y + size // 2
    scale = size / 32
    
    # Cloud
    draw.ellipse(
        [cx - 12 * scale, cy - 6 * scale, cx - 4 * scale, cy + 2 * scale],
        fill="#6666ff",
        outline="#0000aa",
        width=1,
    )
    draw.ellipse(
        [cx - 6 * scale, cy - 10 * scale, cx + 6 * scale, cy + 2 * scale],
        fill="#6666ff",
        outline="#0000aa",
        width=1,
    )
    draw.ellipse(
        [cx + 4 * scale, cy - 6 * scale, cx + 12 * scale, cy + 2 * scale],
        fill="#6666ff",
        outline="#0000aa",
        width=1,
    )
    
    # Raindrops
    drop_y = cy + 8 * scale
    for drop_x in [cx - 8 * scale, cx, cx + 8 * scale]:
        draw.ellipse(
            [drop_x - 2 * scale, drop_y, drop_x + 2 * scale, drop_y + 6 * scale],
            fill="#0000ff",
        )


def _draw_snow(draw, x: int, y: int, size: int) -> None:
    """Draw a snow icon."""
    cx = x + size // 2
    cy = y + size // 2
    scale = size / 32
    
    # Cloud
    draw.ellipse(
        [cx - 12 * scale, cy - 6 * scale, cx - 4 * scale, cy + 2 * scale],
        fill="#ffffff",
        outline="#cccccc",
        width=1,
    )
    draw.ellipse(
        [cx - 6 * scale, cy - 10 * scale, cx + 6 * scale, cy + 2 * scale],
        fill="#ffffff",
        outline="#cccccc",
        width=1,
    )
    draw.ellipse(
        [cx + 4 * scale, cy - 6 * scale, cx + 12 * scale, cy + 2 * scale],
        fill="#ffffff",
        outline="#cccccc",
        width=1,
    )
    
    # Snowflakes
    import math
    snowflake_y = cy + 8 * scale
    for snowflake_x in [cx - 8 * scale, cx, cx + 8 * scale]:
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            x1 = snowflake_x + 3 * scale * math.cos(rad)
            y1 = snowflake_y + 3 * scale * math.sin(rad)
            draw.line([(snowflake_x, snowflake_y), (x1, y1)], fill="#ffffff", width=1)


def _draw_storm(draw, x: int, y: int, size: int) -> None:
    """Draw a storm icon (dark cloud with lightning)."""
    cx = x + size // 2
    cy = y + size // 2
    scale = size / 32
    
    # Dark cloud
    draw.ellipse(
        [cx - 12 * scale, cy - 6 * scale, cx - 4 * scale, cy + 2 * scale],
        fill="#444444",
        outline="#222222",
        width=1,
    )
    draw.ellipse(
        [cx - 6 * scale, cy - 10 * scale, cx + 6 * scale, cy + 2 * scale],
        fill="#444444",
        outline="#222222",
        width=1,
    )
    draw.ellipse(
        [cx + 4 * scale, cy - 6 * scale, cx + 12 * scale, cy + 2 * scale],
        fill="#444444",
        outline="#222222",
        width=1,
    )
    
    # Lightning bolt
    lightning_points = [
        (cx + 2 * scale, cy + 4 * scale),
        (cx, cy + 8 * scale),
        (cx + 4 * scale, cy + 8 * scale),
        (cx + 2 * scale, cy + 12 * scale),
    ]
    draw.polygon(lightning_points, fill="#ffff00")


def _draw_fog(draw, x: int, y: int, size: int) -> None:
    """Draw a fog icon (horizontal lines)."""
    cx = x + size // 2
    cy = y + size // 2
    scale = size / 32
    
    for i in range(3):
        y_offset = cy - 8 * scale + (i * 6 * scale)
        draw.rectangle(
            [cx - 12 * scale, y_offset, cx + 12 * scale, y_offset + 4 * scale],
            fill="#999999",
            outline="#666666",
        )


def _draw_wind(draw, x: int, y: int, size: int) -> None:
    """Draw a wind icon."""
    cx = x + size // 2
    cy = y + size // 2
    scale = size / 32
    
    # Three curved wind lines
    for i in range(3):
        y_offset = cy - 8 * scale + (i * 6 * scale)
        # Draw arc approximation with multiple lines
        for dx in range(-12, 13, 2):
            import math
            curve_y = y_offset + math.sin(dx / 4) * 3 * scale
            if dx == -12:
                x1, y1 = cx + dx * scale, y_offset
            draw.line(
                [(cx + dx * scale, curve_y), (cx + (dx + 2) * scale, curve_y)],
                fill="#cccccc",
                width=2,
            )
