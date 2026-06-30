# logic.py

from machine import Pin
import config
import utime
import micropython

_last_edge_us = 0
_last_level = 0
_last_direction = None
_last_debounce_us = 0
_pulse_count = 0

_input_pin = Pin(config.INPUT_PIN, Pin.IN, Pin.PULL_DOWN)

DEBOUNCE_US = config.DEBOUNCE_US

_rising_cb = None
_falling_cb = None
_change_cb = None
_async_hooks = []


def _edge_handler(pin):
    global _last_edge_us, _last_level, _last_direction
    global _last_debounce_us, _pulse_count

    now = utime.ticks_us()
    level = pin.value()

    if utime.ticks_diff(now, _last_debounce_us) < DEBOUNCE_US:
        return

    _last_debounce_us = now
    _last_edge_us = now
    _last_level = level
    _last_direction = "rise" if level else "fall"

    if level == 1:
        _pulse_count += 1
        if _rising_cb:
            _rising_cb(now)
    else:
        if _falling_cb:
            _falling_cb(now)

    if _change_cb:
        _change_cb(level, now)

    for hook in _async_hooks[:]:
        if hook["target"] == level:
            hook["triggered"] = True


def init_monitor():
    global _last_level

    _last_level = _input_pin.value()
    micropython.alloc_emergency_exception_buf(100)
    _input_pin.irq(
        trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
        handler=_edge_handler,
    )


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
    return _input_pin.value()


def last_direction():
    return _last_direction


def edge_age_ms():
    if _last_edge_us == 0:
        return None
    return utime.ticks_diff(utime.ticks_us(), _last_edge_us) // 1000


def last_edge_time():
    return _last_edge_us


def get_pulse_count():
    return _pulse_count


def reset_pulse_count():
    global _pulse_count
    _pulse_count = 0


async def wait_for_edge(target_level=1):
    import uasyncio

    hook = {"target": target_level, "triggered": False}
    _async_hooks.append(hook)

    try:
        while not hook["triggered"]:
            await uasyncio.sleep_ms(1)
    finally:
        _async_hooks.remove(hook)

    return utime.ticks_us()