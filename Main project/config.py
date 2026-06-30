# config.py
# Pin mappings for your SCL/SDA labeled TFT (ST7735)

INPUT_PIN = 15         # Logic probe input
ADC_PIN = 26           # Analog voltage input which is not yet used
MODE_BUTTON_PIN = 16   # Button to cycle display modes
EDGE_BUTTON_PIN = 19

# TFT display wiring (adjusted to match my setup)
SCL = 13           
SDA = 12          
I2C_FREQ = 50000      # 50 kHz

#Rotary Encoder Pins
PSH_BTN = 7
A_PIN = 8
B_PIN = 9

# Reference voltage for analog measurement
VREF = 3.3
INPUT_THRESHOLD_LOW = 0.8  # Volts
INPUT_THRESHOLD_HIGH = 2.0  # Volts
MAX_INPUT_VOLTAGE = 3.3     # Volts

TEST_PWM = True  # Set to True to enable test PWM output on pin 17 for testing purposes



# PIO Configuration
PIO_FREQ = 125_000_000    # 125MHz (1 clock cycle = 8ns)
DEFAULT_TIMEOUT_MS = 1000  # Timeout after a full second
CLOCK_NS = 8              # Time for one clock cycle at 125MHz

DEBOUNCE_US = 50

# Safe Mode ON = disables risky features (IRQs, timers, etc.)
SAFE_MODE = False

# config.py
TEXT_COLOR = 0xFFFF       # White
BG_COLOR = 0x0000         # Black
HIGHLIGHT_COLOR = 0x001F  # Blue
GREEN = 0x07E0            # Green
RED = 0xF800              # Red



