# Scrolling Test Guide

## Quick Validation

To test if scrolling is working correctly:

### 1. Check Configuration
Ensure your config has scrolling enabled:
```json
{
  "trevor-world": {
    "scroll": {
      "enabled": true,
      "speed": 1,
      "delay": 0.01,
      "gap_width": 32
    },
    "messages": [
      {
        "message": "This is a very long message that should definitely scroll across the display",
        "display_duration": 10,
        "color": [255, 255, 255]
      }
    ]
  }
}
```

**Key Points:**
- `scroll.enabled` must be `true`
- Message text must be longer than display width (usually 128 pixels)
- `display_duration` should be long enough to see full scroll cycle (5-10 seconds minimum)

### 2. Verify in Logs

Look for these log messages:
```
INFO - plugin.trevor-world - Scroll settings: 1 px/frame, 0.01s delay = 100.0 px/s, target FPS: 120
INFO - plugin.trevor-world - Trevor's World plugin initialized with N messages
DEBUG - plugin.trevor-world - Scrolling enabled: message_width=456, display_width=128
DEBUG - plugin.trevor-world - Setting scrolling image in ScrollHelper
DEBUG - plugin.trevor-world - Scrolling display: pos=0.5
```

### 3. Expected Behavior

**Scrolling Working:**
- Text moves smoothly from right to left across display
- Text speed is consistent (1 pixel per frame at 120 FPS = ~120 pixels/second)
- Text repeats/loops after reaching the left edge
- No flickering or jumping

**If Not Working:**
- Text appears static or doesn't move
- Text position jumps erratically
- Message advances without displaying (timer issue)

### 4. Debug Checklist

- [ ] `scroll.enabled: true` in config
- [ ] Message text is wider than display (test with long message: "This is a very long test message with lots of text")
- [ ] Font is loading correctly (check logs for "Loaded TTF font")
- [ ] Display dimensions look correct (should be 128x32 or similar)
- [ ] No exceptions in logs starting with "ERROR"
- [ ] ScrollHelper messages in logs indicate image was set

### 5. Common Issues

**Issue: Text doesn't scroll**
- Check if message is actually wider than display
- Verify `scroll.enabled: true`
- Look for error logs about cache creation

**Issue: Text jumps/glitches**
- This is usually the float vs int issue which has been fixed
- Check logs for "Failed to create scroll cache"

**Issue: Very slow scrolling**
- Check `scroll.speed` value (default 1 is normal)
- Check `target_fps` (higher = smoother but slower perceived speed)
- Note: 1 pixel/frame at 120 FPS = 120 pixels/second, which is quite fast

**Issue: Text not visible at all**
- Font might not be loading
- Display manager might not be initialized
- Check for "Font not loaded" or "Error during display" messages

---

## Performance Notes

- **Frame Rate:** 120 FPS is recommended (smoother scrolling)
- **CPU Impact:** Minimal with ScrollHelper (numpy-based, 6-10x faster than PIL)
- **Memory:** Cache image is ~130KB for typical display (128x32)

---

## Recent Fixes (v1.2.2)

- ✅ Fixed float-to-int conversion errors
- ✅ Simplified `update()` method to only update scroll position
- ✅ Improved debug logging in `display()` method
- ✅ Better error handling for cache creation
