# display.py — For ST7735 1.8" TFT over SPI

from st7735 import ST7735
from machine import Pin, SPI
from time import ticks_ms
import config


# --- CONFIGURED PINS TO MATCH MY SETUP ---
TFT_SCK = config.TFT_SCK   # SCL (SPI Clock)
TFT_MOSI = config.TFT_MOSI  # SDA (SPI Data)
TFT_DC = config.TFT_DC     # Data/Command
TFT_CS = config.TFT_CS     # Chip Select
TFT_RST = config.TFT_RST   # Reset

# --- Initialize SPI and TFT ---
spi = SPI(1, baudrate=20000000, polarity=0, phase=0,
          sck=Pin(10), mosi=Pin(11))

tft = ST7735(spi, 128, 160, Pin(12), Pin(13), Pin(14))
tft.init()
text_color = config.TEXT_COLOR
# --- Display Utilities ---

def clear():
    tft.clear

def test_display():
    tft.fill(0)
    tft.text("Display test", 10, 10, text_color)
    tft.text("Time: {}".format(ticks_ms()), 10, 30, text_color)
    tft.show()

def show_mode(mode):
    tft.fill(0)
    tft.text("MODE:", 5, 5, text_color)
    tft.text(mode.upper(), 5, 25, text_color)
    tft.show()

def show_logic(level):
    tft.fill(0)
    tft.text("LOGIC MODE", 5, 5, text_color)
    tft.text("Level: {}".format("HIGH" if level else "LOW"), 5, 25, text_color)
    tft.show()

def show_frequency(freq_hz):
    tft.fill(0)
    tft.text("FREQ MODE", 5, 5, text_color)
    tft.text("Freq:", 5, 25, text_color)
    tft.text("{} Hz".format(freq_hz), 5, 45, text_color)
    tft.show()

def show_pulse(width_us):
    tft.fill(0)
    tft.text("PULSE WIDTH", 5, 5, text_color)
    tft.text("Pulse:", 5, 25, text_color)
    tft.text("{} us".format(width_us), 5, 45, text_color)
    tft.show()

def show_duty_cycle(duty_percent, freq_hz):
    tft.fill(0)
    tft.text("DUTY CYCLE", 5, 5, text_color)
    tft.text("Duty: {:.1f}%".format(duty_percent), 5, 25, text_color)
    tft.text("Freq: {} Hz".format(int(freq_hz)), 5, 45, text_color)
    tft.show()
    
def show_rise_fall(rise_ns, fall_ns):
    tft.fill(0)
    tft.text("EDGE TIMES", 5, 5, text_color)
    tft.text(f"Rise: {rise_ns} ns", 5, 25, text_color)
    tft.text(f"Fall: {fall_ns} ns", 5, 45, text_color)
    tft.show()
    
def show_edge_count(edges):
    tft.fill(0)
    tft.text("EDGE COUNT", 5, 5, text_color)
    tft.text("Edges:", 5, 25, text_color)
    tft.text("{}/s".format(edges), 5, 45, text_color)
    tft.show()
    
def show_number(num):
    """MUST BE IN CPU MODE"""
    tft.fill(0)
    tft.text("Number: ", 5, 5, text_color)
    tft.text("{}".format(num), 5, 45, text_color)
    tft.show()





