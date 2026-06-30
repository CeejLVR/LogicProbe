from machine import Pin, PWM
import utime
import config
import uasyncio

# --- Safe Mode Check (GP18 override before anything else) ---
failsafe_pin = Pin(18, Pin.IN, Pin.PULL_UP)
if not failsafe_pin.value():
    config.SAFE_MODE = True

print("SAFE MODE:", config.SAFE_MODE)

# Imports after config
import display
display.clear()
import logic
from encoder import RotaryEncoder
from signal_analyzer import SignalAnalyzer
analyzer = SignalAnalyzer(config.INPUT_PIN)
encoder = RotaryEncoder(config.A_PIN, config.B_PIN, config.PSH_BTN)
last_encoder_event = 0

def handle_button():
    global freq_min, freq_max, last_button_state

    pressed = encoder.button_pressed()
    current_button_state = 0 if pressed else 1

    if last_button_state == 1 and current_button_state == 0:
        if current_mode == "edge_count":
            logic.reset_pulse_count()
        elif current_mode == "frequency":
            freq_min = None
            freq_max = None

    last_button_state = current_button_state


async def handle_encoder():
    global last_encoder_event
    while True:
        delta = encoder.read()
        if delta != 0:
            now = utime.ticks_ms()
            # 200ms UI debounce
            if utime.ticks_diff(now, last_encoder_event) > 200:
                last_encoder_event = now
                switch_mode(delta)
        handle_button()
        await uasyncio.sleep_ms(1)


# Initialize IRQ only if not in safe mode
if not config.SAFE_MODE:
    logic.init_monitor()

# Modes
modes = ["logic", "frequency", "pulse", "duty", "voltage", "edge_count"]
current_mode = "logic"
display.show_mode(current_mode)
last_mode_change = utime.ticks_ms()

freq_min = None
freq_max = None
last_button_state = 1

# Test PWM generator (use scope to verify)
if config.TEST_PWM:
    test_pwm = PWM(Pin(17))
    test_pwm.freq(5000)  # 5 kHz
    test_pwm.duty_u16(32768)  # 50%


# Buttons

# Display control variables
display_state = "normal"  # could be "normal" or "show_number"
number_to_show = None

# --- Mode Switching ---
def switch_mode(delta):
    global current_mode, last_mode_change, display_state

    now = utime.ticks_ms()

    # debounce/cooldown
    if utime.ticks_diff(now, last_mode_change) < 150:
        return

    idx = (modes.index(current_mode) + delta) % len(modes)
    current_mode = modes[idx]

    last_mode_change = now
    display_state = "normal"
    display.show_mode(current_mode)





# --- Update Display ---
async def periodic_update():
    global display_state, number_to_show
    while True:
        if display_state == "show_number" and number_to_show is not None:
            # Keep showing the number on display
            display.show_number(number_to_show)
        else:
            # Normal update loop
            if current_mode == "logic":
                display.show_logic_detail(
                    logic.read_level(),
                    logic.last_direction(),
                    logic.edge_age_ms(),
                )

            elif current_mode == "frequency":
                freq = analyzer.frequency()
                global freq_min, freq_max
                if freq > 0:
                    freq_min = freq if freq_min is None else min(freq_min, freq)
                    freq_max = freq if freq_max is None else max(freq_max, freq)
                display.show_frequency_detail(freq, freq_min, freq_max)

            elif current_mode == "pulse":
                width = analyzer.pulse_width_us()
                display.show_pulse(width)

            elif current_mode == "duty":
                duty, freq = analyzer.duty_cycle()
                display.show_duty_cycle(duty, freq)

            elif current_mode == "voltage":
                voltage = analyzer.voltage()
                state = analyzer.voltage_state(voltage)
                display.show_voltage(voltage, state)

            elif current_mode == "edge_count":
                display.show_edge_count(logic.get_pulse_count())
        await uasyncio.sleep_ms(300)  # Display update rate

# --- Run everything ---
async def main():
    tasks = [
        handle_encoder(),
        periodic_update(),
    ]
    await uasyncio.gather(*tasks)

uasyncio.run(main())
