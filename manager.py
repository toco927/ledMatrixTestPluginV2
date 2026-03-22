"""
Trevor's World Plugin

A simple message queue plugin that displays a list of messages
on the LED matrix with a random number (1-10) appended to each.
Each message displays for its configured duration before cycling to the next.
"""

import logging
import os
import time
import random
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

from src.plugin_system.base_plugin import BasePlugin
from src.common.scroll_helper import ScrollHelper

logger = logging.getLogger(__name__)


class TrevorWorldPlugin(BasePlugin):
    """
    Trevor's World plugin for LEDMatrix.
    
    Displays messages from a list with a random number (1-10) appended.
    Each message displays for its configured duration, then cycles to the next.
    """
    
    def __init__(self, plugin_id, config, display_manager, cache_manager, plugin_manager):
        """Initialize the Trevor's World plugin."""
        super().__init__(plugin_id, config, display_manager, cache_manager, plugin_manager)

        # Message list
        self.messages = config.get('messages', [])
        
        # Display settings
        self.font_family = config.get('font_family', 'press_start')
        self.message_font_size = config.get('message_font_size', 10)
        self.color = tuple(config.get('color', [255, 255, 255]))
        self.default_display_duration = config.get('display_duration', 5)
        
        # Scrolling settings (universal for all messages)
        scroll_config = config.get('scroll', {})
        self.scroll_enabled = scroll_config.get('enabled', False)
        self.scroll_speed = float(scroll_config.get('speed', 1))  # pixels per frame
        self.scroll_delay = float(scroll_config.get('delay', 0.01))  # seconds per frame
        self.target_fps = float(config.get('target_fps', 120))  # target FPS for smooth scrolling
        self.scroll_gap_width = scroll_config.get('gap_width', 32)  # pixels between loop
        
        # Queue state
        self.current_message_index = 0
        self.message_start_time = time.time()
        self.current_random_number = self._generate_random_number()
        self.current_message = ""
        self.current_message_color = self.color
        self.current_display_duration = self.default_display_duration
        
        # Font and rendering
        self.font = None
        self.message_width = 0
        self.message_height = 0
        self.text_image_cache = None
        
        # Frame rate tracking for FPS logging
        self.frame_count = 0
        self.last_frame_time = None
        self.last_fps_log_time = None
        self.frame_times = []
        
        # Load font and set up first message
        self._load_font()
        self._load_current_message()
        
        # Initialize ScrollHelper for scrolling functionality
        display_width = self.display_manager.width if hasattr(self.display_manager, 'width') else 128
        display_height = self.display_manager.height if hasattr(self.display_manager, 'height') else 32
        self.scroll_helper = ScrollHelper(display_width, display_height, logger=self.logger)
        
        # Configure ScrollHelper with plugin settings
        if hasattr(self.scroll_helper, 'set_frame_based_scrolling'):
            self.scroll_helper.set_frame_based_scrolling(True)
            self.logger.info(f"Config scroll_speed: {self.scroll_speed} pixels/frame, scroll_delay: {self.scroll_delay}s")
            self.scroll_helper.set_scroll_speed(self.scroll_speed)
            if self.scroll_helper.scroll_speed != self.scroll_speed:
                self.logger.warning(
                    f"scroll_speed was clamped from {self.scroll_speed} to {self.scroll_helper.scroll_speed} pixels/frame"
                )
        else:
            pixels_per_second = self.scroll_speed / self.scroll_delay if self.scroll_delay > 0 else self.scroll_speed * 100
            self.scroll_helper.set_scroll_speed(pixels_per_second)
        
        self.scroll_helper.set_scroll_delay(self.scroll_delay)
        
        # Set target FPS from config (clamp to valid range)
        target_fps = max(30.0, min(240.0, self.target_fps))
        self.scroll_helper.set_target_fps(target_fps)
        
        # Calculate pixels per second for logging
        pixels_per_second = self.scroll_speed / self.scroll_delay if self.scroll_delay > 0 else self.scroll_speed * 100
        self.logger.info(f"Scroll settings: {self.scroll_speed} px/frame, {self.scroll_delay}s delay = {pixels_per_second:.1f} px/s, target FPS: {target_fps}")
        
        self.logger.info(f"Trevor's World plugin initialized with {len(self.messages)} messages")

    def _generate_random_number(self):
        """Generate a random integer between 1 and 10."""
        return random.randint(1, 10)

    def _load_font(self):
        """Load the font for text rendering."""
        font_path = self.config.get('font_path', 'assets/fonts/PressStart2P-Regular.ttf')
        font_size = self.message_font_size
        
        # Resolve relative paths to project root
        if not os.path.isabs(font_path):
            resolved_path = None
            
            # Strategy 1: Try as-is (if running from project root)
            if os.path.exists(font_path):
                resolved_path = font_path
            else:
                # Strategy 2: Try relative to current working directory
                cwd_path = os.path.join(os.getcwd(), font_path)
                if os.path.exists(cwd_path):
                    resolved_path = cwd_path
                else:
                    # Strategy 3: Try relative to plugin directory's parent (project root)
                    plugin_dir = Path(__file__).parent
                    project_root = plugin_dir.parent.parent
                    project_path = project_root / font_path
                    if project_path.exists():
                        resolved_path = str(project_path)
            
            if resolved_path:
                font_path = resolved_path
            else:
                self.logger.warning(f"Font file not found: {font_path}, using default")
                self.font = ImageFont.load_default()
                return
        
        if not os.path.exists(font_path):
            self.logger.warning(f"Font file not found: {font_path}, using default")
            self.font = ImageFont.load_default()
            return
        
        try:
            if font_path.lower().endswith('.ttf'):
                self.font = ImageFont.truetype(font_path, font_size)
                self.logger.info(f"Loaded TTF font: {font_path} at size {font_size}")
            else:
                self.logger.warning(f"Unsupported font type: {font_path}, using default")
                self.font = ImageFont.load_default()
        except Exception as e:
            self.logger.error(f"Failed to load font {font_path}: {e}")
            self.font = ImageFont.load_default()

    def _load_current_message(self):
        """Load the current message from the list."""
        if not self.messages:
            self.current_message = "No messages"
            self.current_message_color = self.color
            self.current_display_duration = self.default_display_duration
            return
        
        # Clamp index to valid range, and loop
        if self.current_message_index >= len(self.messages):
            self.current_message_index = 0
        
        msg_obj = self.messages[self.current_message_index]
        
        # Extract message text
        self.current_message = msg_obj.get('message', 'Empty Message')
        
        # Extract color (default to plugin's color)
        msg_color = msg_obj.get('color', self.color)
        self.current_message_color = tuple(msg_color) if msg_color else self.color
        
        # Extract display duration (default to plugin's default)
        self.current_display_duration = msg_obj.get('display_duration', self.default_display_duration)
        
        # Reset message timer and generate new random number
        self.message_start_time = time.time()
        self.current_random_number = self._generate_random_number()
        
        self.logger.debug(f"Loaded message {self.current_message_index}: '{self.current_message}' (random: {self.current_random_number})")

    def _calculate_text_dimensions(self):
        """Calculate text width/height for centering."""
        if not self.font:
            self.message_width = len(self.current_message) * 8
            self.message_height = 10
            return
        
        try:
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Add random number to message for width calculation
            display_text = f"{self.current_message} {self.current_random_number}"
            
            bbox = temp_draw.textbbox((0, 0), display_text, font=self.font)
            self.message_width = bbox[2] - bbox[0]
            self.message_height = bbox[3] - bbox[1]
            
            self.logger.debug(f"Text dimensions: {self.message_width}x{self.message_height}")
        except Exception as e:
            self.logger.warning(f"Could not calculate text dimensions: {e}")
            self.message_width = len(self.current_message) * 8
            self.message_height = 10

    def _create_scroll_cache(self):
        """Create a cached image for scrolling text using ScrollHelper."""
        if not self.font or not self.message_width:
            return
        
        try:
            width = self.display_manager.width
            height = self.display_manager.height
            display_text = f"{self.current_message} {self.current_random_number}"
            
            # Cache width: display + message + display + gap
            cache_width = width + self.message_width + width + self.scroll_gap_width
            self.text_image_cache = Image.new('RGB', (cache_width, height), (0, 0, 0))
            draw = ImageDraw.Draw(self.text_image_cache)
            
            # Calculate vertical centering
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), display_text, font=self.font)
            text_height = bbox[3] - bbox[1]
            y_pos = (height - text_height) // 2 - bbox[1]
            
            # Draw text starting after the initial display_width padding
            draw.text((width, y_pos), display_text, font=self.font, fill=self.current_message_color)
            
            # Ensure image is in RGB mode
            if self.text_image_cache.mode != 'RGB':
                self.text_image_cache = self.text_image_cache.convert('RGB')
            
            # Set the scrolling image in ScrollHelper
            self.scroll_helper.set_scrolling_image(self.text_image_cache)
            
            # Verify it was set correctly
            if self.scroll_helper.cached_image is None:
                self.logger.error("Failed to set scrolling image in ScrollHelper")
            
            self.logger.debug(f"Created scroll cache: {cache_width}x{height}")
        except Exception as e:
            self.logger.error(f"Failed to create scroll cache: {e}", exc_info=True)
            self.text_image_cache = None

    def _advance_to_next_message(self):
        """Move to the next message in the queue."""
        if not self.messages:
            return
        
        self.current_message_index += 1
        if self.current_message_index >= len(self.messages):
            self.current_message_index = 0
            self.logger.debug("Cycled back to first message")
        
        self._load_current_message()
        self._calculate_text_dimensions()
        self.text_image_cache = None  # Clear cache for new message
        if self.scroll_helper:
            self.scroll_helper.reset_scroll()  # Reset scroll position

    def update(self):
        """Update plugin - handle scroll position if scrolling is enabled."""
        if not self.scroll_enabled or self.message_width <= self.display_manager.width:
            # Reset scroll position if scrolling is disabled or text fits
            if self.scroll_helper:
                self.scroll_helper.reset_scroll()
            return
        
        # Ensure cache is created before updating scroll position
        if not self.text_image_cache:
            self._create_scroll_cache()
        
        # Use ScrollHelper to update scroll position
        if self.scroll_helper and self.text_image_cache:
            # Verify scroll_helper has the image set
            if self.scroll_helper.cached_image is None:
                self.logger.warning("ScrollHelper cached_image is None, re-setting scrolling image")
                self.scroll_helper.set_scrolling_image(self.text_image_cache)
            
            self.scroll_helper.update_scroll_position()

    def display(self, force_clear=False):
        """
        Render the plugin display.
        
        Displays the current message with appended random number (1-10).
        Supports scrolling if enabled. Handles message advancement timing.
        """
        try:
            if force_clear:
                self.display_manager.clear()
            
            # Check if current message display duration has elapsed
            time_since_message_start = time.time() - self.message_start_time
            if time_since_message_start > self.current_display_duration:
                self._advance_to_next_message()
            
            width = self.display_manager.width
            height = self.display_manager.height
            
            if not self.font:
                self.logger.error("Font not loaded, cannot display")
                return
            
            # Build display text: message + random number
            display_text = f"{self.current_message} {self.current_random_number}"
            
            # Handle scrolling if enabled and text is wider than display
            if self.scroll_enabled and self.message_width > width:
                # Create cache if needed
                if not self.text_image_cache:
                    self._create_scroll_cache()
                
                if self.text_image_cache and self.scroll_helper:
                    # Verify scroll_helper has the image set
                    if self.scroll_helper.cached_image is None:
                        self.logger.warning("ScrollHelper cached_image is None in display(), re-setting scrolling image")
                        self.scroll_helper.set_scrolling_image(self.text_image_cache)
                    
                    # Get visible portion from ScrollHelper
                    visible_image = self.scroll_helper.get_visible_portion()
                    
                    if visible_image:
                        # Ensure display_manager.image exists and is the right size
                        if not hasattr(self.display_manager, 'image') or self.display_manager.image is None:
                            self.display_manager.image = Image.new('RGB', (width, height), (0, 0, 0))
                        
                        # Update display with visible portion
                        self.display_manager.image.paste(visible_image, (0, 0))
                        self.display_manager.update_display()
                        
                        # Log frame rate for scrolling text
                        self._log_frame_rate()
                        
                        self.logger.debug(f"Displayed visible portion: scroll_position={self.scroll_helper.scroll_position:.2f}")
                    else:
                        self.logger.warning("ScrollHelper.get_visible_portion() returned None")
                        # Fallback to static display
                        self._display_static_text(display_text, width, height)
                else:
                    # Fallback: static text if cache creation failed
                    self._display_static_text(display_text, width, height)
            else:
                # Static text (centered)
                self._display_static_text(display_text, width, height)
            
        except Exception as e:
            self.logger.error(f"Error during display: {e}", exc_info=True)
    
    def _display_static_text(self, text, width, height):
        """Helper method to display static (non-scrolling) text."""
        try:
            img = Image.new('RGB', (width, height), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Calculate text dimensions for centering
            bbox = draw.textbbox((0, 0), text, font=self.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center text on display
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw the text
            draw.text((x, y), text, font=self.font, fill=self.current_message_color)
            
            # Update display
            self.display_manager.image = img
            self.display_manager.update_display()
        except Exception as e:
            self.logger.error(f"Error displaying static text: {e}")
    
    def _log_frame_rate(self):
        """Log frame rate statistics for scrolling text."""
        if not self.scroll_enabled:
            return
        
        current_time = time.time()
        
        # Initialize timing on first call
        if self.last_frame_time is None:
            self.last_frame_time = current_time
            self.last_fps_log_time = current_time
            return
        
        # Calculate instantaneous frame time
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        
        # Keep only last 100 frames for average
        if len(self.frame_times) > 100:
            self.frame_times.pop(0)
        
        # Log FPS every 5 seconds to avoid spam
        if current_time - self.last_fps_log_time >= 5.0:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times) if self.frame_times else frame_time
            avg_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            instant_fps = 1.0 / frame_time if frame_time > 0 else 0
            
            self.logger.info(
                f"Message scroll FPS - Avg: {avg_fps:.1f}, Current: {instant_fps:.1f}, "
                f"Frame time: {frame_time*1000:.2f}ms, Target: {self.target_fps:.0f} FPS"
            )
            self.last_fps_log_time = current_time
            self.frame_count = 0
        
        self.last_frame_time = current_time
        self.frame_count += 1

    def on_config_change(self, new_config):
        """Handle configuration changes at runtime."""
        super().on_config_change(new_config)
        
        # Update message list
        new_messages = new_config.get('messages', self.messages)
        if new_messages != self.messages:
            self.messages = new_messages
            self.current_message_index = 0
            self._load_current_message()
            self.text_image_cache = None
            if self.scroll_helper:
                self.scroll_helper.reset_scroll()
            self.logger.info(f"Messages updated: {len(self.messages)} messages loaded")
        
        # Update colors
        new_color = new_config.get('color', self.color)
        self.color = tuple(new_color) if new_color else self.color
        
        # Update font settings
        old_font_size = self.message_font_size
        self.message_font_size = new_config.get('message_font_size', self.message_font_size)
        if self.message_font_size != old_font_size:
            self._load_font()
        
        # Update display duration
        self.default_display_duration = new_config.get('display_duration', self.default_display_duration)
        
        # Update scroll settings
        scroll_config = new_config.get('scroll', {})
        old_scroll_enabled = self.scroll_enabled
        self.scroll_enabled = scroll_config.get('enabled', self.scroll_enabled)
        
        # Update ScrollHelper settings if scroll speed, delay, or target_fps changed
        new_scroll_speed = float(scroll_config.get('speed', self.scroll_speed))
        new_scroll_delay = float(scroll_config.get('delay', self.scroll_delay))
        new_target_fps = new_config.get('target_fps', self.target_fps)
        
        scroll_settings_changed = False
        if new_scroll_speed != self.scroll_speed:
            self.scroll_speed = new_scroll_speed
            scroll_settings_changed = True
        if new_scroll_delay != self.scroll_delay:
            self.scroll_delay = new_scroll_delay
            scroll_settings_changed = True
        if new_target_fps != self.target_fps:
            self.target_fps = float(new_target_fps)
            scroll_settings_changed = True
        
        if scroll_settings_changed and self.scroll_helper:
            if hasattr(self.scroll_helper, 'set_frame_based_scrolling'):
                self.scroll_helper.set_scroll_speed(self.scroll_speed)
            else:
                pixels_per_second = self.scroll_speed / self.scroll_delay if self.scroll_delay > 0 else self.scroll_speed * 100
                self.scroll_helper.set_scroll_speed(pixels_per_second)
            
            self.scroll_helper.set_scroll_delay(self.scroll_delay)
            target_fps = max(30.0, min(240.0, self.target_fps))
            self.scroll_helper.set_target_fps(target_fps)
            self.logger.info(f"Scroll settings updated: speed={self.scroll_speed}, delay={self.scroll_delay}s, target FPS={target_fps}")
        
        # Reset scroll position if scroll was toggled
        if old_scroll_enabled != self.scroll_enabled:
            if self.scroll_helper:
                self.scroll_helper.reset_scroll()
            self.text_image_cache = None
            self.logger.info(f"Scroll {'enabled' if self.scroll_enabled else 'disabled'}")
        
        self.scroll_gap_width = scroll_config.get('gap_width', self.scroll_gap_width)
        
        # Clear cache for new settings
        self.text_image_cache = None
        
        self._calculate_text_dimensions()
        self.logger.info("Configuration updated")

    def validate_config(self):
        """Validate plugin configuration."""
        if not super().validate_config():
            return False
        
        # Validate messages array
        if 'messages' in self.config:
            if not isinstance(self.config['messages'], list):
                self.logger.error("'messages' must be an array")
                return False
            
            if not self.config['messages']:
                self.logger.error("'messages' array cannot be empty")
                return False
            
            # Validate each message
            for idx, msg in enumerate(self.config['messages']):
                if not isinstance(msg, dict):
                    self.logger.error(f"messages[{idx}] must be an object")
                    return False
                
                # Required: message field
                if 'message' not in msg:
                    self.logger.error(f"messages[{idx}]: 'message' is required")
                    return False
                
                if not isinstance(msg['message'], str):
                    self.logger.error(f"messages[{idx}]['message'] must be a string")
                    return False
                
                if not (1 <= len(msg['message']) <= 100):
                    self.logger.error(f"messages[{idx}]['message'] must be between 1 and 100 characters")
                    return False
                
                # Optional: display_duration
                if 'display_duration' in msg:
                    try:
                        dur = float(msg['display_duration'])
                        if not (0.5 <= dur <= 300):
                            self.logger.error(f"messages[{idx}]['display_duration'] must be between 0.5 and 300")
                            return False
                    except (ValueError, TypeError):
                        self.logger.error(f"messages[{idx}]['display_duration'] must be a number")
                        return False
                
                # Optional: color override
                if 'color' in msg:
                    color = msg['color']
                    if not isinstance(color, (list, tuple)) or len(color) != 3:
                        self.logger.error(f"messages[{idx}]['color'] must be an RGB array [R, G, B]")
                        return False
                    if not all(isinstance(c, int) and 0 <= c <= 255 for c in color):
                        self.logger.error(f"messages[{idx}]['color'] values must be integers 0-255")
                        return False
        else:
            self.logger.error("'messages' array is required")
            return False
        
        # Validate colors
        if 'color' in self.config:
            color = self.config['color']
            if not isinstance(color, (list, tuple)) or len(color) != 3:
                self.logger.error("'color' must be an RGB array [R, G, B]")
                return False
            if not all(isinstance(c, int) and 0 <= c <= 255 for c in color):
                self.logger.error("'color' values must be integers 0-255")
                return False
        
        # Validate font size
        if 'message_font_size' in self.config:
            if not isinstance(self.config['message_font_size'], int):
                self.logger.error("'message_font_size' must be an integer")
                return False
            if not (1 <= self.config['message_font_size'] <= 100):
                self.logger.error("'message_font_size' must be between 1 and 100")
                return False
        
        # Validate display duration
        if 'display_duration' in self.config:
            try:
                duration = float(self.config['display_duration'])
                if not (1 <= duration <= 300):
                    self.logger.error("'display_duration' must be between 1 and 300 seconds")
                    return False
            except (ValueError, TypeError):
                self.logger.error("'display_duration' must be a number")
                return False
        
        # Validate scroll settings (universal, not per-message)
        if 'scroll' in self.config:
            scroll = self.config['scroll']
            if not isinstance(scroll, dict):
                self.logger.error("'scroll' must be an object")
                return False
            
            if 'enabled' in scroll:
                if not isinstance(scroll['enabled'], bool):
                    self.logger.error("'scroll.enabled' must be a boolean")
                    return False
            
            if 'speed' in scroll:
                try:
                    speed = float(scroll['speed'])
                    if not (0.1 <= speed <= 50):
                        self.logger.warning(f"'scroll.speed' {speed} is outside typical range 0.1-50")
                except (ValueError, TypeError):
                    self.logger.error("'scroll.speed' must be a number")
                    return False
            
            if 'delay' in scroll:
                try:
                    delay = float(scroll['delay'])
                    if not (0.001 <= delay <= 0.1):
                        self.logger.warning(f"'scroll.delay' {delay} is outside typical range 0.001-0.1")
                except (ValueError, TypeError):
                    self.logger.error("'scroll.delay' must be a number")
                    return False
            
            if 'gap_width' in scroll:
                try:
                    gap = float(scroll['gap_width'])
                    if gap < 0:
                        self.logger.error("'scroll.gap_width' must be non-negative")
                        return False
                except (ValueError, TypeError):
                    self.logger.error("'scroll.gap_width' must be a number")
                    return False
        
        self.logger.info("Configuration validated successfully")
        return True

    def get_info(self):
        """Return plugin information for web UI."""
        info = super().get_info()
        info.update({
            'current_message': self.current_message[:50],
            'random_number': self.current_random_number,
            'message_index': self.current_message_index,
            'total_messages': len(self.messages),
            'display_duration': self.current_display_duration,
            'scroll_enabled': self.scroll_enabled,
            'scroll_speed': self.scroll_speed,
            'scroll_delay': self.scroll_delay,
            'scroll_gap_width': self.scroll_gap_width,
        })
        return info

    def cleanup(self):
        """Cleanup resources when plugin is unloaded."""
        if self.scroll_helper:
            self.scroll_helper.clear_cache()
        self.text_image_cache = None
        self.logger.info("Cleaning up Trevor's World plugin")
        super().cleanup()

