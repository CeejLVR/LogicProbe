from machine import Pin, disable_irq, enable_irq, time_pulse_us, Timer
import utime
import config

# Calibration factors from my test results
CALIBRATION = {
    'pulse_width': 1,
    'duty_cycle': 1,
    'frequency': 2,
}

def auto_sample_time(freq_hz):
    """Adjust sample time based on expected frequency."""
    if freq_hz < 100:
        return 200  # 200ms for low freq
    elif freq_hz < 1000:
        return 50   # 50ms for mid freq
    else:
        return 10   # 10ms for high freq


class CpuPulseWidth:
    def __init__(self, pin_num):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
        self.timeout_us = config.DEFAULT_TIMEOUT_MS * 1000
        self.min_us = 2
        self.max_us = 20000

    def measure(self, samples=15):
        widths = []
        
        for _ in range(samples):
            try:
                width = time_pulse_us(self.pin, 1, self.timeout_us)
                if self.min_us < width < self.max_us:
                    widths.append(width)
            except OSError:
                print("PW measurement timed out or failed.")
                pass
            
        if not widths:
            print("No valid pulse widths measured.")
            return 0
            
        # Reject outliers
        widths.sort()
        n = len(widths)
        filtered = widths[n//4 : 3*n//4]  # Interquartile range
        avg = sum(filtered) // len(filtered)
        return int(avg * CALIBRATION['pulse_width'])

class CpuFrequencyCounter:
    def __init__(self, pin_num):
        self.pin = Pin(pin_num, Pin.IN)
        self.edge_count = 0
        self.last_state = self.pin.value()
        self.timer = Timer()
        self.min_freq_hz = 10

    def _edge_callback(self, pin):
        if pin.value() == 1 and self.last_state == 0:  # Rising edge
            self.edge_count += 1
        self.last_state = pin.value()

    def measure(self, sample_time_ms=100):
        if sample_time_ms < 1:  # Minimum 1ms for high frequencies
            sample_time_ms = 1
            
        self.edge_count = 0
        self.last_state = self.pin.value()
        
        # Setup interrupt for edges
        self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._edge_callback)
        
        start_time = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), start_time) < sample_time_ms:
            pass
        
        self.pin.irq(handler=None)  # Disable interrupt
        
        raw_freq = (self.edge_count * 500) / sample_time_ms  # Each full cycle = 2 edges
        return raw_freq * CALIBRATION['frequency'] if raw_freq >= self.min_freq_hz else 0


class CpuEdgeTimer:
    def __init__(self, pin_num):
        self.pin = Pin(pin_num, Pin.IN)
        self.timeout_us = config.DEFAULT_TIMEOUT_MS * 1000
        self.debounce_us = 5

    def _wait_edge(self, target_state):
        start = utime.ticks_us()
        last_valid = start

        while True:
            now = utime.ticks_us()
            if self.pin.value() == target_state:
                if utime.ticks_diff(now, last_valid) > self.debounce_us:
                    return True
            else:
                last_valid = now

            if utime.ticks_diff(now, start) > self.timeout_us:
                return False

    def _measure_transition(self, from_state):
        if not self._wait_edge(from_state):
            return 0
        start = utime.ticks_us()
        if not self._wait_edge(1 - from_state):
            return 0
        return utime.ticks_diff(utime.ticks_us(), start)

    def measure(self, samples=15):
        rise_times, fall_times = [], []

        for _ in range(samples):
            rise = self._measure_transition(0)
            if rise <= 0:
                continue
            fall = self._measure_transition(1)
            if fall <= 0:
                continue

            rise_times.append(rise)
            fall_times.append(fall)

        if not rise_times or not fall_times:
            return 0, 0

        rise_times.sort()
        fall_times.sort()
        median_rise = rise_times[len(rise_times) // 2]
        median_fall = fall_times[len(fall_times) // 2]
        
        # Calculate duty cycle and apply calibration
        period = median_rise + median_fall
        if period > 0:
            duty_cycle = (median_rise / period) * CALIBRATION['duty_cycle'] * 100
            # Recalculate rise time based on calibrated duty cycle
            calibrated_rise = (duty_cycle * period) / 100
            calibrated_fall = period - calibrated_rise
            return calibrated_rise, calibrated_fall
        return median_rise, median_fall


class CpuEdgeCounter:
    def __init__(self, pin_num, button_pin_num):
        self.pin = Pin(pin_num, Pin.IN)
        self.button = Pin(button_pin_num, Pin.IN, Pin.PULL_UP)
        self.last_signal = self.pin.value()
        self.last_button = self.button.value()
        self.edge_count = 0
        self.counting = False
        self.result_ready = False

    def reset(self):
        self.edge_count = 0
        self.last_signal = self.pin.value()
        self.counting = False
        self.result_ready = False

    def update(self):
        current_button = self.button.value()

        if self.last_button == 1 and current_button == 0:
            if self.result_ready:
                self.reset()
            else:
                self.counting = True

        elif self.last_button == 0 and current_button == 1:
            if self.counting:
                self.counting = False
                self.result_ready = True

        self.last_button = current_button

        if self.counting:
            current_signal = self.pin.value()
            if current_signal != self.last_signal:
                self.edge_count += 1
                self.last_signal = current_signal

    def get_result(self):
        return self.edge_count if self.result_ready else None

