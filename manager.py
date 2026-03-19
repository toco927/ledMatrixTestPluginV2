"""
Trevor's World Plugin

A simple message queue plugin that displays a list of messages
on the LED matrix with a random number (1-10) appended to each.
Each message displays for its configured duration before cycling to the next.
"""

from src.plugin_system.base_plugin import BasePlugin
import time
import random
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path


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
        
        # Load font and set up first message
        self._load_font()
        self._load_current_message()
        
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
            
            if isinstance(self.font, ImageFont.FreeTypeFont) or isinstance(self.font, ImageFont.ImageFont):
                bbox = temp_draw.textbbox((0, 0), display_text, font=self.font)
                self.message_width = bbox[2] - bbox[0]
                self.message_height = bbox[3] - bbox[1]
            else:
                self.message_width = len(display_text) * 8
                self.message_height = 10
        except Exception as e:
            self.logger.warning(f"Could not calculate text dimensions: {e}")
            self.message_width = len(self.current_message) * 8
            self.message_height = 10

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

    def update(self):
        """Update plugin - this is called periodically but timing is handled in display()."""
        # Timing logic has been moved to display() for more accurate tracking
        # since display() is only called when the plugin is actively being rendered
        pass

    def display(self, force_clear=False):
        """
        Render the plugin display.
        
        Displays the current message with appended random number (1-10).
        Handles message advancement timing to ensure accurate cycling.
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
            
            # Create display image
            img = Image.new('RGB', (width, height), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Build display text: message + random number
            display_text = f"{self.current_message} {self.current_random_number}"
            
            # Calculate text dimensions for centering
            try:
                bbox = draw.textbbox((0, 0), display_text, font=self.font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except Exception:
                text_width = len(display_text) * 8
                text_height = 10
            
            # Center text on display
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw the text
            try:
                draw.text((x, y), display_text, font=self.font, fill=self.current_message_color)
            except Exception as e:
                self.logger.error(f"Error drawing text: {e}")
            
            # Update display
            self.display_manager.image = img
            self.display_manager.update_display()
            
        except Exception as e:
            self.logger.error(f"Error during display: {e}", exc_info=True)

    def on_config_change(self, new_config):
        """Handle configuration changes at runtime."""
        super().on_config_change(new_config)
        
        # Update message list
        new_messages = new_config.get('messages', self.messages)
        if new_messages != self.messages:
            self.messages = new_messages
            self.current_message_index = 0
            self._load_current_message()
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
        })
        return info

    def cleanup(self):
        """Cleanup resources when plugin is unloaded."""
        self.logger.info("Cleaning up Trevor's World plugin")
        super().cleanup()
