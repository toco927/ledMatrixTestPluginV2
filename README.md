# Trevor's World Plugin

A simple and efficient plugin for the LEDMatrix plugin system that displays a rotating list of messages. Each message is displayed for a configurable duration with a randomly generated number (1-10) appended to it.

## Purpose

This plugin demonstrates:
- **Simple list cycling** - Rotate through messages in sequence
- **Per-message customization** - Color and duration overrides
- **Random number generation** - Append random numbers to messages
- **Clean architecture** - Minimal, focused codebase
- **Configuration validation** - Robust error checking

## Features

- ✅ Message list cycling (loops indefinitely)
- ✅ Random number (1-10) appended to each message
- ✅ Per-message color override
- ✅ Per-message display duration
- ✅ Universal scrolling (applies to all messages)
- ✅ Configurable default font and colors
- ✅ Graceful error handling
- ✅ Configuration validation

## Installation

1. Edit `config/config.json` and add:

```json
{
  "trevor-world": {
    "enabled": true,
    "font_family": "press_start",
    "message_font_size": 10,
    "color": [255, 255, 255],
    "display_duration": 5,
    "scroll": {
      "enabled": false,
      "speed": 1,
      "delay": 0.01,
      "gap_width": 32
    },
    "messages": [
      {
        "message": "Message One",
        "display_duration": 5,
        "color": [255, 255, 255]
      },
      {
        "message": "Message Two",
        "display_duration": 4,
        "color": [0, 255, 0]
      },
      {
        "message": "Message Three",
        "display_duration": 6,
        "color": [255, 128, 0]
      }
    ]
  }
}
```

2. The plugin will load automatically with your plugin system.

## Configuration

### Plugin-Level Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable the plugin |
| `messages` | array | `[]` | List of messages to display |
| `font_family` | string | `press_start` | Font family (press_start, four_by_six, tom_thumb, tiny, picopixel) |
| `message_font_size` | integer | `10` | Font size in pixels (1-100) |
| `color` | RGB array | `[255, 255, 255]` | Default text color [R, G, B] |
| `display_duration` | number | `5` | Default seconds per message |
| `font_path` | string | `assets/fonts/PressStart2P-Regular.ttf` | Path to font file |
| `scroll.enabled` | boolean | `false` | Enable scrolling for wide messages |
| `scroll.speed` | number | `1` | Pixels to scroll per frame (0.1-50) |
| `scroll.delay` | number | `0.01` | Seconds between scroll updates (0.001-0.1) |
| `scroll.gap_width` | number | `32` | Gap in pixels between text loops |

### Message-Level Settings

Each message in the `messages` array is an object with:

| Setting | Type | Required | Default | Description |
|---------|------|----------|---------|-------------|
| `message` | string | ✅ | - | Text to display (1-100 characters) |
| `display_duration` | number | ❌ | plugin default | Seconds to display (0.5-300) |
| `color` | RGB array | ❌ | plugin default | Text color [R, G, B] |

**Note:** A random number (1-10) is automatically appended to each message when displayed.

## Behavior

### Message Cycling

Messages cycle through in order:
1. Display message 1 for its `display_duration`
2. Display message 2 for its `display_duration`
3. Continue through all messages
4. Loop back to message 1 and repeat indefinitely

### Display Format

Each message displays as: `{message text} {random_number}`

Example:
```
"Trevor made this 7"
"Welcome to LED Matrix 2"
"Custom Message System 9"
```

The random number changes each time the message is displayed.

### Scrolling

Scrolling is **universal** - the same scrolling settings apply to all messages:

- **When enabled**: Text that is wider than the display width will scroll horizontally
- **When disabled**: Text is centered (default behavior)
- **Settings affect all messages**: Changing scroll settings applies to the entire message list, not individual messages

Example with scrolling enabled:
```json
"scroll": {
  "enabled": true,
  "speed": 1,
  "delay": 0.01,
  "gap_width": 32
}
```

**Scrolling Parameters:**
- `speed`: Pixels per frame (higher = faster scrolling)
- `delay`: Seconds between each scroll update (lower = smoother but faster)
- `gap_width`: Blank space in pixels between text loops

## Configuration Schema

See `config_schema.json` for the complete JSON schema definition used for validation.

## Development

### Adding More Features

To extend this plugin:

1. Edit `manager.py` - Add methods to `TrevorWorldPlugin` class
2. Update `config_schema.json` - Add new configuration properties
3. Update validation in `validate_config()` method
4. Update `on_config_change()` to handle new properties

### Testing Configuration

Validate your config file:
```bash
python3 -m json.tool config_schema.json
python3 -m json.tool example_config.json
```

Check plugin syntax:
```bash
python3 -m py_compile manager.py
```

## License

Same as parent LEDMatrix plugin system.
