# Trevor's World Plugin

A feature-rich plugin for the LEDMatrix plugin system. Displays customizable messages with optional time display, scrolling support, and a message queue system for cycling through multiple messages.

## Purpose

This plugin serves as:
- **Test plugin** for validating the plugin system works correctly
- **Example plugin** for developers creating their own plugins
- **Comprehensive demonstration** of the BasePlugin interface with advanced features
- **Practical plugin** for displaying rotating messages with individual styling

## Features

- ✅ Single message or message queue mode
- ✅ Per-message configuration (colors, fonts, duration, scrolling)
- ✅ Optional time display with separate styling
- ✅ Text scrolling for messages wider than display
- ✅ Configurable fonts and sizes
- ✅ State persistence (resumes queue position on restart)
- ✅ Graceful error handling
- ✅ Configuration validation
- ✅ Font loading with multiple fallback strategies

## Installation

This plugin is included as a test plugin. To enable it:

1. Edit `config/config.json` and add (choose single message or queue mode):

**Single Message Mode:**
```json
{
  "trevor-world": {
    "enabled": true,
    "queue_mode": false,
    "message": "Trevor made this",
    "show_time": true,
    "color": [255, 255, 255],
    "time_color": [0, 255, 255],
    "display_duration": 10,
    "scroll_enabled": false
  }
}
```

**Queue Mode:**
```json
{
  "trevor-world": {
    "enabled": true,
    "queue_mode": true,
    "message_queue": [
      {
        "id": "msg_001",
        "message": "Message 1",
        "display_duration": 5
      },
      {
        "id": "msg_002",
        "message": "Message 2",
        "display_duration": 3,
        "color": [255, 0, 0]
      }
    ],
    "empty_queue_message": "Queue Empty",
    "cache_file": ".trevor_world_queue_state"
  }
}
```

2. Restart the display:

```bash
sudo systemctl restart ledmatrix
```

## Configuration Options

### Global Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable the plugin |
| `queue_mode` | boolean | `false` | Enable message queue cycling (true) or single message mode (false) |
| `message` | string | `"Trevor made this"` | Single message to display (single message mode only) |
| `show_time` | boolean | `true` | Show current time below message |
| `color` | array | `[255, 255, 255]` | RGB color for message (white) |
| `time_color` | array | `[0, 255, 255]` | RGB color for time (cyan) |
| `display_duration` | number | `5` | Display time in seconds |
| `font_family` | string | `"press_start"` | Font family (press_start, four_by_six, tom_thumb, tiny, picopixel) |
| `message_font_size` | integer | `10` | Font size for message (1-100) |
| `time_font_size` | integer | `8` | Font size for time (1-100) |
| `scroll_enabled` | boolean | `false` | Enable text scrolling for wide messages |
| `scroll_speed` | number | `1` | Scroll speed in pixels per frame (0.1-10) |
| `scroll_delay` | number | `0.01` | Delay between scroll frames in seconds (0.001-0.1) |
| `scroll_loop` | boolean | `true` | Loop scrolling continuously |
| `scroll_gap_width` | number | `32` | Gap width between scroll loops in pixels |

### Queue Mode Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `message_queue` | array | `[]` | Array of message objects to cycle through |
| `empty_queue_message` | string | `"Queue Empty"` | Message shown when queue is empty |
| `cache_file` | string | `".trevor_world_queue_state"` | File for persisting queue state |

### Queue Message Object

Each message in `message_queue` can have:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | No | Unique identifier for message |
| `order` | integer | No | Sort order (defaults to array position) |
| `message` | string | **Yes** | The message text to display |
| `display_duration` | number | No | Override global duration for this message |
| `color` | array | No | Override [R, G, B] color for this message |
| `time_color` | array | No | Override [R, G, B] color for time in this message |
| `show_time` | boolean | No | Override time display for this message |
| `scroll_enabled` | boolean | No | Override scrolling for this message |
| `scroll_speed` | number | No | Override scroll speed for this message |
| `scroll_delay` | number | No | Override scroll delay for this message |
| `message_font_size` | integer | No | Override message font size for this message |
| `time_font_size` | integer | No | Override time font size for this message |
| `enabled` | boolean | No | Include message in queue (default: true) |

## Examples

### 1. Minimal Configuration (Single Message)
```json
{
  "trevor-world": {
    "enabled": true
  }
}
```

### 2. Custom Single Message with Scrolling
```json
{
  "trevor-world": {
    "enabled": true,
    "message": "Go Lightning!",
    "color": [0, 128, 255],
    "display_duration": 15,
    "scroll_enabled": true,
    "scroll_speed": 2
  }
}
```

### 3. Message Only (No Time Display)
```json
{
  "trevor-world": {
    "enabled": true,
    "message": "LED Matrix",
    "show_time": false,
    "color": [255, 0, 255]
  }
}
```

### 4. Queue with Multiple Messages
```json
{
  "trevor-world": {
    "enabled": true,
    "queue_mode": true,
    "message_queue": [
      {
        "id": "welcome",
        "order": 1,
        "message": "Welcome!",
        "display_duration": 3,
        "color": [0, 255, 0]
      },
      {
        "id": "time_msg",
        "order": 2,
        "message": "Check the time",
        "display_duration": 2,
        "color": [255, 255, 0],
        "show_time": true
      },
      {
        "id": "scroll_msg",
        "order": 3,
        "message": "This message scrolls across the display",
        "display_duration": 5,
        "color": [255, 0, 255],
        "scroll_enabled": true,
        "scroll_speed": 1.5
      }
    ],
    "empty_queue_message": "All done!"
  }
}
```

