# display.py — Clean UI for SH1106 I2C OLED Logic Probe
from machine import I2C, Pin
import sh1106
import config

# I2C init
i2c = I2C(
    0,
    scl=Pin(config.SCL),
    sda=Pin(config.SDA),
    freq=config.I2C_FREQ
)

# SH1106 OLED 128x64
oled = sh1106.SH1106_I2C(128, 64, i2c)


# Colors for monochrome display
WHITE = 1
BLACK = 0

# --- Helpers ---
def clear():
    """Clear the entire display buffer."""
    oled.fill(BLACK)
    oled.show()

def header(title):
    """Draw a highlighted header bar with title."""
    # Draw filled top bar (inverted: white background, black text)
    oled.fill_rect(0, 0, 128, 16, WHITE)
    oled.text(title, 2, 4, BLACK)   # black text on white background

def center_text(text, y, color=WHITE):
    """Center text horizontally."""
    x = (128 - len(text) * 8) // 2
    oled.text(text, x, y, color)

def line(y):
    """Draw a horizontal line at given y (white)."""
    oled.hline(0, y, 128, WHITE)

# --- Display Modes with Optimized Updates ---
def show_mode(mode):
    oled.fill(BLACK)
    header("MODE")
    center_text(mode.upper(), 30)
    oled.show()

def show_logic(level):
    # Clear only the content area (below header)
    oled.fill_rect(0, 16, 128, 48, BLACK)
    header("LOGIC PROBE")
    status = "HIGH" if level else "LOW"
    # Use white text; optionally invert for emphasis
    center_text(status, 35, WHITE)
    oled.show()

def show_frequency(freq_hz):
    oled.fill_rect(0, 16, 128, 48, BLACK)
    header("FREQUENCY")
    line(20)
    if freq_hz >= 1000:
        txt = "{:.2f} kHz".format(freq_hz / 1000)
    else:
        txt = "{} Hz".format(int(freq_hz))
    center_text(txt, 40)
    oled.show()

def show_pulse(width_us):
    oled.fill_rect(0, 16, 128, 48, BLACK)
    header("PULSE WIDTH")
    line(20)
    txt = "{} us".format(int(width_us))
    center_text(txt, 40)
    oled.show()

def show_duty_cycle(duty_percent, freq_hz):
    oled.fill_rect(0, 16, 128, 48, BLACK)
    header("DUTY CYCLE")
    line(20)
    # Bar graph outline
    bar_width = min(max(int(duty_percent), 0), 100)
    oled.rect(14, 35, 100, 8, WHITE)

    # Filled portion
    oled.fill_rect(14, 35, bar_width, 8, WHITE)
    # Percent text
    oled.text("{:.1f}%".format(duty_percent), 50, 48, WHITE)
    # Frequency text (smaller, bottom right)
    oled.text("{:.0f}Hz".format(freq_hz), 70, 56, WHITE)
    oled.show()

def show_rise_fall(rise_ns, fall_ns):
    oled.fill_rect(0, 16, 128, 48, BLACK)
    header("EDGE TIMES")
    line(20)
    oled.text("Rise: {}ns".format(int(rise_ns)), 5, 30, WHITE)
    oled.text("Fall: {}ns".format(int(fall_ns)), 5, 45, WHITE)
    oled.show()

def show_edge_count(edges):
    oled.fill_rect(0, 16, 128, 48, BLACK)
    header("EDGE COUNT")
    line(20)
    text = "{} edges/s".format(edges)
    center_text(text, 40)
    oled.show()

def show_number(num):
    oled.fill_rect(0, 16, 128, 48, BLACK)
    header("NUMBER")
    center_text(str(num), 35)
    oled.show()
