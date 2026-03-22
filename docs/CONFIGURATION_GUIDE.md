# Configuration Guide - Trevor's World Plugin v1.2.0

## Overview

Trevor's World plugin now uses **ScrollHelper** with frame-based scrolling for smooth, professional animation. This guide explains all configuration options.

---

## Basic Configuration

### Minimal Setup
```json
{
  "trevor-world": {
    "enabled": true,
    "messages": [
      { "message": "Hello World" }
    ]
  }
}
```

### Full Setup with Scrolling
```json
{
  "trevor-world": {
    "enabled": true,
    "color": [255, 255, 255],
    "message_font_size": 10,
    "display_duration": 5,
    "target_fps": 120,
    "scroll": {
      "enabled": true,
      "speed": 1,
      "delay": 0.01,
      "gap_width": 32
    },
    "messages": [
      {
        "message": "Message 1",
        "display_duration": 5,
        "color": [255, 255, 255]
      }
    ]
  }
}
```

---

## Configuration Parameters

### Top-Level Settings

#### `enabled` (boolean)
- **Default:** `true`
- **Description:** Enable/disable the plugin
- **Example:** `"enabled": true`

#### `color` (RGB array)
- **Default:** `[255, 255, 255]` (white)
- **Description:** Default text color for all messages
- **Format:** `[Red, Green, Blue]` where each is 0-255
- **Example:** `"color": [0, 255, 0]` for green

#### `message_font_size` (integer)
- **Default:** `10`
- **Range:** 1-100
- **Description:** Font size in pixels
- **Example:** `"message_font_size": 12`

#### `font_family` (string)
- **Default:** `"press_start"`
- **Options:** `"press_start"`, `"four_by_six"`, `"tom_thumb"`, `"tiny"`, `"picopixel"`
- **Description:** Font family to use
- **Example:** `"font_family": "press_start"`

#### `display_duration` (number)
- **Default:** `5`
- **Range:** 1-300 seconds
- **Description:** Default display time for each message (can be overridden per-message)
- **Example:** `"display_duration": 4`

#### `target_fps` (number) ⭐ **NEW in v1.2.0**
- **Default:** `120`
- **Range:** 30-240
- **Description:** Target frame rate for smooth scrolling
  - 60 FPS: Lower CPU usage, acceptable smoothness
  - 120 FPS: Recommended default for LED displays
  - 240 FPS: Maximum smoothness, higher CPU
- **Example:** `"target_fps": 120`

#### `font_path` (string)
- **Default:** `"assets/fonts/PressStart2P-Regular.ttf"`
- **Description:** Path to custom font file (relative to project root)
- **Example:** `"font_path": "assets/fonts/CustomFont.ttf"`

---

### Scroll Settings

#### `scroll.enabled` (boolean)
- **Default:** `false`
- **Description:** Enable scrolling for messages wider than display
- **Note:** Text narrower than display will always center, never scroll
- **Example:** `"enabled": true`

#### `scroll.speed` (number) ⭐ **Frame-Based in v1.2.0**
- **Default:** `1`
- **Range:** 0.1-50
- **Description:** Pixels to move per frame
- **Examples:**
  - `0.5` - Slow, smooth scroll
  - `1.0` - Normal, balanced (RECOMMENDED)
  - `2.0` - Fast scroll
  - `3.0+` - Very fast, may look jumpy
- **Calculation:** `pixels_per_second = speed ÷ delay`
  - Example: 1px/frame ÷ 0.01s = 100 px/s

#### `scroll.delay` (number)
- **Default:** `0.01`
- **Range:** 0.001-0.1
- **Description:** Seconds per frame (throttling)
- **Common Values:**
  - `0.005` - 200 FPS throttle (very smooth, more CPU)
  - `0.01` - 100 FPS throttle (smooth, moderate CPU) **RECOMMENDED**
  - `0.02` - 50 FPS throttle (acceptable, less CPU)
  - `0.033` - 30 FPS throttle (minimum acceptable)
- **Interaction:** Works with `target_fps` to control smoothness

#### `scroll.gap_width` (number)
- **Default:** `32`
- **Range:** 0+
- **Description:** Pixels of space between message loops
- **Example:** `"gap_width": 16` for tighter looping

---

## Message Array

Each message in the messages array can have:

### Message Properties

#### `message` (string) - REQUIRED
- **Range:** 1-100 characters
- **Description:** Text to display (random number 1-10 will be appended)
- **Example:** `"message": "Hello Trevor"`

#### `display_duration` (number) - OPTIONAL
- **Default:** Uses top-level `display_duration` if not specified
- **Range:** 0.5-300 seconds
- **Description:** How long to display this specific message
- **Example:** `"display_duration": 3`

#### `color` (RGB array) - OPTIONAL
- **Default:** Uses top-level `color` if not specified
- **Format:** `[Red, Green, Blue]` (0-255 each)
- **Description:** Color override for this specific message
- **Example:** `"color": [255, 0, 0]` for red

---

## Configuration Examples