### 5. Queue with Per-Message Font Sizes
```json
{
  "trevor-world": {
    "enabled": true,
    "queue_mode": true,
    "message_font_size": 10,
    "message_queue": [
      {
        "message": "Big Text",
        "message_font_size": 14,
        "display_duration": 3
      },
      {
        "message": "Small Text",
        "message_font_size": 6,
        "display_duration": 3
      }
    ]
  }
}
```

## Testing the Plugin

### 1. Check Plugin Discovery

After adding the configuration, check the logs:

```bash
sudo journalctl -u ledmatrix -f | grep trevor-world
```

You should see:
```
Discovered plugin: trevor-world v1.0.0
Loaded plugin: trevor-world
Trevor's World plugin initialized (queue_mode=false)
```

For queue mode:
```
Trevor's World plugin initialized (queue_mode=true)
Queue mode enabled with 3 messages
Loaded queue state: index=0, complete=False
```

### 2. Test via Web API

Check if the plugin is installed:
```bash
curl http://localhost:5001/api/plugins/installed | jq '.plugins[] | select(.id=="trevor-world")'
```

### 3. Watch It Display

The plugin will appear in the normal display rotation. In queue mode, it will automatically advance to the next message after each `display_duration` expires.

### 4. Verify Queue State Persistence

Check that the cache file is created:
```bash
ls -la ~/.trevor_world_queue_state
# or wherever you set cache_file
```

The file contains JSON with the current queue index and timestamp:
```json
{
  "current_index": 1,
  "queue_complete": false,
  "saved_at": "2026-03-17T14:32:45.123456"
}
```

## Development Notes

This plugin demonstrates:

### BasePlugin Interface
```python
class TrevorWorldPlugin(BasePlugin):
    def __init__(self, plugin_id, config, display_manager, cache_manager, plugin_manager):
        super().__init__(plugin_id, config, display_manager, cache_manager, plugin_manager)
        # Initialize configuration, fonts, cache
    
    def update(self):
        # Update time display, handle scrolling, advance queue
        pass
    
    def display(self, force_clear=False):
        # Render message and time to display
        pass
    
    def on_config_change(self, new_config):
        # Handle dynamic configuration updates
        pass
```

### Advanced Features

**Font Management**
- Multiple font fallback strategies (TTF, BDF, default)
- Per-message font size configuration
- Graceful degradation if fonts unavailable

**Scrolling**
- Pre-renders text to image cache for smooth animation
- Configurable scroll speed and delay
- Loop support with gap width

**State Persistence**
- Saves queue state to JSON cache file
- Automatic directory creation
- Graceful error handling for corrupted/missing cache

**Per-Message Configuration**
- Each queue message can override global settings
- Enabled/disabled message filtering
- Message sorting by order field

**Performance Optimization**
- Font caching to avoid reload per frame
- Image caching for scrolling animation
- Efficient queue message filtering

## Troubleshooting

### Plugin Not Loading
- Check that `manifest.json` is valid JSON
- Verify `enabled: true` in config.json
- Check logs for error messages: `sudo journalctl -u ledmatrix -f | grep trevor-world`
- Ensure Python path is correct

### Queue Not Advancing
- Verify `queue_mode: true` in config
- Check that `display_duration` is set for each message
- Look for log messages about queue advancement
- Ensure messages are marked `enabled: true`

### Display Issues
- Verify display_manager is initialized
- Check that colors are valid RGB arrays [R, G, B]
- Ensure message isn't too long for display (enable scrolling if needed)
- Check font files are accessible

### Scrolling Not Working
- Verify `scroll_enabled: true`
- Check that message width exceeds display width
- Adjust `scroll_speed` and `scroll_delay` for smoother/faster motion
- Monitor logs for text cache creation errors

### Configuration Errors
- Validate JSON syntax in config.json using `python3 -m json.tool config.json`
- Check that all color arrays have exactly 3 values (RGB)
- Ensure numeric values (duration, speed, delay) are valid numbers
- For queue mode, ensure at least one message has `enabled: true`

### State Persistence Issues
- Check cache file location and permissions: `ls -la .trevor_world_queue_state`
- Ensure directory exists or allow plugin to create it
- Look for cache-related warnings in logs
- Delete cache file to reset to index 0: `rm .trevor_world_queue_state`

### Font Loading Issues
- Check logs for font loading errors
- Verify font files exist in expected locations
- Try with default font if custom fonts not found
- Check font family names are valid (press_start, four_by_six, etc.)

## License

GPL-3.0 License - Same as LEDMatrix project

## Contributing

This is a feature-rich reference plugin included with LEDMatrix. Feel free to use it as a template for your own plugins!

## Support

For plugin system questions and documentation, see:
- [LEDMatrix Plugin Documentation](https://github.com/ChuckBuilds/LEDMatrix)
- [Plugin Architecture Spec](https://github.com/ChuckBuilds/LEDMatrix/blob/main/PLUGIN_ARCHITECTURE_SPEC.md)
- [Queue Implementation Details](./QUEUE_IMPLEMENTATION.md)


