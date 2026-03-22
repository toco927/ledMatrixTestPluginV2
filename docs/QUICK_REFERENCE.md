# Quick Reference: ScrollHelper Implementation

## What Changed in 30 Seconds

Your scrolling now uses **ScrollHelper** - a robust utility class that handles all the complex scroll position tracking automatically.

### The Old Way (Manual)
```python
self.scroll_position += self.scroll_speed  # Update manually
visible = self.text_image_cache.crop((int(self.scroll_position), 0, ...))  # Crop manually
```

### The New Way (ScrollHelper)
```python
self.scroll_helper.update_scroll_position()  # Update automatically
visible_image = self.scroll_helper.get_visible_portion()  # Crop automatically
```

---

## Configuration Format

```json
{
  "scroll": {
    "enabled": true,
    "speed": 1,
    "delay": 0.01,
    "gap_width": 32
  },
  "target_fps": 120
}
```

**Quick Settings:**
- Slow smooth scroll: `"speed": 0.5, "delay": 0.01`
- Normal scroll: `"speed": 1, "delay": 0.01`
- Fast scroll: `"speed": 2, "delay": 0.01`
- Super smooth: `"target_fps": 120` (higher = smoother, more CPU)

---

## Key Methods

| Method | Purpose | Called By |
|--------|---------|-----------|
| `update()` | Update scroll position | Display engine (each frame) |
| `display()` | Render current view | Display engine (each frame) |
| `_create_scroll_cache()` | Pre-render text to image | update() or display() |
| `_display_static_text()` | Render centered text | display() when not scrolling |
| `_log_frame_rate()` | Log FPS stats | display() when scrolling |

---

## Debugging

### Check These Logs
```
# Initialization
"Trevor's World plugin initialized with N messages"
"Config scroll_speed: X pixels/frame, scroll_delay: Y s"
"Scroll settings: X px/frame, Y s delay = Z px/s, target FPS: W"

# During scrolling
"Created scroll cache: WxH"
"Message scroll FPS - Avg: X, Current: Y, Frame time: Zms, Target: W FPS"

# Problems
"Failed to set scrolling image in ScrollHelper"
"ScrollHelper cached_image is None"
"Failed to create scroll cache: [error message]"
```

### Quick Fixes
| Problem | Fix |
|---------|-----|
| Not scrolling | Check `scroll.enabled: true` and text is wider than display |
| Jittery scrolling | Reduce `target_fps` or `scroll.speed` |
| Too slow/fast | Adjust `scroll.speed` (pixels per frame) |
| Message hangs | Check `display_duration` is long enough |
| High CPU | Reduce `target_fps` from 120 to 60 |

---

## Performance Tips

1. **Scroll Speed** (most impactful)
   - Smaller = smoother but slower
   - Larger = faster but may look jumpy
   - Sweet spot: 0.5 to 2 pixels/frame

2. **Frame Rate** (balances smooth vs. CPU)
   - 60 FPS = minimum, uses less CPU
   - 120 FPS = recommended for LED matrix
   - 240 FPS = maximum smoothness, more CPU

3. **Scroll Delay** (fine-tuning)
   - 0.01 = 100 FPS throttle (works with target_fps)
   - Smaller = more FPS attempts, smoother if system can handle
   - Larger = less CPU, but may limit smoothness

---

## Common Configurations

### Slow, Smooth (Default)
```json
{ "scroll": { "speed": 1, "delay": 0.01 }, "target_fps": 120 }
```

### Fast Ticker
```json
{ "scroll": { "speed": 2, "delay": 0.01 }, "target_fps": 120 }
```

### Low-CPU Smooth
```json
{ "scroll": { "speed": 1, "delay": 0.02 }, "target_fps": 60 }
```

### Very Smooth (High Performance)
```json
{ "scroll": { "speed": 0.5, "delay": 0.005 }, "target_fps": 240 }
```

---

## New Features

✅ **FPS Monitoring** - Logs average FPS every 5 seconds
✅ **Frame-Based Scrolling** - Consistent movement regardless of load
✅ **Automatic Reset** - Scroll resets when message changes
✅ **Error Recovery** - Validates cache and re-sets if needed
✅ **Configurable FPS** - Target frame rate setting

---

## Files Modified

- `manager.py` - Main plugin file (completely updated)

## Files Created

- `UPDATE_SUMMARY.md` - This update overview
- `SCROLLING_IMPROVEMENTS.md` - Detailed technical guide
- `BEFORE_AFTER_COMPARISON.md` - Before/after comparison

---

## Import Changes

**Added:**
```python
import logging
from typing import Dict, Any
from src.common.scroll_helper import ScrollHelper

logger = logging.getLogger(__name__)
```

**Removed:**
- Manual scroll position tracking code
- Time calculation imports (now in ScrollHelper)

---

## That's It! 🎉

Your plugin now uses professional scrolling. Just:
1. Test it with your config
2. Watch the FPS logs to verify performance
3. Adjust `scroll.speed` if needed

Questions? Check `SCROLLING_IMPROVEMENTS.md` for more details!
