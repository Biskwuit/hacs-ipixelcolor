"""Advanced text rendering with pixel-perfect control for iPixel Color."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont


def render_text_advanced(
    text: str,
    x: int = 0,
    y: int = 0,
    max_width: int = 4,
    max_height: int = 7,
    text_color: str = "ffffff",
    bg_color: str = "000000",
    font_size: int | None = None,
    matrix_width: int = 32,
    matrix_height: int = 32,
) -> dict[str, list[tuple]]:
    """
    Render text with strict pixel dimension constraints per character.
    Returns pixel data as a list of (x, y, color) tuples instead of an image file.
    
    Args:
        text: The text to render
        x: Starting X position (pixels from left)
        y: Starting Y position (pixels from top)
        max_width: Maximum pixels wide per character
        max_height: Maximum pixels tall per character
        text_color: Color in hex (e.g., "ffffff")
        bg_color: Background color in hex
        font_size: Font size in pixels (auto-calculated if None)
        matrix_width: Total matrix width in pixels
        matrix_height: Total matrix height in pixels
    
    Returns:
        Dictionary with 'pixels' list and 'bg_color'
    """
    # Create image in memory to measure text
    img = Image.new("RGB", (matrix_width, matrix_height), color=f"#{bg_color}")
    draw = ImageDraw.Draw(img)
    
    # Auto-calculate font size based on max_height if not provided
    if font_size is None:
        font_size = max(max_height - 2, 5)  # Leave 1-2px margin
    
    # Try to load font
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
        )
    except (OSError, IOError):
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
            )
        except (OSError, IOError):
            font = ImageFont.load_default()
    
    # Render each character with position control
    current_x = x
    current_y = y
    
    for char in text:
        # Get character bounding box to know actual size
        try:
            bbox = draw.textbbox((current_x, current_y), char, font=font)
            char_width = bbox[2] - bbox[0]
            char_height = bbox[3] - bbox[1]
        except:
            # Fallback if textbbox fails
            char_width = max_width
            char_height = max_height
        
        # Check if character fits within constraints
        if char_width > max_width:
            # Character is too wide - skip
            continue
        
        if char_height > max_height:
            # Character is too tall - skip
            continue
        
        # Check if we're out of bounds horizontally
        if current_x + char_width > matrix_width:
            # Move to next line
            current_x = x
            current_y += max_height + 1  # Move down by max_height + 1px spacing
        
        # Check if we're out of bounds vertically
        if current_y + char_height > matrix_height:
            # Text doesn't fit
            break
        
        # Draw the character
        draw.text(
            (current_x, current_y),
            char,
            fill=f"#{text_color}",
            font=font,
        )
        
        # Move cursor
        current_x += char_width + 1  # 1px spacing between chars
    
    # Extract pixels from the image
    pixels = []
    img_data = img.getdata()
    img_width, img_height = img.size
    
    for py in range(img_height):
        for px in range(img_width):
            pixel_idx = py * img_width + px
            pixel_rgb = img_data[pixel_idx]
            
            # Convert RGB to hex
            pixel_hex = f"{pixel_rgb[0]:02x}{pixel_rgb[1]:02x}{pixel_rgb[2]:02x}"
            
            # Only add non-background pixels
            if pixel_hex.lower() != bg_color.lower():
                pixels.append((px, py, pixel_hex))
    
    return {
        "pixels": pixels,
        "bg_color": bg_color,
    }
