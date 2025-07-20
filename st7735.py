import time
import framebuf
import machine
import config  # Your configuration file with the pin definitions

class ST7735S:
    def __init__(self, width=128, height=160):
        """
        Initialize ST7735S display controller using pins from config
        
        Args:
            width: Display width (default 128)
            height: Display height (default 160)
        """
        self.width = width
        self.height = height
        
        # Initialize SPI and pins from config
        self.spi = machine.SPI(1,
                              baudrate=20_000_000,
                              polarity=0,
                              phase=0,
                              sck=machine.Pin(config.TFT_SCK),
                              mosi=machine.Pin(config.TFT_MOSI))
        
        self.dc = machine.Pin(config.TFT_DC, machine.Pin.OUT)
        self.rst = machine.Pin(config.TFT_RST, machine.Pin.OUT)
        self.cs = machine.Pin(config.TFT_CS, machine.Pin.OUT)
        
        # Initialize display
        self.reset()
        self.init_display()
        
        # Create framebuffer
        self.buffer = bytearray(self.width * self.height * 2)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.RGB565)
    
    def write_cmd(self, cmd):
        """Write command to display"""
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)
    
    def write_data(self, data):
        """Write data to display"""
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)
    
    def reset(self):
        """Hardware reset"""
        self.rst(1)
        time.sleep_ms(5)
        self.rst(0)
        time.sleep_ms(20)
        self.rst(1)
        time.sleep_ms(150)
    
    def init_display(self):
        """Initialize display with basic commands"""
        # Initialization sequence
        cmds = [
            (0x01, None, 150),  # SWRESET, 150ms delay
            (0x11, None, 255),  # SLPOUT, 255ms delay
            (0x3A, b'\x05', 10),  # COLMOD, 16-bit color
            (0x36, b'\xC0', 0),   # MADCTL, RGB color filter
            (0x29, None, 255),    # DISPON, 255ms delay
        ]
        
        for cmd, data, delay in cmds:
            self.write_cmd(cmd)
            if data:
                self.write_data(data)
            if delay:
                time.sleep_ms(delay)
    
    def show(self):
        """Display the framebuffer on screen"""
        self.write_cmd(0x2A)  # Column address set
        self.write_data(bytes([0, 0, 0, self.width-1]))
        
        self.write_cmd(0x2B)  # Row address set
        self.write_data(bytes([0, 0, 0, self.height-1]))
        
        self.write_cmd(0x2C)  # Memory write
        self.write_data(self.buffer)
    
    def clear(self, color=0):
        """Clear the display with specified color"""
        self.framebuf.fill(color)
        self.show()
