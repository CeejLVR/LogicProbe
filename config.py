# config.py
# Pin mappings for your SCL/SDA labeled TFT (ST7735)

INPUT_PIN = 15         # Logic probe input
ADC_PIN = 26           # Analog voltage input which is not yet used
MODE_BUTTON_PIN = 16   # Button to cycle display modes
EDGE_BUTTON_PIN = 19

# TFT display wiring (adjusted to match my setup)
TFT_SCK = 10           # SCL → GP10
TFT_MOSI = 11          # SDA → GP11
TFT_RST = 12           # RES → GP12
TFT_DC = 13            # DC  → GP13
TFT_CS = 14            # CS  → GP14

# Control BL using a GPIO
# BACKLIGHT_PIN = 15   # or just hardwire BL to 3.3V

# Reference voltage for analog measurement
VREF = 3.3
INPUT_THRESHOLD_LOW = 0.8  # Volts
INPUT_THRESHOLD_HIGH = 2.0  # Volts
MAX_INPUT_VOLTAGE = 5.0     # Volts


# PIO Configuration
USE_PIO = False
PIO_FREQ = 125_000_000    # Typically 125MHz (1 clock cycle = 8ns)
DEFAULT_TIMEOUT_MS = 500  # Timeout after a full second
CLOCK_NS = 8              # Time for one clock cycle at 125MHz

DEBOUNCE_US = 5000







# Safe Mode ON = disables risky features (IRQs, timers, etc.)
SAFE_MODE = False



# Color Palette for ST7735 TFT

# config.py
TEXT_COLOR = 0xFFFF       # White
BG_COLOR = 0x0000         # Black
HIGHLIGHT_COLOR = 0x001F  # Blue
GREEN = 0x07E0            # Green
RED = 0xF800              # Red


