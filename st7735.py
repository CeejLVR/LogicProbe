# Lightweight ST7735 driver for MicroPython

import time
import framebuf

class ST7735(framebuf.FrameBuffer):
    def __init__(self, spi, width, height, reset, dc, cs, rotation=0):
        self.spi = spi
        self.width = width
        self.height = height
        self.dc = dc
        self.cs = cs
        self.reset = reset
        self.rotation = rotation

        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)

        self.dc.init(self.dc.OUT, value=0)
        self.cs.init(self.cs.OUT, value=1)
        self.reset.init(self.reset.OUT, value=1)

        self.init()

    def init(self):
        self.reset.value(0)
        time.sleep_ms(50)
        self.reset.value(1)
        time.sleep_ms(50)

        for cmd, data in (
            (0x01, b''),       # Software reset
            (0x11, b''),       # Sleep out
            (0x3A, b'\x05'),   # 16-bit color
            (0x36, b'\xC8'),   # MADCTL (rotation config)
            (0x29, b''),       # Display ON
        ):
            self.write_cmd(cmd)
            if data:
                self.write_data(data)
            time.sleep_ms(10)

    def write_cmd(self, cmd):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(data)
        self.cs.value(1)

    def show(self):
        self.write_cmd(0x2A)
        self.write_data(bytearray([0x00, 0, 0x00, self.width - 1]))
        self.write_cmd(0x2B)
        self.write_data(bytearray([0x00, 0, 0x00, self.height - 1]))
        self.write_cmd(0x2C)
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(self.buffer)
        self.cs.value(1)
    
    def clear(self):
    # Fill the buffer with 0 (black)
        for i in range(len(self.buffer)):
            self.buffer[i] = 0
        self.show()
        
'''
    def fill(self, color):
        # Fill the buffer with the specified color
        for i in range(0, len(self.buffer), 2):
            self.buffer[i] = (color >> 8) & 0xFF
            self.buffer[i + 1] = color & 0xFF
        self.show()
        
    def text(self, string, x, y, color):
        # Simple text rendering (not fully implemented)
        for i, char in enumerate(string):
            if x + i * 8 < self.width and y < self.height:
                # Draw a simple pixel for each character (placeholder)
                self.buffer[(y * self.width + (x + i * 8)) * 2] = (color >> 8) & 0xFF
                self.buffer[(y * self.width + (x + i * 8)) * 2 + 1] = color & 0xFF
        self.show()
'''


