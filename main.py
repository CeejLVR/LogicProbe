from machine import Timer, Pin, PWM
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
from signal_analyzer import SignalAnalyzer
analyzer = SignalAnalyzer(config.INPUT_PIN, mode="cpu")  # "cpu" or "pio" (cpu for freq < 1kHz)

# Initialize IRQ only if not in safe mode
if not config.SAFE_MODE:
    logic.init_monitor()

# Modes
modes = ["logic", "frequency", "pulse", "duty", "edge_time", "edge_counter"]
current_mode = "logic"
display.show_mode(current_mode)
last_mode_change = utime.ticks_ms()

# Test PWM generator (use scope to verify)
test_pwm = PWM(Pin(17))
test_pwm.freq(5000)  # 5 kHz
test_pwm.duty_u16(32768)  # 50%

# Buttons
mode_button = Pin(config.MODE_BUTTON_PIN, Pin.IN, Pin.PULL_UP)
edge_count_button = Pin(config.EDGE_BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# Display control variables
display_state = "normal"  # could be "normal" or "show_number"
number_to_show = None

# --- Mode Switching ---
def switch_mode():
    global current_mode, last_mode_change, display_state
    idx = (modes.index(current_mode) + 1) % len(modes)
    current_mode = modes[idx]
    last_mode_change = utime.ticks_ms()
    display_state = "normal"  # Reset display state when switching modes
    display.show_mode(current_mode)

async def monitor_mode_switch():
    global last_mode_change
    while True:
        if not mode_button.value() and utime.ticks_diff(utime.ticks_ms(), last_mode_change) > 300:
            switch_mode()
        await uasyncio.sleep_ms(50)


# --- Edge Counting Task ---
async def monitor_button_for_edges():
    global display_state, number_to_show
    while True:
        count = await analyzer.edge_count_while_held(edge_count_button)
        if count is not None:
            number_to_show = count
            display_state = "show_number"
            display.show_number(count)
        await uasyncio.sleep_ms(300)  # Avoid double-trigger
        
async def poll_edge_counter():
    while True:
        analyzer.update()  # This calls CpuEdgeCounter.update() if in cpu mode
        await uasyncio.sleep_ms(1)


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
                display.show_logic(logic.read_level())
            elif current_mode == "frequency":
                display.show_frequency(analyzer.frequency())
            elif current_mode == "pulse":
                width = analyzer.pulse_width_us()
                display.show_pulse(width)
            elif current_mode == "duty":
                duty, freq = analyzer.duty_cycle()
                display.show_duty_cycle(duty, freq)
            elif current_mode == "edge_time":
                rise, fall = analyzer.rise_fall_times_ns()
                display.show_rise_fall(round(rise, 2), round(fall, 2))
            elif current_mode == "edge_counter":
                edges = analyzer.edge_count()
                display.show_number(edges)
        await uasyncio.sleep_ms(100)  # Display update rate



# Button to clear number display and return to normal display mode
#               --not currently in use--
async def monitor_clear_display_button():
    global display_state
    clear_button = Pin(config.CLEAR_DISPLAY_BUTTON_PIN, Pin.IN, Pin.PULL_UP)  # You'd need a button wired for this
    while True:
        if not clear_button.value() and display_state == "show_number":
            display_state = "normal"
            display.clear()
            display.show_mode(current_mode)
            await uasyncio.sleep_ms(500)  # Debounce
        await uasyncio.sleep_ms(50)

# --- Run everything ---
async def main():
    tasks = [
        monitor_mode_switch(),
        monitor_button_for_edges(),
        periodic_update(),
        # monitor_clear_display_button(),  # Uncomment to use clear display button
        poll_edge_counter(),
    ]
    await uasyncio.gather(*tasks)

uasyncio.run(main())


