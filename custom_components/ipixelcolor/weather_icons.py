"""Generate weather icons for iPixel Color displays."""
from __future__ import annotations

from PIL import Image, ImageDraw
import tempfile
from pathlib import Path


def _create_icon(draw_func, size: tuple = (32, 32), bg_color: str = "000000") -> str:
    """
    Create an icon using a draw function and save it to a temp file.
    
    Args:
        draw_func: Function that takes an ImageDraw object and draws on it
        size: (width, height) tuple for the image
        bg_color: Background color in hex
    
    Returns:
        Path to the saved PNG file
    """
    img = Image.new("RGB", size, color=f"#{bg_color}")
    draw = ImageDraw.Draw(img)
    draw_func(draw)
    
    # Save to temp file
    temp_dir = Path(tempfile.gettempdir()) / "ipixelcolor_weather"
    temp_dir.mkdir(exist_ok=True)
    filepath = temp_dir / "weather_icon.png"
    img.save(filepath, "PNG")
    return str(filepath)


def sunny_icon() -> str:
    """Draw a sunny weather icon (sun with rays)."""
    def draw(draw):
        # Sun circle in center
        cx, cy = 16, 16
        radius = 6
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill="#ffff00")
        
        # Rays around sun
        ray_length = 3
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            import math
            rad = math.radians(angle)
            x1 = cx + (radius + 1) * math.cos(rad)
            y1 = cy + (radius + 1) * math.sin(rad)
            x2 = cx + (radius + ray_length + 1) * math.cos(rad)
            y2 = cy + (radius + ray_length + 1) * math.sin(rad)
            draw.line([(x1, y1), (x2, y2)], fill="#ffff00", width=1)
    
    return _create_icon(draw)


def cloudy_icon() -> str:
    """Draw a cloudy weather icon."""
    def draw(draw):
        # Cloud shape
        draw.ellipse([6, 12, 14, 20], fill="#cccccc")
        draw.ellipse([10, 10, 22, 20], fill="#cccccc")
        draw.ellipse([18, 12, 26, 20], fill="#cccccc")
        # Cloud base
        draw.rectangle([6, 18, 26, 22], fill="#cccccc")
    
    return _create_icon(draw)


def rainy_icon() -> str:
    """Draw a rainy weather icon (cloud with rain drops)."""
    def draw(draw):
        # Cloud
        draw.ellipse([5, 8, 13, 16], fill="#8888ff")
        draw.ellipse([9, 6, 21, 16], fill="#8888ff")
        draw.ellipse([17, 8, 25, 16], fill="#8888ff")
        draw.rectangle([5, 14, 25, 18], fill="#8888ff")
        
        # Rain drops below
        drop_color = "#0000ff"
        draw.ellipse([8, 20, 10, 24], fill=drop_color)
        draw.ellipse([14, 20, 16, 24], fill=drop_color)
        draw.ellipse([20, 20, 22, 24], fill=drop_color)
    
    return _create_icon(draw)


def snowy_icon() -> str:
    """Draw a snowy weather icon."""
    def draw(draw):
        # Cloud
        draw.ellipse([5, 8, 13, 16], fill="#ffffff")
        draw.ellipse([9, 6, 21, 16], fill="#ffffff")
        draw.ellipse([17, 8, 25, 16], fill="#ffffff")
        draw.rectangle([5, 14, 25, 18], fill="#ffffff")
        
        # Snowflakes
        import math
        for i, (cx, cy) in enumerate([(10, 22), (16, 22), (22, 22)]):
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                x = cx + 2 * math.cos(rad)
                y = cy + 2 * math.sin(rad)
                draw.line([(cx, cy), (x, y)], fill="#ffffff", width=1)
    
    return _create_icon(draw)


def stormy_icon() -> str:
    """Draw a stormy weather icon (dark cloud with lightning)."""
    def draw(draw):
        # Dark cloud
        draw.ellipse([4, 10, 12, 18], fill="#444444")
        draw.ellipse([8, 8, 20, 18], fill="#444444")
        draw.ellipse([16, 10, 24, 18], fill="#444444")
        draw.rectangle([4, 16, 24, 20], fill="#444444")
        
        # Lightning bolt
        lightning_color = "#ffff00"
        points = [(14, 20), (12, 24), (16, 24), (14, 28)]
        draw.polygon(points, fill=lightning_color)
    
    return _create_icon(draw)


def cloudy_sunny_icon() -> str:
    """Draw a partly cloudy icon (sun peeking behind cloud)."""
    def draw(draw):
        # Sun on left (small)
        draw.ellipse([4, 12, 10, 18], fill="#ffff00")
        
        # Cloud on right
        draw.ellipse([12, 10, 18, 16], fill="#cccccc")
        draw.ellipse([16, 8, 26, 16], fill="#cccccc")
        draw.rectangle([12, 14, 26, 18], fill="#cccccc")
    
    return _create_icon(draw)


def foggy_icon() -> str:
    """Draw a foggy weather icon."""
    def draw(draw):
        # Horizontal fog layers
        colors = ["#999999", "#aaaaaa", "#bbbbbb"]
        for i, color in enumerate(colors):
            y = 10 + (i * 6)
            draw.rectangle([4, y, 28, y + 4], fill=color)
    
    return _create_icon(draw)


def windy_icon() -> str:
    """Draw a windy weather icon."""
    def draw(draw):
        # Wind lines (curved)
        line_color = "#cccccc"
        draw.arc([6, 10, 24, 14], 0, 180, fill=line_color, width=2)
        draw.arc([6, 16, 24, 20], 0, 180, fill=line_color, width=2)
        draw.arc([6, 22, 24, 26], 0, 180, fill=line_color, width=2)
    
    return _create_icon(draw)


# Map weather conditions to icon generators
WEATHER_ICONS = {
    "sunny": sunny_icon,
    "clear-night": sunny_icon,
    "clear": sunny_icon,
    "cloudy": cloudy_icon,
    "overcast": cloudy_icon,
    "partlycloudy": cloudy_sunny_icon,
    "partly-cloudy": cloudy_sunny_icon,
    "partlycloudy-and-light-rain": rainy_icon,
    "rainy": rainy_icon,
    "rain": rainy_icon,
    "pouring": rainy_icon,
    "snow": snowy_icon,
    "snowy": snowy_icon,
    "snowy-rainy": snowy_icon,
    "thunderstorm": stormy_icon,
    "lightning": stormy_icon,
    "lightning-rainy": stormy_icon,
    "fog": foggy_icon,
    "windy": windy_icon,
}


def get_weather_icon(condition: str) -> str:
    """
    Get the path to a weather icon for the given condition.
    
    Args:
        condition: Weather condition (e.g., "sunny", "rainy", "cloudy")
    
    Returns:
        Path to the generated PNG icon file
    """
    condition_lower = condition.lower().strip()
    
    # Try direct match first
    if condition_lower in WEATHER_ICONS:
        return WEATHER_ICONS[condition_lower]()
    
    # Try partial matches
    for key, icon_func in WEATHER_ICONS.items():
        if key in condition_lower or condition_lower in key:
            return icon_func()
    
    # Default to cloudy if no match
    return cloudy_icon()
