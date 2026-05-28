from machine import Pin, I2C
import framebuf

class SH1106_I2C(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3c):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)

        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)

        self.init_display()

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray([0x80, cmd]))

    def init_display(self):
        cmds = [
            0xAE,
            0xD5, 0x80,
            0xA8, 0x3F,
            0xD3, 0x00,
            0x40,
            0xA1,
            0xC8,
            0xDA, 0x12,
            0x81, 0xCF,
            0xD9, 0xF1,
            0xDB, 0x40,
            0xA4,
            0xA6,
            0xAF
        ]

        for cmd in cmds:
            self.write_cmd(cmd)

    def show(self):
        for page in range(self.pages):
            self.write_cmd(0xB0 + page)

            # column offset
            self.write_cmd(0x02)
            self.write_cmd(0x10)

            start = self.width * page
            end = start + self.width

            # get page slice
            page_buf = self.buffer[start:end]

            # send in chunks to avoid I2C timeout
            for i in range(0, self.width, 16):
                chunk = page_buf[i:i+16]
                self.i2c.writeto(self.addr, b'\x40' + chunk)

