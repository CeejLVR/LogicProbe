# display.py — Clean UI for ST7735 TFT Logic Probe
from st7735 import ST7735S
import config
import framebuf
import time

# Initialize display with optimized settings
tft = ST7735S(width=128, height=160)
tft.spi.init(baudrate=30_000_000)  # Increased SPI speed

# Colors
text_color = config.TEXT_COLOR
bg_color = config.BG_COLOR
highlight_color = config.HIGHLIGHT_COLOR

# --- Optimized Helpers ---
def clear(force=False):
    """Optimized clear that only updates if needed"""
    if force or tft.framebuf.fill(bg_color):
        tft.show()

def header(title):
    """Optimized header that only redraws changed areas"""
    # Save previous header text if needed
    tft.framebuf.fill_rect(0, 0, 128, 20, highlight_color)
    tft.framebuf.text(title, 5, 5, bg_color)

def center_text(text, y, color=text_color):
    x = (128 - len(text) * 8) // 2
    tft.framebuf.text(text, x, y, color)

def line(y):
    tft.framebuf.hline(0, y, 128, text_color)

# --- Display Modes with Optimized Updates ---
def show_mode(mode):
    tft.framebuf.fill(bg_color)
    header("MODE")
    center_text(mode.upper(), 60)
    tft.show()

def show_logic(level):
    # Only update changing parts
    tft.framebuf.fill_rect(0, 20, 128, 140, bg_color)  # Clear only content area
    header("LOGIC PROBE")
    center_text("HIGH" if level else "LOW", 70, config.GREEN if level else config.RED)
    tft.show()

def show_frequency(freq_hz):
    tft.framebuf.fill_rect(0, 20, 128, 140, bg_color)
    header("FREQUENCY")
    line(25)
    
    if freq_hz >= 1000:
        txt = "{:.2f} kHz".format(freq_hz / 1000)
    else:
        txt = "{} Hz".format(int(freq_hz))

    center_text(txt, 70)
    tft.show()
def show_pulse(width_us):
    """Optimized pulse width display with partial updates"""
    # Clear only content area (below header and line)
    tft.framebuf.fill_rect(0, 26, 128, 134, bg_color)
    header("PULSE WIDTH")
    line(25)
    
    txt = "{} us".format(int(width_us))
    center_text(txt, 70)
    tft.show()

def show_duty_cycle(duty_percent, freq_hz):
    """Optimized duty cycle display with minimal redraws"""
    # Clear only the areas we'll modify
    tft.framebuf.fill_rect(0, 26, 128, 94, bg_color)  # Below header to bottom
    
    header("DUTY CYCLE")
    line(25)
    
    # Draw bar graph (only redraw changed portion)
    bar_width = int(duty_percent / 100 * 100)
    # Clear old bar
    tft.framebuf.fill_rect(14, 70, 100, 15, bg_color)
    # Draw new bar
    tft.framebuf.fill_rect(14, 70, bar_width, 15, highlight_color)
    tft.framebuf.rect(14, 70, 100, 15, text_color)
    
    # Text (clear old text areas first)
    tft.framebuf.fill_rect(50, 90, 40, 8, bg_color)
    tft.framebuf.fill_rect(40, 110, 50, 8, bg_color)
    tft.framebuf.text("{:.1f}%".format(duty_percent), 50, 90, text_color)
    tft.framebuf.text("{:.0f}Hz".format(freq_hz), 40, 110, text_color)
    tft.show()

def show_rise_fall(rise_ns, fall_ns):
    """Optimized edge timing display"""
    # Clear only the text areas we'll use
    tft.framebuf.fill_rect(0, 26, 128, 74, bg_color)  # Below line to bottom
    
    header("EDGE TIMES")
    line(25)
    
    # Clear old text areas
    tft.framebuf.fill_rect(10, 60, 80, 8, bg_color)
    tft.framebuf.fill_rect(10, 80, 80, 8, bg_color)
    
    tft.framebuf.text("Rise: {}ns".format(int(rise_ns)), 10, 60, text_color)
    tft.framebuf.text("Fall: {}ns".format(int(fall_ns)), 10, 80, text_color)
    tft.show()

def show_edge_count(edges):
    """Optimized edge counter display"""
    # Clear only center area where number appears
    tft.framebuf.fill_rect(0, 26, 128, 134, bg_color)
    
    header("EDGE COUNT")
    line(25)
    
    # Clear old text area
    text = "{} edges/s".format(edges)
    text_width = len(text) * 8
    tft.framebuf.fill_rect((128 - text_width)//2, 70, text_width, 8, bg_color)
    
    center_text(text, 70)
    tft.show()

def show_number(num):
    """Optimized number display"""
    # Clear only center area where number appears
    tft.framebuf.fill_rect(0, 26, 128, 134, bg_color)
    
    header("NUMBER")
    
    # Clear old number area
    num_str = str(num)
    text_width = len(num_str) * 8
    tft.framebuf.fill_rect((128 - text_width)//2, 70, text_width, 8, bg_color)
    
    center_text(num_str, 70)
    tft.show()
