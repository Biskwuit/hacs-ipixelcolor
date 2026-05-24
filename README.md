# iPixel Color LED Matrix — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io/)

Control your **iPixel Color LED matrix** devices via Bluetooth Low Energy directly from Home Assistant.

Built on the [pypixelcolor](https://lucagoc.github.io/pypixelcolor/latest/) library.

---

## Features

- 🔵 **Automatic Bluetooth discovery** — iPixel devices are detected automatically
- 💡 **Light entity** — power on/off + brightness slider
- 🔄 **Orientation selector** — rotate the display (0°, 90°, 180°, 270°)
- 🌟 **Brightness number** — fine-grained 0–100% control
- 🕐 **Clock button** — one-click clock mode
- 🗑️ **Clear button** — wipe the EEPROM
- 📋 **Services** — send text, send images/GIFs, set clock, set individual pixels

---

## Requirements

- Home Assistant 2024.1 or newer
- Bluetooth adapter accessible by HA (built-in or USB dongle)
- iPixel Color LED matrix device

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/your-username/hacs-ipixelcolor` as an **Integration**
3. Install **iPixel Color LED Matrix**
4. Restart Home Assistant

### Manual

Copy the `custom_components/ipixelcolor` folder into your HA `config/custom_components/` directory and restart.

---

## Configuration

### Auto-discovery

When your iPixel device is powered on and in range, Home Assistant will detect it automatically and propose adding it via a notification.

### Manual setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **iPixel Color**
3. The integration will scan for nearby devices. Select yours from the list, or enter the Bluetooth MAC address manually (e.g. `30:E1:AF:BD:5F:D0`)

---

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `light.ipixel_color` | Light | Power control + brightness |
| `number.ipixel_color_brightness` | Number | Brightness 0–100% slider |
| `select.ipixel_color_orientation` | Select | Display rotation |
| `button.ipixel_color_clear_display` | Button | Clear EEPROM |
| `button.ipixel_color_show_clock` | Button | Activate clock mode |

---

## Services

### `ipixelcolor.send_text`

Display a message on the matrix.

```yaml
service: ipixelcolor.send_text
data:
  entity_id: light.ipixel_color
  text: "Hello HA!"
  animation: 1       # 0=static, 1=scroll left, 2=right, 3=up, 4=down
  speed: 80          # 0-100
  color: "ff6600"    # hex color
  rainbow_mode: 0    # 0 or 1
  save_slot: 0       # 0-9
```

### `ipixelcolor.send_image`

Display an image or GIF from the HA host filesystem.

```yaml
service: ipixelcolor.send_image
data:
  entity_id: light.ipixel_color
  path: "/config/www/my_animation.gif"
  save_slot: 1
```

### `ipixelcolor.set_clock`

Switch to clock display mode.

```yaml
service: ipixelcolor.set_clock
data:
  entity_id: light.ipixel_color
  style: 1         # 1-5
  show_date: true
  format_24: true
```

### `ipixelcolor.set_pixel`

Set the color of a single pixel.

```yaml
service: ipixelcolor.set_pixel
data:
  entity_id: light.ipixel_color
  x: 0
  y: 0
  color: "ff0000"
```

---

## Automations example

Display a welcome message when someone arrives home:

```yaml
automation:
  - alias: "iPixel — Welcome home"
    trigger:
      - platform: state
        entity_id: person.your_name
        to: home
    action:
      - service: ipixelcolor.send_text
        data:
          entity_id: light.ipixel_color
          text: "Welcome home!"
          animation: 1
          color: "00ff88"
          speed: 70
```

Show the clock at night:

```yaml
automation:
  - alias: "iPixel — Night clock"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: ipixelcolor.set_clock
        data:
          entity_id: light.ipixel_color
          style: 1
          format_24: true
      - service: ipixelcolor.send_text  # lower brightness at night
        data:
          entity_id: light.ipixel_color
          text: ""
      - service: number.set_value
        target:
          entity_id: number.ipixel_color_brightness
        data:
          value: 20
```

Display the current album cover on the LED matrix when music starts:

```yaml
automation:
  - alias: "iPixel — Show album cover"
    trigger:
      - platform: state
        entity_id: media_player.music_assistant
        to: playing
    action:
      - service: ipixelcolor.send_media_cover
        data:
          ipixel_entity_id: light.ipixel_color
          media_player_entity_id: media_player.music_assistant
          save_slot: 0
```

Display the current weather condition as an icon:

```yaml
automation:
  - alias: "iPixel — Show weather icon"
    trigger:
      - platform: state
        entity_id: weather.home
    action:
      - service: ipixelcolor.send_weather_icon
        data:
          ipixel_entity_id: light.ipixel_color
          weather_entity_id: weather.home
          save_slot: 0
```

---

## Troubleshooting

**Device not discovered automatically**
Make sure Bluetooth is enabled in HA and the device is powered on. You can also add it manually via the MAC address.

**Cannot connect**
Ensure no other app (phone, CLI) is connected to the device simultaneously — BLE allows only one connection at a time.

**Commands not working**
Check the HA logs (`Settings → System → Logs`) for `ipixelcolor` entries.

---

## License

MIT — see [pypixelcolor](https://github.com/lucagoc/pypixelcolor) for the underlying library license.
