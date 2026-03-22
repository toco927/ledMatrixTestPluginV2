# Trevor's World Plugin - Scrolling Improvements

## Summary of Changes

Your plugin has been updated to use **ScrollHelper** - a dedicated scrolling utility class - instead of manual scroll position management. This provides smoother, more reliable scrolling animation and better performance.

## Key Improvements

### 1. **ScrollHelper Integration**
- **Before**: Manual scroll position tracking with `self.scroll_position`, `self.last_scroll_time`, and time-based calculations
- **After**: Delegated to `ScrollHelper` class which handles:
  - Frame-based scrolling (pixels per frame instead of pixels per second)
  - Proper FPS synchronization
  - Image caching and efficient rendering
  - Scroll completion detection

### 2. **Better Imports**
```python
# Added:
import logging
from typing import Dict, Any
from src.common.scroll_helper import ScrollHelper

logger = logging.getLogger(__name__)
```

### 3. **Initialization Changes**
The `__init__` method now:
- Initializes `ScrollHelper` with display dimensions
- Configures frame-based scrolling for smoother animation
- Supports `target_fps` configuration (default 120 FPS)
- Logs detailed scroll configuration information

```python
# New initialization in __init__:
self.scroll_helper = ScrollHelper(display_width, display_height, logger=self.logger)

# Configure for frame-based scrolling
if hasattr(self.scroll_helper, 'set_frame_based_scrolling'):
    self.scroll_helper.set_frame_based_scrolling(True)
    self.scroll_helper.set_scroll_speed(self.scroll_speed)
```

### 4. **Improved Cache Creation**
The `_create_scroll_cache()` method now:
- Properly centers text vertically using textbbox calculations
- Sets the cache image in ScrollHelper for efficient rendering
- Validates the image was set correctly
- Handles RGB mode conversion

### 5. **Better Update Loop**
The `update()` method now:
- Uses ScrollHelper's `update_scroll_position()` for consistent scrolling
- Automatically verifies the cached image is set
- Properly resets scroll when text fits or scrolling is disabled

### 6. **Enhanced Display Method**
The `display()` method now:
- Uses `ScrollHelper.get_visible_portion()` for efficient cropping
- Includes a new `_display_static_text()` helper for non-scrolling text
- Better error handling and fallback support
- Added FPS logging via `_log_frame_rate()`

### 7. **New Helper Methods**
- **`_display_static_text(text, width, height)`**: Handles centered text display
- **`_log_frame_rate()`**: Tracks and logs average/current FPS every 5 seconds

### 8. **Configuration Runtime Changes**
The `on_config_change()` method now:
- Properly updates ScrollHelper settings when scroll_speed, scroll_delay, or target_fps change
- Handles frame-based vs. time-based scrolling mode detection
- Resets scroll helper appropriately when scroll is toggled

### 9. **Cleanup**
The `cleanup()` method now:
- Calls `self.scroll_helper.clear_cache()` to free memory
- Properly releases image cache resources

## Scrolling Configuration

In your config.json, you can now use:

```json
{
  "scroll": {
    "enabled": true,
    "speed": 1,           // pixels per frame (recommended: 0.5-2)
    "delay": 0.01,        // seconds per frame (0.01 = 100 FPS)
    "gap_width": 32       // pixels between message loops
  },
  "target_fps": 120       // target frame rate for scrolling (30-240)
}
```

**Speed Guide:**
- `0.5` pixels/frame = slow smooth scroll
- `1.0` pixels/frame = moderate scroll (recommended)
- `2.0` pixels/frame = fast scroll

**Frame Rate:**
- Higher FPS = smoother scrolling but more CPU usage
- 120 FPS is typically optimal for LED matrix displays

## Removed Code

The following manual scroll management code has been removed:
- `self.scroll_position` - Now managed by ScrollHelper
- `self.last_scroll_time` - Time calculations handled by ScrollHelper
- Manual `scroll_position` calculations in display loop
- Time-based scroll logic

## Benefits

✅ **Smoother Scrolling**: Frame-based movement is more consistent on LED displays
✅ **Better Performance**: ScrollHelper uses numpy arrays for efficient image slicing
✅ **Automatic FPS Sync**: Respects target FPS settings automatically
✅ **Easier Maintenance**: Less manual scroll management code
✅ **Better Error Handling**: More robust fallbacks when scrolling fails
✅ **Frame Rate Monitoring**: Built-in FPS logging for debugging

## Testing Recommendations

1. Test scrolling with different `scroll_speed` values
2. Verify FPS logs appear every 5 seconds when scrolling is enabled
3. Test message transitions during active scrolling
4. Test with `scroll.enabled: false` to verify static display works
5. Test runtime config changes with `on_config_change()`

## Troubleshooting

If scrolling still doesn't work:
1. Check that `ScrollHelper` is imported correctly
2. Verify display_manager has `width` and `height` attributes
3. Look for errors in `_create_scroll_cache()` logging
4. Ensure your config has `scroll.enabled: true`
5. Check that text width exceeds display width (otherwise text displays static)
