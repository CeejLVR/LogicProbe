# logic.py

from machine import Pin
import config
import utime
import micropython

# Internal state
_last_edge_us = 0
_last_level = 0
_last_debounce_us = 0
_pulse_count = 0

# debounce time 
DEBOUNCE_US = config.DEBOUNCE_US

# User-defined callbacks
_rising_cb = None
_falling_cb = None
_change_cb = None

# Async hooks for uasyncio-compatible funcs
_async_hooks = []


def _edge_handler(pin):
    global _last_edge_us, _last_level, _last_debounce_us, _pulse_count

    now = utime.ticks_us()
    level = pin.value()

    # Debounce to avoid false triggers
    if utime.ticks_diff(now, _last_debounce_us) < DEBOUNCE_US:
        return
    _last_debounce_us = now

    _last_edge_us = now
    _last_level = level

    if level == 1:
        _pulse_count += 1
        if _rising_cb:
            _rising_cb(now)
    else:
        if _falling_cb:
            _falling_cb(now)

    if _change_cb:
        _change_cb(level, now)

    # Notify async func
    for hook in _async_hooks:
        if hook['target'] == level:
            hook['triggered'] = True


def init_monitor():
    """Attach IRQ handler to input pin"""
    pin = Pin(config.INPUT_PIN, Pin.IN, Pin.PULL_DOWN)
    micropython.alloc_emergency_exception_buf(100)
    pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=_edge_handler)


def on_rising(callback):
    global _rising_cb
    _rising_cb = callback


def on_falling(callback):
    global _falling_cb
    _falling_cb = callback


def on_change(callback):
    global _change_cb
    _change_cb = callback


def read_level():
    return _last_level


def last_edge_time():
    return _last_edge_us


def get_pulse_count():
    return _pulse_count


def reset_pulse_count():
    global _pulse_count
    _pulse_count = 0


# Async interface for uasyncio
async def wait_for_edge(target_level=1):
    import uasyncio
    hook = {'target': target_level, 'triggered': False}
    _async_hooks.append(hook)

    try:
        while not hook['triggered']:
            await uasyncio.sleep_ms(1)
    finally:
        _async_hooks.remove(hook)

    return utime.ticks_us()



'''
# Example usage of the logic module
import logic
import uasyncio


def rising_handler(timestamp):
    print("Rising edge at", timestamp)

def falling_handler(timestamp):
    print("Falling edge at", timestamp)

def edge_change(level, timestamp):
    print(f"Level changed to {level} at {timestamp} µs")

logic.init_monitor()
logic.on_rising(rising_handler)
logic.on_falling(falling_handler)
logic.on_change(edge_change)

# Count pulses
print("Total pulses:", logic.get_pulse_count())

# Async use
async def watch_edges():
    while True:
        ts = await logic.wait_for_edge(1)
        print("Async ↑ detected at", ts)

uasyncio.run(watch_edges())
'''