### Example 1: Simple Static Messages (No Scrolling)
```json
{
  "trevor-world": {
    "enabled": true,
    "color": [255, 255, 255],
    "display_duration": 3,
    "scroll": {
      "enabled": false
    },
    "messages": [
      { "message": "Line 1" },
      { "message": "Line 2" }
    ]
  }
}
```

### Example 2: Scrolling with Smooth Animation
```json
{
  "trevor-world": {
    "enabled": true,
    "color": [255, 255, 255],
    "display_duration": 5,
    "target_fps": 120,
    "scroll": {
      "enabled": true,
      "speed": 0.5,
      "delay": 0.01,
      "gap_width": 32
    },
    "messages": [
      { "message": "Very smooth scrolling animation" }
    ]
  }
}
```

### Example 3: Fast Ticker Board
```json
{
  "trevor-world": {
    "enabled": true,
    "color": [255, 100, 0],
    "display_duration": 2,
    "target_fps": 120,
    "scroll": {
      "enabled": true,
      "speed": 2,
      "delay": 0.01,
      "gap_width": 16
    },
    "messages": [
      { "message": "Stock Price Alert", "color": [0, 255, 0] },
      { "message": "Breaking News", "color": [255, 0, 0] }
    ]
  }
}
```

### Example 4: Low CPU Mode
```json
{
  "trevor-world": {
    "enabled": true,
    "color": [255, 255, 255],
    "display_duration": 5,
    "target_fps": 60,
    "scroll": {
      "enabled": true,
      "speed": 1,
      "delay": 0.02,
      "gap_width": 32
    },
    "messages": [
      { "message": "Lower CPU usage" }
    ]
  }
}
```

### Example 5: Per-Message Customization
```json
{
  "trevor-world": {
    "enabled": true,
    "color": [255, 255, 255],
    "display_duration": 5,
    "target_fps": 120,
    "scroll": {
      "enabled": true,
      "speed": 1,
      "delay": 0.01
    },
    "messages": [
      {
        "message": "Red Message",
        "display_duration": 3,
        "color": [255, 0, 0]
      },
      {
        "message": "Green Message",
        "display_duration": 4,
        "color": [0, 255, 0]
      },
      {
        "message": "Blue Message",
        "display_duration": 2,
        "color": [0, 0, 255]
      }
    ]
  }
}
```

---

## Performance Tuning

### Optimize for CPU (Lower Power)
```json
{
  "target_fps": 60,
  "scroll": {
    "speed": 1,
    "delay": 0.02
  }
}
```
**Result:** ~0.2ms per frame, 50 FPS actual

### Optimize for Smoothness (High Quality)
```json
{
  "target_fps": 240,
  "scroll": {
    "speed": 0.5,
    "delay": 0.005
  }
}
```
**Result:** ~0.5ms per frame, 200+ FPS actual, very smooth

### Balanced (Recommended)
```json
{
  "target_fps": 120,
  "scroll": {
    "speed": 1,
    "delay": 0.01
  }
}
```
**Result:** ~0.3ms per frame, 100+ FPS actual, good balance

---

## Migration from v1.1.x to v1.2.0

### What Changed
- ScrollHelper integration for better performance
- Frame-based scrolling (pixels per frame)
- Added `target_fps` parameter
- Improved descriptions and documentation

### Backward Compatibility
✅ Old configurations still work
✅ Automatic adaptation to frame-based system
✅ No breaking changes

### Recommended Updates
1. Add `"target_fps": 120` to config
2. Set `"scroll.enabled": true` if you want scrolling
3. Adjust `speed` and `delay` for your preference

---

## Troubleshooting Configuration

### Text Not Scrolling
**Check:**
- `scroll.enabled` is `true`
- Message is wider than display width
- `scroll.speed` > 0

### Scrolling Too Fast/Slow
**Adjust:** `scroll.speed` value
- Slower: reduce from 1 to 0.5
- Faster: increase from 1 to 2

### Visual Jitter or Tearing
**Adjust:** `target_fps` value
- Lower: reduce from 120 to 60
- Increase delay: from 0.01 to 0.02

### High CPU Usage
**Reduce:** `target_fps` or increase `delay`
- Try: `target_fps: 60` or `delay: 0.02`

### FPS Logs Not Appearing
**Ensure:**
- Scrolling is enabled and text is wider than display
- Wait 5+ seconds (logs appear every 5 seconds)
- Check logger level is set to INFO or DEBUG

---

## Complete Configuration Reference

```json
{
  "trevor-world": {
    "enabled": true,
    "color": [255, 255, 255],
    "message_font_size": 10,
    "font_family": "press_start",
    "font_path": "assets/fonts/PressStart2P-Regular.ttf",
    "display_duration": 5,
    "target_fps": 120,
    "scroll": {
      "enabled": true,
      "speed": 1,
      "delay": 0.01,
      "gap_width": 32
    },
    "messages": [
      {
        "message": "Message text",
        "display_duration": 5,
        "color": [255, 255, 255]
      }
    ]
  }
}
```

---

**Version:** 1.2.0
**Last Updated:** March 21, 2026
**Status:** Production Ready
