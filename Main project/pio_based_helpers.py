import rp2
from machine import Pin
import utime
import config
# Constants
CLOCK_NS = config.CLOCK_NS
DEFAULT_TIMEOUT_MS = config.DEFAULT_TIMEOUT_MS

# -----------------------------------------------------------------------------
# Pulse Width Measurement (SM0)
# -----------------------------------------------------------------------------
@rp2.asm_pio()
def pulse_width_capture():
    wrap_target()
    wait(0, pin, 0)       # Sync to LOW
    wait(1, pin, 0)       # Wait for rising edge
    mov(x, invert(null))  # Initialize counter
    label("count_high")
    jmp(x_dec, "next")    # Decrement counter
    label("next")
    jmp(pin, "count_high") # Continue while HIGH
    mov(isr, x)           # Store counter
    push(noblock)         # Send to CPU
    wrap()

class PrecisionPulse:
    def __init__(self, pin_num):
        self.sm = rp2.StateMachine(
            0, pulse_width_capture,
            freq=125_000_000,
            in_base=Pin(pin_num),
            jmp_pin=Pin(pin_num)
        )
        self.active = False

    def measure(self, samples=10, timeout_ms=DEFAULT_TIMEOUT_MS):
        self.sm.active(1)
        results = []
        start_time = utime.ticks_ms()
        
        try:
            for _ in range(samples):
                while not self.sm.rx_fifo():
                    if utime.ticks_diff(utime.ticks_ms(), start_time) > timeout_ms:
                        return 0.0
                results.append((0xFFFFFFFF - self.sm.get()) * 2 * CLOCK_NS / 1000)
            return round((sum(results) / len(results)), 2) if results else 0.0
        finally:
            self.sm.active(0)

# -----------------------------------------------------------------------------
# Edge Timing (Rise/Fall) (SM1)
# -----------------------------------------------------------------------------
@rp2.asm_pio()
def edge_timing():
    wrap_target()
    wait(1, pin, 0)          # Wait for rising edge
    set(x, 31)               # Smaller counter
    
    # Measure HIGH duration
    label("rise")
    jmp(pin, "continue_rise") # Continue if pin still HIGH
    jmp("fall_start")         # Jump to fall measurement if pin LOW
    label("continue_rise") 
    jmp(x_dec, "rise")        # Decrement counter
    
    # Measure LOW duration
    label("fall_start")
    set(x, 31)
    label("fall")
    jmp(pin, "done")          # Jump if pin went HIGH
    jmp(x_dec, "fall")        # Continue counting LOW duration
    
    label("done")
    mov(isr, invert(x))       # Store result (0xFFFFFFFF - x)
    push(block)               # Send result
    wrap()
    
class EdgeTimer:
    def __init__(self, pin_num):
        self.sm = rp2.StateMachine(
            1, edge_timing,
            freq=125_000_000,  # 125 MHz (8 ns resolution)
            in_base=Pin(pin_num),
            jmp_pin=Pin(pin_num)
        )
        self.clock_ns = 8  # 8 ns per cycle

    def measure(self, samples=5, timeout_ms=1000):
        self.sm.active(1)
        self.sm.restart()  # Clear FIFO
        results = []
        start_time = utime.ticks_ms()

        try:
            for _ in range(samples):
                # Wait for 2 values (rise + fall)
                while self.sm.rx_fifo() < 2:
                    if utime.ticks_diff(utime.ticks_ms(), start_time) > timeout_ms:
                        return (0.0, 0.0)
                # Read and convert to nanoseconds
                rise_cycles = self.sm.get()  # First: rise time
                fall_cycles = self.sm.get()  # Second: fall time
                rise_ns = rise_cycles * self.clock_ns
                fall_ns = fall_cycles * self.clock_ns
                results.append((rise_ns, fall_ns))
            
            # Calculate averages
            avg_rise = sum(r[0] for r in results) / len(results)
            avg_fall = sum(r[1] for r in results) / len(results)
            return (avg_rise, avg_fall)
        finally:
            self.sm.active(0)
            
# -----------------------------------------------------------------------------
# Smart Frequency (Period + Edges) (SM2)
# -----------------------------------------------------------------------------
@rp2.asm_pio()
def measure_frequency():
    # Initial sync to first rising edge
    wait(0, pin, 0)       # Wait for LOW
    wait(1, pin, 0)       # Wait for first rising edge
    wrap_target()          # Start loop here
    
    # Wait for full period (falling then rising edge)
    wait(0, pin, 0)       # Wait for falling edge
    wait(1, pin, 0)       # Wait for next rising edge
    mov(isr, null)        # Push dummy value (0) to FIFO
    push()                # Signal one period completed
    wrap()                # Loop back to wrap_target



class FrequencyMeasure:
    def __init__(self, pin_num):
        self.pin = Pin(pin_num, Pin.IN)
        self.sm = rp2.StateMachine(
            2, measure_frequency,
            freq=125_000_000,  # 125 MHz (8 ns/cycle)
            in_base=self.pin,
            jmp_pin=self.pin
        )
        self.sm.active(0)

    def measure(self, sample_time_ms=100):
        self.sm.active(1)
        self.sm.restart()  # Clear FIFO and reset state
        start_time = utime.ticks_ms()
        edge_count = 0
        
        # Count edges for the duration
        while utime.ticks_diff(utime.ticks_ms(), start_time) < sample_time_ms:
            if self.sm.rx_fifo() > 0:
                self.sm.get()  # Discard dummy value
                edge_count += 1
        
        self.sm.active(0)
        
        if edge_count == 0:
            return 0, 0.0, 0  # No edges detected
        
        # Calculate results
        total_time_ns = sample_time_ms * 1_000_000  # ms -> ns
        avg_period_ns = total_time_ns / edge_count   # Average period
        freq_hz = edge_count * 1000 / sample_time_ms  # Frequency
        
        return avg_period_ns, freq_hz, edge_count


# -----------------------------------------------------------------------------
# Rotary Encoder (SM3)
# -----------------------------------------------------------------------------
# encoder.pio
@rp2.asm_pio()
def encoder():
    wrap_target()
    mov(x, invert(null))        # x = 0xFFFFFFFF
    label("read")
    in_(pins, 2)                # read both encoder pins into OSR
    mov(y, isr)                 # y = old state
    in_(pins, 2)                # read again for current state
    mov(isr, y)                 # swap
    jmp(x_dec, "continue")      # dummy delay for debounce
    label("continue")
    irq(block)                  # signal update
    push(noblock)               # push encoded state
    wrap()

from machine import Pin

class RotaryEncoder:
    def __init__(self, pin_a, pin_b):
        self.pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)

        self.last_state = (self.pin_a.value() << 1) | self.pin_b.value()

        self.position = 0

        self.transition_table = {
            0b0001:  1,
            0b0010: -1,
            0b0100: -1,
            0b0111:  1,
            0b1000:  1,
            0b1011: -1,
            0b1101: -1,
            0b1110:  1
        }

    def read(self):
        current_state = (self.pin_a.value() << 1) | self.pin_b.value()

        transition = (self.last_state << 2) | current_state

        self.last_state = current_state

        movement = self.transition_table.get(transition, 0)

        self.position += movement

        # one full detent
        if self.position >= 2:
            self.position = 0
            return 1

        elif self.position <= -2:
            self.position = 0
            return -1

        return 0
