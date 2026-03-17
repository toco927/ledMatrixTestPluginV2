# Message Queue Implementation

## Overview
The Trevor's World plugin now supports a message queue system that cycles through multiple messages, each with individual configuration, and persists state across restarts.

## Key Features

### 1. Queue Persistence
- **State Storage**: Queue index and completion state saved to `.trevor_world_queue_state` (configurable)
- **Resume Functionality**: Plugin resumes from last message when restarted
- **Cross-Platform**: Cache file stored in plugin directory for portability

### 2. Per-Message Configuration
Each message in the queue can override global settings:
- **Display**: `message`, `display_duration`
- **Visual**: `color`, `time_color`, `show_time`
- **Scrolling**: `scroll_enabled`, `scroll_speed`, `scroll_delay`
- **Fonts**: `message_font_size`, `time_font_size`
- **Control**: `enabled` flag to skip messages without removing them

### 3. Queue Management
- **Automatic Cycling**: Messages advance when `display_duration` expires
- **Enabled/Disabled**: Skip messages by setting `enabled: false`
- **Message Ordering**: Sort by `order` field (optional)
- **Completion Handling**: Display `empty_queue_message` when queue exhausted
- **Looping**: Queue resets to first message after last one

## Configuration

### Enable Queue Mode
```json
{
  "trevor-world": {
    "queue_mode": true,
    "message_queue": [
      {
        "id": "msg_001",
        "order": 1,
        "message": "First message",
        "display_duration": 5,
        "enabled": true
      },
      {
        "id": "msg_002",
        "order": 2,
        "message": "Second message",
        "display_duration": 3,
        "color": [255, 0, 0],
        "scroll_enabled": true
      }
    ],
    "empty_queue_message": "Queue Empty",
    "cache_file": ".trevor_world_queue_state"
  }
}
```

### Queue Message Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `id` | string | Required | Unique identifier |
| `order` | number | Position | Sort order in queue |
| `message` | string | Required | Message text |
| `display_duration` | number | 5 | Seconds to show message |
| `enabled` | boolean | true | Include in queue |
| `color` | [R,G,B] | Global default | Message color |
| `time_color` | [R,G,B] | Global default | Time display color |
| `show_time` | boolean | Global default | Show time |
| `scroll_enabled` | boolean | Global default | Enable scrolling |
| `scroll_speed` | number | Global default | Pixels per update |
| `scroll_delay` | number | Global default | Delay between updates |
| `message_font_size` | number | Global default | Message font size |
| `time_font_size` | number | Global default | Time font size |

## Implementation Details

### New Methods

#### `_get_cache_file_path()`
Resolves cache file path, falling back to current directory if plugin directory unavailable.

#### `_load_queue_state()`
Loads persisted queue index and completion state from cache file. Gracefully handles missing/corrupted cache.

#### `_save_queue_state()`
Saves current queue index and completion state with timestamp for debugging.

#### `_get_enabled_queue_messages()`
Returns filtered list of enabled messages, sorted by `order` field.

#### `_load_current_message_settings()`
Applies message-specific settings from current queue entry, with fallback to global defaults. Handles empty queues gracefully.

#### `_advance_queue()`
Moves to next enabled message, handles queue completion, saves state, resets scroll position, and updates display timing.

### Modified Methods

#### `__init__()`
- Added queue mode detection and initialization
- Calls `_load_queue_state()` to resume previous position
- Calls `_load_current_message_settings()` to apply first message settings
- Initializes `message_start_time` for duration tracking

#### `update()`
- Added queue advancement logic that triggers when `display_duration` elapsed
- Calls `_advance_queue()` to move to next message

#### `display(force_clear=False)`
- Added empty queue message display when `queue_complete = True`
- Gracefully measures and centers empty queue message

#### `on_config_change(new_config)`
- Detects queue configuration changes
- Resets to first message if queue modified
- Maintains backward compatibility with single-message mode

## Usage

### Single Message Mode (Original)
```json
{
  "trevor-world": {
    "queue_mode": false,
    "message": "Trevor made this",
    "scroll_enabled": true,
    "display_duration": 10
  }
}
```

### Queue Mode (New)
```json
{
  "trevor-world": {
    "queue_mode": true,
    "message_queue": [
      { "message": "Hello", "display_duration": 2 },
      { "message": "Welcome", "display_duration": 3 },
      { "message": "Goodbye", "display_duration": 2 }
    ]
  }
}
```

## Behavior

1. **Initialization**: Plugin loads saved queue index from cache, defaults to 0 if missing
2. **Display**: Shows current message with per-message settings applied
3. **Timing**: Tracks elapsed time since message started
4. **Advancement**: When duration expires, loads next enabled message
5. **Persistence**: Saves state after each advancement
6. **Completion**: Shows empty queue message when all messages cycled
7. **Resume**: Next display rotation continues from saved position

## Error Handling

- Missing cache file: Reset to index 0
- Corrupted cache: Log warning, reset to index 0
- Empty queue: Display `empty_queue_message`
- Invalid message index: Clamp to valid range
- Missing message settings: Fall back to global defaults

## Performance

- **Minimal Overhead**: State persistence only occurs on message change (not on every update)
- **Cache-Friendly**: Font and image caches reused within each message
- **Efficient Filtering**: Enabled message list generated only when needed

## Future Enhancements

- Dynamic queue reloading without restart
- Priority-based message ordering
- Time-based message scheduling
- Message repeat counts
- Fallback message display on error
