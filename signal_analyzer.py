from machine import Pin
from pio_based_helpers import PrecisionPulse, EdgeTimer, FrequencyMeasure
from cpu_based_helpers import CpuPulseWidth, CpuEdgeTimer, CpuFrequencyCounter, CpuEdgeCounter
import uasyncio
import config

class SignalAnalyzer:
    def __init__(self, pin_num, mode="pio"):
        self.pin = Pin(pin_num, Pin.IN)
        self.mode = mode
        if mode == "pio":
            # PIO-based measurements
            self._pulse = PrecisionPulse(pin_num)
            self._edge = EdgeTimer(pin_num)
            self._freq = FrequencyMeasure(pin_num)
        else:
            # CPU-based measurments
            self._pulse = CpuPulseWidth(pin_num)
            self._edge = CpuEdgeTimer(pin_num)
            self._freq = CpuFrequencyCounter(pin_num)
            self._edge_counter = CpuEdgeCounter(pin_num, config.EDGE_BUTTON_PIN)
            self.edge_button_enabled = False
            self.edge_button_result = None

    
    def set_mode(self, mode):
        if mode == self.mode:
            return
        self.__init__(self.pin.id(), mode=mode)  # Reinitialize with new mode

    
    
    def pulse_width_us(self, samples=15):
        """Measure high pulse width in microseconds."""
        return self._pulse.measure(samples)


    def rise_fall_times_ns(self, samples=15):
        """Measure rise and fall times in nanoseconds."""
        return self._edge.measure(samples)

    def frequency(self, sample_time_ms=100):
        """Return frequency in Hz."""
        if self.mode == "pio":
            _, freq_hz, _ = self._freq.measure(sample_time_ms)
        else:
            freq_hz =  self._freq.measure(sample_time_ms)
        return freq_hz

    def period_ns(self, sample_time_ms=100):
        """Return period in nanoseconds."""
        if self.mode == "pio":
            period_ns, _, _ = self._freq.measure(sample_time_ms)
            return period_ns
        else:
            freq = self.frequency()
            period_us = 1_000_000_000 / freq if freq > 0 else 0
            return period_us
        return 0

    def edge_count(self, sample_time_ms=100):
        """Return number of edges counted during the sample time."""
        if self.mode == "pio":
            _, _, edges = self._freq.measure(sample_time_ms)
        else:
            edges = self._edge_counter.update()
        return edges

    def duty_cycle(self, pulse_samples=10, freq_sample_time_ms=100):
        """Calculate duty cycle (%) and frequency (Hz)."""
        pw_us = self.pulse_width_us(pulse_samples)

        if self.mode == "pio":
            period_ns, freq_hz, _ = self._freq.measure(freq_sample_time_ms)
        else:
            period_ns = self.period_ns(freq_sample_time_ms)
            freq_hz = 1_000_000_000 / period_ns if period_ns else 0.0

        if period_ns == 0:
            return 0.0, 0.0

        duty = (pw_us * 1000) / period_ns * 100  # Convert us -> ns
        return round(duty, 1), freq_hz
    
    def enable_button_edge_count(self, button_pin_num):
        if self.mode != "cpu":
            raise RuntimeError("Button-based edge counting is only supported in 'cpu' mode.")
        self._edge_counter.button = Pin(button_pin_num, Pin.IN, Pin.PULL_UP)
        self._edge_counter.last_button = self._edge_counter.button.value()
        self.edge_button_enabled = True
        self.edge_button_result = None

    def update(self):
        if self.mode == "cpu" and self.edge_button_enabled:
            self._edge_counter.update()
            self.edge_button_result = self._edge_counter.get_result()

    def get_button_edge_result(self):
        return self.edge_button_result
    
    
    async def edge_count_while_held(self, button_pin, show_callback=None):
        """Counts edges while button is held down. Displays result when released."""
        if self.mode != "cpu":
            return

        print("Waiting for button press...")
        while button_pin.value():  # Wait for press (PULL_UP)
            await uasyncio.sleep_ms(10)

        print("Button pressed. Starting edge count...")
        self._edge_counter.reset()

        while not button_pin.value():  # While still held
            current = self.pin.value()
            if current != self._edge_counter.last_signal:
                self._edge_counter.edge_count += 1
                self._edge_counter.last_signal = current
            await uasyncio.sleep_ms(1)

        count = self._edge_counter.edge_count
        print(f"Edge count: {count}")

        if show_callback:
            show_callback(count)

        return count
