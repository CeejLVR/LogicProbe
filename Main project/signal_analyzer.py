from machine import Pin, ADC
from pio_based_helpers import PrecisionPulse, EdgeTimer, FrequencyMeasure
import config

class SignalAnalyzer:
    def __init__(self, pin_num):
        self.pin = Pin(pin_num, Pin.IN)
        self.adc = ADC(config.ADC_PIN)
        # PIO-based measurements
        self._pulse = PrecisionPulse(pin_num)
        self._edge = EdgeTimer(pin_num)
        self._freq = FrequencyMeasure(pin_num)


    def pulse_width_us(self, samples=15):
        """Measure high pulse width in microseconds."""
        return self._pulse.measure(samples)

    def rise_fall_times_ns(self, samples=15):
        """Measure rise and fall times in nanoseconds."""
        return self._edge.measure(samples)

    def frequency(self, sample_time_ms=100):
        """Return frequency in Hz."""
        _, freq_hz, _ = self._freq.measure(sample_time_ms)
        return freq_hz

    def period_ns(self, sample_time_ms=100):
        """Return period in nanoseconds."""
        period_ns, _, _ = self._freq.measure(sample_time_ms)
        return period_ns

    # Edge Count not currently in use
    def edge_count(self, sample_time_ms=100):
        """Return number of edges counted during the sample time."""
        _, _, edges = self._freq.measure(sample_time_ms)
        return edges

    def duty_cycle(self, pulse_samples=10, freq_sample_time_ms=100):
        """Calculate duty cycle (%) and frequency (Hz)."""
        pw_us = self.pulse_width_us(pulse_samples)
        period_ns, freq_hz, _ = self._freq.measure(freq_sample_time_ms)

        if period_ns == 0:
            return 0.0, 0.0
        
        duty = (pw_us * 1000) / period_ns * 100  # Convert us -> ns
        return round(duty, 1), freq_hz
    
    def voltage(self, samples=16):
        total = 0

        for _ in range(samples):
            total += self.adc.read_u16()

        raw = total / samples
        return round((raw / 65535) * config.VREF, 2)

    def voltage_state(self, voltage=None):
        if voltage is None:
            voltage = self.voltage()

        if voltage < config.INPUT_THRESHOLD_LOW:
            return "LOW"

        if voltage > config.INPUT_THRESHOLD_HIGH:
            return "HIGH"

        return "MID"


