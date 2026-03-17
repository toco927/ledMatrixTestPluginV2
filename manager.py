"""
Trevor's World Plugin

A simple test plugin that displays a customizable greeting message
on the LED matrix. Used to demonstrate and test the plugin system.
"""

from src.plugin_system.base_plugin import BasePlugin
import time
from datetime import datetime
import os

try:
    import freetype
except ImportError:
    freetype = None


class TrevorWorldPlugin(BasePlugin):
    """
    Simple Trevor's World plugin for LEDMatrix.

    Displays a customizable greeting message with the current time.
    Demonstrates basic plugin functionality.
    """
    
    def __init__(self, plugin_id, config, display_manager, cache_manager, plugin_manager):
        """Initialize the Hello World plugin."""
        super().__init__(plugin_id, config, display_manager, cache_manager, plugin_manager)

        # Plugin-specific configuration
        self.message = config.get('message', 'Trevor made this')
        self.show_time = config.get('show_time', True)
        self.color = tuple(config.get('color', [255, 255, 255]))
        self.time_color = tuple(config.get('time_color', [0, 255, 255]))
        
        self.font_family = config.get('font_family', 'press_start')
        self.message_font_size = config.get('message_font_size', 10)  # Font size for message
        self.time_font_size = config.get('time_font_size', 8)  # Font size for time

        # Load the 6x9 BDF font
        self._load_font()

        # State
        self.last_update = None
        self.current_time_str = ""

        self.logger.info(f"Trevor's World plugin initialized with message: '{self.message}'")

        # Register fonts
        self._register_fonts()

    def _register_fonts(self):
        """Register fonts with the font manager."""
        try:
            if not hasattr(self.plugin_manager, 'font_manager'):
                return

            font_manager = self.plugin_manager.font_manager

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

            self.logger.info("Trevor's World fonts registered")
        except Exception as e:
            self.logger.warning(f"Error registering fonts: {e}")

    def _load_font(self):
        """Load the 6x9 BDF font for text rendering."""
        if freetype is None:
            self.logger.warning("freetype not available, font rendering disabled")
            self.bdf_font = None
            return

        try:
            font_path = "assets/fonts/6x9.bdf"
            if not os.path.exists(font_path):
                self.logger.error(f"Font file not found: {font_path}")
                self.bdf_font = None
                return

            self.bdf_font = freetype.Face(font_path)
            self.logger.info(f"6x9 BDF font loaded successfully from {font_path}")
        except Exception as e:
            self.logger.error(f"Failed to load 6x9 BDF font: {e}")
            self.bdf_font = None

    def update(self):
        """
        Update plugin data.
        
        For this simple plugin, we just update the current time string.
        In a real plugin, this would fetch data from APIs, databases, etc.
        """
        try:
            self.last_update = time.time()
            
            if self.show_time:
                now = datetime.now()
                new_time_str = now.strftime("%I:%M %p")
                
                # Only log if the time actually changed (reduces spam from sub-minute updates)
                if new_time_str != self.current_time_str:
                    self.current_time_str = new_time_str
                    # Only log time changes occasionally
                    if not hasattr(self, '_last_time_log') or time.time() - self._last_time_log > 60:
                        self.logger.info(f"Time updated: {self.current_time_str}")
                        self._last_time_log = time.time()
                else:
                    self.current_time_str = new_time_str
                
        except Exception as e:
            self.logger.error(f"Error during update: {e}", exc_info=True)
    
    def display(self, force_clear=False):
        """
        Render the plugin display.
        
        Displays the configured message and optionally the current time.
        """
        try:
            # Clear display if requested
            if force_clear:
                self.display_manager.clear()
            
            # Get display dimensions
            width = self.display_manager.width
            height = self.display_manager.height
            
            # Get fonts from font manager
            message_font = None
            time_font = None

            try:
                if hasattr(self.plugin_manager, 'font_manager'):
                    
                    font_manager = self.plugin_manager.font_manager
                    
                    message_font = font_manager.resolve_font(
                        element_key=f"{self.plugin_id}.message",
                        family=self.font_family,
                        size_px=self.message_font_size
                    )

                    time_font = font_manager.resolve_font(
                        element_key=f"{self.plugin_id}.time",
                        family=self.font_family,
                        size_px=self.time_font_size
                    )
                    
                    # message_font = font_manager.get_font(f"{self.plugin_id}.message", self.message_font_size)
                    # time_font = font_manager.get_font(f"{self.plugin_id}.time", self.time_font_size)
            except Exception as e:
                self.logger.warning(f"Error getting fonts from font manager: {e}")

            # Calculate positions for centered text
            # --- Centering logic ---
            def get_text_size(text, font=None, font_fallback=None):
                # Try to use display_manager's get_text_width and get_font_height if available
                try:
                    if font and hasattr(self.display_manager, 'get_text_width') and hasattr(self.display_manager, 'get_font_height'):
                        w = self.display_manager.get_text_width(text, font=font)
                        h = self.display_manager.get_font_height(font=font)
                        return w, h
                except Exception:
                    pass
                # Fallback: use BDF font if available
                try:
                    if font_fallback and hasattr(self.display_manager, 'get_text_width') and hasattr(self.display_manager, 'get_font_height'):
                        w = self.display_manager.get_text_width(text, font=font_fallback)
                        h = self.display_manager.get_font_height(font=font_fallback)
                        return w, h
                except Exception:
                    pass
                # Last resort: estimate
                return len(text) * 6, 9  # crude guess

            if self.show_time:
                # --- Center message horizontally, time at bottom ---
                # Message
                msg_w, msg_h = get_text_size(self.message, font=message_font, font_fallback=self.bdf_font)
                msg_x = (width - msg_w) // 2
                msg_y = (height // 2) - (msg_h // 2)

                # Time
                time_w, time_h = get_text_size(self.current_time_str, font=time_font, font_fallback=self.bdf_font)
                time_x = (width - time_w) // 2
                time_y = height - time_h  # bottom of display

                # Draw the greeting message
                if message_font:
                    self.display_manager.draw_text(
                        self.message,
                        x=msg_x,
                        y=msg_y,
                        font=message_font
                    )
                else:
                    self.display_manager.draw_text(
                        self.message,
                        x=msg_x,
                        y=msg_y,
                        color=self.color,
                        font=self.bdf_font
                    )

                # Draw the current time
                if self.current_time_str:
                    if time_font:
                        self.display_manager.draw_text(
                            self.current_time_str,
                            x=time_x,
                            y=time_y,
                            font=time_font
                        )
                    else:
                        self.display_manager.draw_text(
                            self.current_time_str,
                            x=time_x,
                            y=time_y,
                            color=self.time_color,
                            font=self.bdf_font
                        )
            else:
                # Center message both horizontally and vertically
                msg_w, msg_h = get_text_size(self.message, font=message_font, font_fallback=self.bdf_font)
                msg_x = (width - msg_w) // 2
                msg_y = (height - msg_h) // 2
                if message_font:
                    self.display_manager.draw_text(
                        self.message,
                        x=msg_x,
                        y=msg_y,
                        font=message_font
                    )
                else:
                    self.display_manager.draw_text(
                        self.message,
                        x=msg_x,
                        y=msg_y,
                        color=self.color,
                        font=self.bdf_font
                    )
            
            # Update the physical display
            self.display_manager.update_display()
                
        except Exception as e:
            self.logger.error(f"Error during display: {e}", exc_info=True)
            # Show error message on display
            try:
                self.display_manager.clear()
                self.display_manager.draw_text(
                    "Error!",
                    x=width // 2,
                    y=height // 2,
                    color=(255, 0, 0),
                    font=self.bdf_font
                )
                self.display_manager.update_display()
            except:
                pass  # If we can't even show error, just log it
    
    def validate_config(self):
        """
        Validate plugin configuration.
        
        Ensures the configuration values are valid.
        """
        # Call parent validation
        if not super().validate_config():
            return False
        
        # Validate message
        if 'message' in self.config:
            if not isinstance(self.config['message'], str):
                self.logger.error("'message' must be a string")
                return False
            if len(self.config['message']) > 50:
                self.logger.warning("'message' is very long, may not fit on display")

        if 'font_family' in self.config:
            if self.config['font_family'] not in ['press_start', 'four_by_six', 'tom_thumb', 'tiny', 'picopixel']:
                self.logger.error("'font_family' must be one of the predefined font families")
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

        # Validate message_font_size
        if 'message_font_size' in self.config:
            if not isinstance(self.config['message_font_size'], int):
                self.logger.error("'message_font_size' must be an integer")
                return False
            if not (1 <= self.config['message_font_size'] <= 100):
                self.logger.error("'message_font_size' must be between 1 and 100")
                return False

        # Validate time_font_size
        if 'time_font_size' in self.config:
            if not isinstance(self.config['time_font_size'], int):
                self.logger.error("'time_font_size' must be an integer")
                return False
            if not (1 <= self.config['time_font_size'] <= 100):
                self.logger.error("'time_font_size' must be between 1 and 100")
                return False

        self.logger.info("Configuration validated successfully")
        return True
    
    def get_info(self):
        """
        Return plugin information for web UI.
        """
        info = super().get_info()
        info['message'] = self.message
        info['show_time'] = self.show_time
        info['last_update'] = self.last_update
        info['current_time'] = self.current_time_str
        info['message_font_size'] = self.message_font_size
        info['time_font_size'] = self.time_font_size
        return info
    
    def cleanup(self):
        """
        Cleanup resources when plugin is unloaded.
        """
        self.logger.info("Cleaning up Trevor's World plugin")
        super().cleanup()

