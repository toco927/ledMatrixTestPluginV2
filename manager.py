"""
Trevor's World Plugin

A message queue plugin that displays a customizable list of messages
on the LED matrix with individual settings for each message.
Supports scrolling, custom colors, fonts, and persistence across restarts.
"""

from src.plugin_system.base_plugin import BasePlugin
import time
from datetime import datetime
import os
from pathlib import Path
import json

# --- Scrolling and caching additions ---
from PIL import Image, ImageDraw, ImageFont

try:
    import freetype
except ImportError:
    freetype = None


class TrevorWorldPlugin(BasePlugin):
    """
    Trevor's World plugin for LEDMatrix with message queue support.

    Displays messages from a queue with individual settings for each message.
    Supports scrolling, custom colors, fonts, and persists state across restarts.
    """
    
    def __init__(self, plugin_id, config, display_manager, cache_manager, plugin_manager):
        """Initialize the Trevor's World plugin with queue support."""
        super().__init__(plugin_id, config, display_manager, cache_manager, plugin_manager)

        # Queue mode configuration
        self.queue_mode = config.get('queue_mode', False)
        self.message_queue = config.get('message_queue', [])
        self.empty_queue_message = config.get('empty_queue_message', 'Queue Empty')
        self.cache_file = config.get('cache_file', '.trevor_world_queue_state')
        
        # Queue state
        self.current_queue_index = 0
        self.queue_complete = False
        self.message_start_time = time.time()
        self.message_change_pending = False
        
        # Default display settings (used as fallback for queue messages)
        self.show_time = config.get('show_time', True)
        self.font_family = config.get('font_family', 'press_start')
        self.message_font_size = config.get('message_font_size', 10)
        self.time_font_size = config.get('time_font_size', 8)
        self.color = tuple(config.get('color', [255, 255, 255]))
        self.time_color = tuple(config.get('time_color', [0, 255, 255]))
        
        # Handle scroll configuration - support both nested object and flat properties
        scroll_config = config.get('scroll', {})
        self.scroll_enabled = scroll_config.get('enabled', config.get('scroll_enabled', False))
        self.scroll_speed = float(scroll_config.get('speed', config.get('scroll_speed', 1)))
        self.scroll_delay = float(scroll_config.get('delay', config.get('scroll_delay', 0.01)))
        self.scroll_loop = scroll_config.get('loop', config.get('scroll_loop', True))
        self.scroll_gap_width = scroll_config.get('gap_width', config.get('scroll_gap_width', 32))
        
        self.display_duration = config.get('display_duration', 5)
        
        # Single message mode (non-queue)
        if not self.queue_mode:
            self.message = config.get('message', 'Trevor made this')
        else:
            self.message = ''  # Will be set from queue

        # Font/image cache
        self.font = None
        self.message_width = 0
        self.message_height = 0
        self.time_width = 0
        self.time_height = 0
        self.text_image_cache = None
        self.scroll_position = 0
        self.last_scroll_time = time.time()

        # State
        self.last_update = None
        self.current_time_str = ""
        self.message_start_time = time.time()  # Track when current message started

        # Load font and calculate dimensions
        self._load_font()
        self._calculate_text_dimensions()

        self.logger.info(f"Trevor's World plugin initialized (queue_mode={self.queue_mode})")
        
        if self.queue_mode:
            self._load_queue_state()
            self._load_current_message_settings()
            self.logger.info(f"Queue mode enabled with {len(self.message_queue)} messages")
        else:
            self.logger.info(f"Single message mode: '{self.message}'")

        # Register fonts
        self._register_fonts()

    def _register_fonts(self):
        """Register fonts with the font manager if available."""
        try:
            if not hasattr(self.plugin_manager, 'font_manager'):
                self.logger.debug("Font manager not available, skipping font registration")
                return

            font_manager = self.plugin_manager.font_manager
            if not font_manager:
                self.logger.debug("Font manager is None, skipping font registration")
                return

            # Message font
            font_manager.register_manager_font(
                manager_id=self.plugin_id,
                element_key=f"{self.plugin_id}.message",
                family="press_start",
                size_px=self.message_font_size,
                color=self.color
            )

            # Time font
            font_manager.register_manager_font(
                manager_id=self.plugin_id,
                element_key=f"{self.plugin_id}.time",
                family="press_start",
                size_px=self.time_font_size,
                color=self.time_color
            )

            self.logger.info("Trevor's World fonts registered successfully")
        except AttributeError as e:
            self.logger.debug(f"Font manager registration skipped: {e}")
        except Exception as e:
            self.logger.warning(f"Error registering fonts: {e}")

    def _get_cache_file_path(self):
        """Get the full path to the queue state cache file."""
        # Try to store in plugin directory, fallback to temp
        try:
            plugin_dir = Path(__file__).parent
            cache_path = plugin_dir / self.cache_file
            return cache_path
        except Exception:
            return Path(self.cache_file)

    def _load_queue_state(self):
        """Load saved queue state (last displayed message index)."""
        try:
            cache_path = self._get_cache_file_path()
            if cache_path.exists():
                with open(cache_path, 'r') as f:
                    state = json.load(f)
                    self.current_queue_index = state.get('current_index', 0)
                    self.queue_complete = state.get('queue_complete', False)
                    self.logger.info(f"Loaded queue state: index={self.current_queue_index}, complete={self.queue_complete}")
            else:
                self.current_queue_index = 0
                self.queue_complete = False
        except Exception as e:
            self.logger.warning(f"Could not load queue state: {e}, resetting to start")
            self.current_queue_index = 0
            self.queue_complete = False

    def _save_queue_state(self):
        """Save current queue state (for resuming after restart)."""
        try:
            cache_path = self._get_cache_file_path()
            # Ensure parent directory exists
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            state = {
                'current_index': self.current_queue_index,
                'queue_complete': self.queue_complete,
                'saved_at': datetime.now().isoformat()
            }
            with open(cache_path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save queue state: {e}")

    def _get_enabled_queue_messages(self):
        """Get list of enabled messages in order."""
        enabled = [msg for msg in self.message_queue if msg.get('enabled', True)]
        # Sort by order if provided
        try:
            enabled.sort(key=lambda x: x.get('order', self.message_queue.index(x)))
        except Exception:
            pass
        return enabled

    def _load_current_message_settings(self):
        """Load settings for the current queue message."""
        enabled_messages = self._get_enabled_queue_messages()
        
        if not enabled_messages:
            self.queue_complete = True
            self.message = self.empty_queue_message
            self.show_time = False
            self.scroll_enabled = False
            self.display_duration = 5
            self.logger.warning("Queue is empty or all messages disabled")
            return
        
        # Clamp index to valid range
        if self.current_queue_index >= len(enabled_messages):
            self.current_queue_index = len(enabled_messages) - 1
            self.queue_complete = True
        
        current_msg = enabled_messages[self.current_queue_index]
        
        # Load message-specific settings with fallback to defaults
        self.message = current_msg.get('message', 'Empty Message')
        self.message_font_size = current_msg.get('message_font_size', self.message_font_size)
        self.time_font_size = current_msg.get('time_font_size', self.time_font_size)
        self.color = tuple(current_msg.get('color', self.color))
        self.time_color = tuple(current_msg.get('time_color', self.time_color))
        self.show_time = current_msg.get('show_time', self.show_time)
        
        # Handle scroll configuration - support both nested object and flat properties
        msg_scroll = current_msg.get('scroll', {})
        self.scroll_enabled = msg_scroll.get('enabled', current_msg.get('scroll_enabled', self.scroll_enabled))
        self.scroll_speed = float(msg_scroll.get('speed', current_msg.get('scroll_speed', self.scroll_speed)))
        self.scroll_delay = float(msg_scroll.get('delay', current_msg.get('scroll_delay', self.scroll_delay)))
        
        self.display_duration = current_msg.get('display_duration', self.display_duration)
        
        self.logger.debug(f"Loaded queue message {self.current_queue_index}: '{self.message[:30]}...'")

    def _advance_queue(self):
        """Move to next message in queue."""
        enabled_messages = self._get_enabled_queue_messages()
        if not enabled_messages:
            self.queue_complete = True
            return
        
        self.current_queue_index += 1
        if self.current_queue_index >= len(enabled_messages):
            self.queue_complete = True
            self.logger.info("Queue complete, cycling back to start")
            # Reset for looping
            self.current_queue_index = 0
            self.queue_complete = False
        
        self._load_current_message_settings()
        self._save_queue_state()
        self.message_change_pending = False
        self.message_start_time = time.time()
        self.text_image_cache = None  # Clear cache for new message

    def _load_font(self):
        """Load the font for text rendering (TTF or BDF) with multiple fallback strategies."""
        font_path = self.config.get('font_path', 'assets/fonts/PressStart2P-Regular.ttf')
        font_size = self.message_font_size
        
        # Resolve relative paths to project root
        if not os.path.isabs(font_path):
            resolved_path = None
            
            # Strategy 1: Try as-is (if running from project root)
            if os.path.exists(font_path):
                resolved_path = font_path
            else:
                # Strategy 2: Try relative to current working directory (project root)
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
            elif font_path.lower().endswith('.bdf'):
                # BDF fonts need freetype
                if freetype is not None:
                    self.font = freetype.Face(font_path)
                    self.font.set_pixel_sizes(0, font_size)
                    self.logger.info(f"Loaded BDF font: {font_path} at size {font_size}")
                else:
                    self.logger.warning("freetype not available for BDF font, using default")
                    self.font = ImageFont.load_default()
            else:
                self.logger.warning(f"Unsupported font type: {font_path}, using default")
                self.font = ImageFont.load_default()
        except Exception as e:
            self.logger.error(f"Failed to load font {font_path}: {e}")
            self.font = ImageFont.load_default()

    def _calculate_text_dimensions(self):
        """Calculate message and time text width/height for centering and scrolling."""
        if not self.font:
            # Use fallback dimensions if font not loaded
            self.message_width = len(self.message) * 8
            self.message_height = 10
            self.time_width = len(self.current_time_str) * 8 if self.current_time_str else 0
            self.time_height = 10
            return
        
        try:
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Calculate message dimensions
            if isinstance(self.font, ImageFont.FreeTypeFont) or isinstance(self.font, ImageFont.ImageFont):
                bbox = temp_draw.textbbox((0, 0), self.message, font=self.font)
                self.message_width = bbox[2] - bbox[0]
                self.message_height = bbox[3] - bbox[1]
            else:
                # Default fallback for other font types
                self.message_width = len(self.message) * 8
                self.message_height = 10
            
            # Calculate time dimensions if we have a time string
            if self.current_time_str:
                try:
                    bbox_time = temp_draw.textbbox((0, 0), self.current_time_str, font=self.font)
                    self.time_width = bbox_time[2] - bbox_time[0]
                    self.time_height = bbox_time[3] - bbox_time[1]
                except Exception:
                    self.time_width = len(self.current_time_str) * 8
                    self.time_height = 10
            else:
                self.time_width = 0
                self.time_height = 0
        except Exception as e:
            self.logger.warning(f"Could not calculate text dimensions: {e}")
            self.message_width = len(self.message) * 8
            self.message_height = 10
            self.time_width = len(self.current_time_str) * 8 if self.current_time_str else 0
            self.time_height = 10

    def _create_text_cache(self):
        """Pre-render the message for scrolling."""
        if not self.message or self.message_width == 0 or not self.font:
            self.logger.warning("Cannot create text cache: message is empty, text_width is 0, or font not loaded")
            return
        try:
            width = self.display_manager.width
            height = self.display_manager.height
            cache_width = width + self.message_width + width + self.scroll_gap_width
            self.text_image_cache = Image.new('RGB', (cache_width, height), (0, 0, 0))
            draw = ImageDraw.Draw(self.text_image_cache)
            y_pos = (height - self.message_height) // 2
            draw.text((width, y_pos), self.message, font=self.font, fill=self.color)
            self.logger.info(f"Created text cache: {cache_width}x{height} (text: {self.message_width}px)")
        except Exception as e:
            self.logger.error(f"Failed to create text cache: {e}")
            self.text_image_cache = None

    def update(self):
        """Update plugin data and scroll position if scrolling is enabled."""
        try:
            self.last_update = time.time()
            
            # Queue advancement logic
            if self.queue_mode:
                time_since_message_start = time.time() - self.message_start_time
                if time_since_message_start > self.display_duration:
                    self._advance_queue()
            
            if self.show_time:
                now = datetime.now()
                new_time_str = now.strftime("%I:%M %p")
                
                # Only log if the time actually changed (reduces spam from sub-minute updates)
                if new_time_str != self.current_time_str:
                    self.current_time_str = new_time_str
                    self._calculate_text_dimensions()  # Recalculate time dimensions
                    # Only log time changes occasionally
                    if not hasattr(self, '_last_time_log') or time.time() - self._last_time_log > 60:
                        self.logger.info(f"Time updated: {self.current_time_str}")
                        self._last_time_log = time.time()
            
            # Scrolling update
            if self.scroll_enabled and self.message_width > self.display_manager.width:
                now = time.time()
                if now - self.last_scroll_time >= self.scroll_delay:
                    self.scroll_position += self.scroll_speed
                    cache_width = self.display_manager.width + self.message_width + self.display_manager.width + self.scroll_gap_width
                    if self.scroll_position > cache_width - self.display_manager.width:
                        if self.scroll_loop:
                            self.scroll_position = 0
                        else:
                            self.scroll_position = cache_width - self.display_manager.width
                    self.last_scroll_time = now
            else:
                self.scroll_position = 0
                
        except Exception as e:
            self.logger.error(f"Error during update: {e}", exc_info=True)
                    
    def display(self, force_clear=False):
        """
        Render the plugin display.
        
        Displays the configured message and optionally the current time.
        Supports both scrolling and static display modes.
        For queue mode, cycles through queued messages or shows empty message.
        """
        try:
            if force_clear:
                self.display_manager.clear()
            
            width = self.display_manager.width
            height = self.display_manager.height
            
            # Handle queue completion
            if self.queue_mode and self.queue_complete:
                # Show empty queue message - static display
                img = Image.new('RGB', (width, height), (0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # Measure and draw empty message
                try:
                    bbox = draw.textbbox((0, 0), self.empty_queue_message, font=self.font)
                    empty_width = bbox[2] - bbox[0]
                    empty_height = bbox[3] - bbox[1]
                except Exception:
                    empty_width = len(self.empty_queue_message) * 8
                    empty_height = 10
                
                msg_x = (width - empty_width) // 2
                msg_y = (height - empty_height) // 2
                
                try:
                    draw.text((msg_x, msg_y), self.empty_queue_message, font=self.font, fill=self.color)
                except Exception as e:
                    self.logger.error(f"Error drawing empty queue message: {e}")
                
                self.display_manager.image = img
                self.display_manager.update_display()
                return
            
            # Ensure font is loaded and dimensions are calculated
            if not self.font:
                self.logger.error("Font not loaded, cannot display")
                return
            
            if self.message_width == 0 or self.message_height == 0:
                self._calculate_text_dimensions()
            
            # --- Scrolling logic ---
            if self.scroll_enabled and self.message_width > width:
                if not self.text_image_cache:
                    self._create_text_cache()
                if self.text_image_cache:
                    # Get visible portion
                    x_offset = int(self.scroll_position)
                    visible = self.text_image_cache.crop((x_offset, 0, x_offset + width, height))
                    # Paste to display_manager.image if available, else fallback
                    if hasattr(self.display_manager, 'image') and self.display_manager.image is not None:
                        self.display_manager.image.paste(visible, (0, 0))
                    else:
                        # Fallback: draw directly
                        img = Image.new('RGB', (width, height), (0, 0, 0))
                        img.paste(visible, (0, 0))
                        self.display_manager.image = img
                    self.display_manager.update_display()
                else:
                    self.logger.warning("Text image cache not available for scrolling")
            else:
                # Centered message and time (static display)
                img = Image.new('RGB', (width, height), (0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # Draw message centered horizontally, in upper-middle area
                msg_x = (width - self.message_width) // 2
                msg_y = (height // 2) - (self.message_height // 2)
                
                # Use loaded font for drawing
                try:
                    draw.text((msg_x, msg_y), self.message, font=self.font, fill=self.color)
                except Exception as e:
                    self.logger.error(f"Error drawing message: {e}")
                
                # Draw time at bottom if enabled
                if self.show_time and self.current_time_str and self.time_width > 0 and self.time_height > 0:
                    time_x = (width - self.time_width) // 2
                    time_y = height - self.time_height
                    try:
                        draw.text((time_x, time_y), self.current_time_str, font=self.font, fill=self.time_color)
                    except Exception as e:
                        self.logger.error(f"Error drawing time: {e}")
                
                self.display_manager.image = img
                self.display_manager.update_display()
                
        except Exception as e:
            self.logger.error(f"Error during display: {e}", exc_info=True)
    
    def on_config_change(self, new_config):
        """Handle configuration changes at runtime."""
        super().on_config_change(new_config)
        
        # Handle queue configuration changes
        if self.queue_mode:
            new_queue = new_config.get('message_queue', self.message_queue)
            if new_queue != self.message_queue:
                self.message_queue = new_queue
                self.current_queue_index = 0
                self.queue_complete = False
                self._load_current_message_settings()
                self.text_image_cache = None
                self.scroll_position = 0
                self.message_start_time = time.time()
                self.logger.info(f"Queue configuration updated, resetting to first message")
            
            self.empty_queue_message = new_config.get('empty_queue_message', self.empty_queue_message)
        else:
            # Single message mode
            self.message = new_config.get('message', self.message)
        
        self.show_time = new_config.get('show_time', self.show_time)
        self.color = tuple(new_config.get('color', self.color))
        self.time_color = tuple(new_config.get('time_color', self.time_color))
        self.font_family = new_config.get('font_family', self.font_family)
        self.message_font_size = new_config.get('message_font_size', self.message_font_size)
        self.time_font_size = new_config.get('time_font_size', self.time_font_size)
        
        # Handle scroll configuration - support both nested object and flat properties
        scroll_config = new_config.get('scroll', {})
        self.scroll_enabled = scroll_config.get('enabled', new_config.get('scroll_enabled', self.scroll_enabled))
        self.scroll_speed = float(scroll_config.get('speed', new_config.get('scroll_speed', self.scroll_speed)))
        self.scroll_delay = float(scroll_config.get('delay', new_config.get('scroll_delay', self.scroll_delay)))
        self.scroll_loop = scroll_config.get('loop', new_config.get('scroll_loop', self.scroll_loop))
        self.scroll_gap_width = scroll_config.get('gap_width', new_config.get('scroll_gap_width', self.scroll_gap_width))
        
        # Reload font and recalculate dimensions
        self._load_font()
        self._calculate_text_dimensions()
        
        # Reset scrolling state
        self.text_image_cache = None
        self.scroll_position = 0
        
        self.logger.info(f"Configuration updated: message='{self.message[:20]}...', scroll_enabled={self.scroll_enabled}")

    def validate_config(self):
        """Validate plugin configuration."""
        if not super().validate_config():
            return False
        
        # Validate queue_mode
        if 'queue_mode' in self.config:
            if not isinstance(self.config['queue_mode'], bool):
                self.logger.error("'queue_mode' must be a boolean")
                return False
        
        queue_mode = self.config.get('queue_mode', False)
        
        # Validate message (required for single message mode, optional for queue mode)
        if 'message' in self.config:
            if not isinstance(self.config['message'], str):
                self.logger.error("'message' must be a string")
                return False
            if not (1 <= len(self.config['message']) <= 50):
                self.logger.error("'message' must be between 1 and 50 characters")
                return False
        elif not queue_mode:
            self.logger.error("'message' is required when queue_mode is false")
            return False
        
        # Validate colors
        for color_key in ['color', 'time_color']:
            if color_key in self.config:
                color = self.config[color_key]
                if not isinstance(color, (list, tuple)) or len(color) != 3:
                    self.logger.error(f"'{color_key}' must be an RGB array [R, G, B]")
                    return False
                if not all(isinstance(c, int) and 0 <= c <= 255 for c in color):
                    self.logger.error(f"'{color_key}' values must be integers 0-255")
                    return False
        
        # Validate show_time
        if 'show_time' in self.config:
            if not isinstance(self.config['show_time'], bool):
                self.logger.error("'show_time' must be a boolean")
                return False

        # Validate font sizes
        for size_key in ['message_font_size', 'time_font_size']:
            if size_key in self.config:
                if not isinstance(self.config[size_key], int):
                    self.logger.error(f"'{size_key}' must be an integer")
                    return False
                if not (1 <= self.config[size_key] <= 100):
                    self.logger.error(f"'{size_key}' must be between 1 and 100")
                    return False
        
        # Validate nested scroll configuration
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
                    if not (0.1 <= speed <= 10):
                        self.logger.warning(f"'scroll.speed' {speed} is outside typical range 0.1-10")
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
            
            if 'loop' in scroll:
                if not isinstance(scroll['loop'], bool):
                    self.logger.error("'scroll.loop' must be a boolean")
                    return False
            
            if 'gap_width' in scroll:
                try:
                    gap_width = float(scroll['gap_width'])
                    if gap_width < 0:
                        self.logger.error("'scroll.gap_width' must be non-negative")
                        return False
                except (ValueError, TypeError):
                    self.logger.error("'scroll.gap_width' must be a number")
                    return False
        
        # Validate display_duration
        if 'display_duration' in self.config:
            try:
                duration = float(self.config['display_duration'])
                if not (1 <= duration <= 300):
                    self.logger.error("'display_duration' must be between 1 and 300 seconds")
                    return False
            except (ValueError, TypeError):
                self.logger.error("'display_duration' must be a number")
                return False
        
        # Validate queue mode configuration
        if queue_mode:
            if 'message_queue' in self.config:
                if not isinstance(self.config['message_queue'], list):
                    self.logger.error("'message_queue' must be an array")
                    return False
                
                if not self.config['message_queue']:
                    self.logger.error("'message_queue' cannot be empty in queue_mode")
                    return False
                
                # Validate each message in the queue
                for idx, msg in enumerate(self.config['message_queue']):
                    if not isinstance(msg, dict):
                        self.logger.error(f"message_queue[{idx}] must be an object")
                        return False
                    
                    # Required: message field
                    if 'message' not in msg:
                        self.logger.error(f"message_queue[{idx}]: 'message' is required")
                        return False
                    
                    if not isinstance(msg['message'], str):
                        self.logger.error(f"message_queue[{idx}]['message'] must be a string")
                        return False
                    
                    if not (1 <= len(msg['message']) <= 100):
                        self.logger.error(f"message_queue[{idx}]['message'] must be between 1 and 100 characters")
                        return False
                    
                    # Validate optional fields
                    if 'display_duration' in msg:
                        try:
                            dur = float(msg['display_duration'])
                            if not (0.5 <= dur <= 300):
                                self.logger.error(f"message_queue[{idx}]['display_duration'] must be between 0.5 and 300")
                                return False
                        except (ValueError, TypeError):
                            self.logger.error(f"message_queue[{idx}]['display_duration'] must be a number")
                            return False
                    
                    if 'order' in msg:
                        if not isinstance(msg['order'], int) or msg['order'] < 0:
                            self.logger.error(f"message_queue[{idx}]['order'] must be a non-negative integer")
                            return False
                    
                    if 'enabled' in msg:
                        if not isinstance(msg['enabled'], bool):
                            self.logger.error(f"message_queue[{idx}]['enabled'] must be a boolean")
                            return False
                    
                    # Validate optional color overrides
                    for color_key in ['color', 'time_color']:
                        if color_key in msg:
                            color = msg[color_key]
                            if not isinstance(color, (list, tuple)) or len(color) != 3:
                                self.logger.error(f"message_queue[{idx}]['{color_key}'] must be an RGB array [R, G, B]")
                                return False
                            if not all(isinstance(c, int) and 0 <= c <= 255 for c in color):
                                self.logger.error(f"message_queue[{idx}]['{color_key}'] values must be integers 0-255")
                                return False
                    
                    # Validate optional boolean overrides
                    if 'show_time' in msg:
                        if not isinstance(msg['show_time'], bool):
                            self.logger.error(f"message_queue[{idx}]['show_time'] must be a boolean")
                            return False
                    
                    # Validate optional font size overrides
                    for size_key in ['message_font_size', 'time_font_size']:
                        if size_key in msg:
                            if not isinstance(msg[size_key], int):
                                self.logger.error(f"message_queue[{idx}]['{size_key}'] must be an integer")
                                return False
                            if not (1 <= msg[size_key] <= 100):
                                self.logger.error(f"message_queue[{idx}]['{size_key}'] must be between 1 and 100")
                                return False
                    
                    # Validate optional nested scroll override
                    if 'scroll' in msg:
                        msg_scroll = msg['scroll']
                        if not isinstance(msg_scroll, dict):
                            self.logger.error(f"message_queue[{idx}]['scroll'] must be an object")
                            return False
                        
                        if 'enabled' in msg_scroll:
                            if not isinstance(msg_scroll['enabled'], bool):
                                self.logger.error(f"message_queue[{idx}]['scroll']['enabled'] must be a boolean")
                                return False
                        
                        if 'speed' in msg_scroll:
                            try:
                                speed = float(msg_scroll['speed'])
                                if not (0.1 <= speed <= 10):
                                    self.logger.warning(f"message_queue[{idx}]['scroll']['speed'] {speed} is outside typical range 0.1-10")
                            except (ValueError, TypeError):
                                self.logger.error(f"message_queue[{idx}]['scroll']['speed'] must be a number")
                                return False
                        
                        if 'delay' in msg_scroll:
                            try:
                                delay = float(msg_scroll['delay'])
                                if not (0.001 <= delay <= 0.1):
                                    self.logger.warning(f"message_queue[{idx}]['scroll']['delay'] {delay} is outside typical range 0.001-0.1")
                            except (ValueError, TypeError):
                                self.logger.error(f"message_queue[{idx}]['scroll']['delay'] must be a number")
                                return False
            else:
                self.logger.error("'message_queue' is required when queue_mode is true")
                return False
            
            # Validate optional queue settings
            if 'empty_queue_message' in self.config:
                if not isinstance(self.config['empty_queue_message'], str):
                    self.logger.error("'empty_queue_message' must be a string")
                    return False
                if not (1 <= len(self.config['empty_queue_message']) <= 50):
                    self.logger.error("'empty_queue_message' must be between 1 and 50 characters")
                    return False
            
            if 'cache_file' in self.config:
                if not isinstance(self.config['cache_file'], str):
                    self.logger.error("'cache_file' must be a string")
                    return False
                if not self.config['cache_file']:
                    self.logger.error("'cache_file' cannot be empty")
                    return False

        self.logger.info("Configuration validated successfully")
        return True
    
    def get_display_duration(self):
        """Get display duration from config or calculate based on scroll settings."""
        # If scrolling is enabled and message is wider than display, calculate duration
        if self.scroll_enabled and self.message_width > self.display_manager.width:
            # Calculate time needed for text to scroll across
            # cache_width = display_width + message_width + display_width + gap
            cache_width = self.display_manager.width + self.message_width + self.display_manager.width + self.scroll_gap_width
            # frames_needed = cache_width / scroll_speed
            # time_needed = frames_needed * scroll_delay
            if self.scroll_speed > 0 and self.scroll_delay > 0:
                frames_needed = cache_width / self.scroll_speed
                duration = frames_needed * self.scroll_delay
                # Add buffer for looping (if enabled)
                if self.scroll_loop:
                    duration += 1.0  # 1 second buffer between loops
                return max(duration, 5.0)  # Minimum 5 seconds
        
        # Default display duration from config
        return self.config.get('display_duration', 10.0)
    
    def get_info(self):
        """Return plugin information for web UI."""
        info = super().get_info()
        # Calculate pixels per second for display
        pixels_per_second = self.scroll_speed / self.scroll_delay if self.scroll_delay > 0 else self.scroll_speed * 100
        info.update({
            'message': self.message[:50] if len(self.message) > 50 else self.message,
            'message_width': self.message_width,
            'message_height': self.message_height,
            'show_time': self.show_time,
            'current_time': self.current_time_str,
            'time_width': self.time_width,
            'time_height': self.time_height,
            'scroll_enabled': self.scroll_enabled,
            'scroll_speed': self.scroll_speed,  # pixels per frame
            'scroll_delay': self.scroll_delay,  # seconds per frame
            'scroll_loop': self.scroll_loop,
            'scroll_gap_width': self.scroll_gap_width,
            'pixels_per_second': round(pixels_per_second, 1),  # calculated from frame-based settings
            'display_duration': self.get_display_duration(),
            'last_update': self.last_update,
            'font_size_message': self.message_font_size,
            'font_size_time': self.time_font_size
        })
        return info
    
    def cleanup(self):
        """Cleanup resources when plugin is unloaded."""
        self.text_image_cache = None  # Clear image cache to free memory
        self.logger.info("Cleaning up Trevor's World plugin")
        super().cleanup()

