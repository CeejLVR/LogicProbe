from machine import Pin
import utime


class RotaryEncoder:

    def __init__(self, pin_clk, pin_dt):

        self.clk = Pin(pin_clk, Pin.IN, Pin.PULL_UP)
        self.dt = Pin(pin_dt, Pin.IN, Pin.PULL_UP)

        self.last_clk = self.clk.value()

        self.last_event_time = utime.ticks_ms()

        # adjust if needed
        self.debounce_ms = 5

    def read(self):

        current_clk = self.clk.value()

        # detect ONLY falling edge
        if self.last_clk == 1 and current_clk == 0:

            now = utime.ticks_ms()

            # debounce
            if utime.ticks_diff(now, self.last_event_time) > self.debounce_ms:

                self.last_event_time = now

                # sample DT after tiny settle delay
                utime.sleep_us(200)

                if self.dt.value():
                    result = 1
                else:
                    result = -1

                self.last_clk = current_clk

                return result

        self.last_clk = current_clk

        return 0

    def button_pressed(self):
        if self.sw is None:
            return False

        return self.sw.value() == 0
