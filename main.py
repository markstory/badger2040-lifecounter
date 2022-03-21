import badger2040
import machine
import time
import utime

# Public Configuration Constants
STARTING_LIFE = 40

# Controls both the update speed of the display
# but also the fastest frequency the UI will update.
#
# FAST & TURBO = 0.3
# Others = 0.5
REFRESH_RATE = badger2040.UPDATE_TURBO

# Set to max=4.0, min = 3.2 if using LiIon
# and max = 2.5, min = 2.0 if using NiMH
MAX_BATTERY_VOLTAGE = 2.5
MIN_BATTERY_VOLTAGE = 1.9


# Application Internal State {{{
NUM_BATT_BARS = 5
MODES = ('life', 'poison', 'exp')

class State:
    _prev_state = None

    def __init__(self, mode='life', life=STARTING_LIFE, poison=0, exp=0, battery=-1):
        self.mode = mode
        self.life = life
        self.poison = poison
        self.exp = exp
        self.battery = battery 

    def flushed(self):
        """
        Call when updates to the UI are applied so that
        we can 'diff' the next render more efficiently.
        """
        self._prev_state = State(
            mode=self.mode,
            life=self.life,
            poison=self.poison,
            exp=self.exp,
            battery=self.battery
        )

    def reset(self):
        self.mode = 'life'
        self.life = STARTING_LIFE
        self.poison = 0
        self.exp = 0
        self.battery = -1

    def is_changed(self, prop):
        if not self._prev_state:
            return False
        return getattr(self._prev_state, prop) != getattr(self, prop)

    def __repr__(self):
        return "State<mode={} life={} poison={} exp={}>".format(
            self.mode, self.life, self.poison, self.exp
        )

state = State()
# }}}

# Button handlers {{{
last_press = 0
def debounce(wait=200):
    """
    IRQ handlers can be fired multiple times due to contact chatter.
    Since we can't handle this with hardware we use a simple timer
    for all the button presses as this program doesn't need any
    concurrent button handling.
    """
    def decorator(func):
        def inner(*args, **kwargs):
            global last_press
            call_time = utime.ticks_ms()
            allowed = call_time - last_press >= wait
            last_press = call_time
            if allowed:
                return func(*args, **kwargs)
        return inner
    if callable(wait):
        return decorator(200)
    else:
        return decorator


@debounce(wait=200)
def next_mode(pin):
    try:
        index = MODES.index(state.mode)
    except:
        index = 0
    index = index + 1
    if index >= len(MODES):
        index = 0
    state.mode = MODES[index]

@debounce(wait=200)
def increment(pin):
    print('increment start', state.life)
    if state.mode == 'life':
        state.life = state.life + 1
    elif state.mode == 'poison':
        state.poison = state.poison + 1
    elif state.mode == 'exp':
        state.exp = state.exp + 1

@debounce(wait=200)
def decrement(pin):
    if state.mode == 'life':
        state.life = state.life - 1
    elif state.mode == 'poison':
        state.poison = state.poison - 1
    elif state.mode == 'exp':
        state.exp = state.exp - 1

@debounce(wait=200)
def reset(pin):
    state.reset()

# }}}

# Pin definitions {{{
button_a = machine.Pin(badger2040.BUTTON_A, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_b = machine.Pin(badger2040.BUTTON_B, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_c = machine.Pin(badger2040.BUTTON_C, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_up = machine.Pin(badger2040.BUTTON_UP, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_down = machine.Pin(badger2040.BUTTON_DOWN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# Battery indicator pins.
vbat_adc = machine.ADC(badger2040.PIN_BATTERY)
vref_adc = machine.ADC(badger2040.PIN_1V2_REF)
vref_en = machine.Pin(badger2040.PIN_VREF_POWER)

vref_en.init(machine.Pin.OUT)
vref_en.value(0)
# }}}

# Button handler wiring {{{
button_a.irq(trigger=machine.Pin.IRQ_FALLING, handler=next_mode)
button_b.irq(trigger=machine.Pin.IRQ_FALLING, handler=reset)
# button_c.irq(trigger=machine.Pin.IRQ_RISING, handler=button)

button_up.irq(trigger=machine.Pin.IRQ_FALLING, handler=increment)
button_down.irq(trigger=machine.Pin.IRQ_FALLING, handler=decrement)
# }}}

# Battery reading {{{
def map_value(input, in_min, in_max, out_min, out_max):
    return (((input - in_min) * (out_max - out_min)) / (in_max - in_min)) + out_min

def read_battery():
    # Enable voltage reading
    vref_en.value(1)

    # Calculate the logical supply voltage as it will be lower than 3.3V when reading
    # from low batteries
    vdd = 1.24 * (65535 / vref_adc.read_u16())
    # 3 here is a gain value, not rounding of 3.3V
    vbat = (vbat_adc.read_u16() / 65535) * 3 * vdd
    if vbat < 0.5:
        # No battery attached.
        state.battery = -1
        return

    # Disable voltage reading
    vref_en.value(0)

    # Scale value so it fits between 0 - NUM_BATT_BARS
    #print(f'vbat={vbat} min={MIN_BATTERY_VOLTAGE} max={MAX_BATTERY_VOLTAGE} num={NUM_BATT_BARS}')
    level = int(map_value(vbat, MIN_BATTERY_VOLTAGE, MAX_BATTERY_VOLTAGE, 0, NUM_BATT_BARS))
    #print(f'level={level} num={NUM_BATT_BARS}')
    if abs(state.battery - level) > 1:
        state.battery = level
# }}}


# Drawing {{{
FILL_BG_LIGHT = 12
FILL_BLACK = 0
FILL_WHITE = 15

def draw_life():
    badger.pen(FILL_WHITE)
    badger.rectangle(16, 0, 130, 128)

    badger.pen(FILL_BLACK)
    badger.thickness(6)
    if state.life < 10:
        badger.text(str(state.life), 80, 90, scale=3.0, rotation=-90)
    elif state.life < 100:
        badger.text(str(state.life), 80, 120, scale=3.0, rotation=-90)
    else:
        badger.text(str(state.life), 100, 125, scale=2.0, rotation=-90)

    badger.thickness(1)
    badger.text('health', 130, 85, scale=0.50, rotation=-90)
    if state.mode == 'life':
        badger.line(136, 88, 136, 40)

    # affected region x, y, w, h
    return [16, 0, 144, 144]

def draw_poison():
    badger.pen(FILL_WHITE)
    badger.rectangle(180, 64, 296, 128)

    value = state.poison
    if value >= 10:
        value = 'X'

    badger.pen(FILL_BLACK)
    badger.thickness(3)
    badger.text(str(value), 230, 115, scale=2.0, rotation=-90)

    badger.thickness(1)
    badger.text('poison', 260, 120, scale=0.50, rotation=-90)
    if state.mode == 'poison':
        badger.line(268, 120, 268, 75)
    return [180, 64, 270, 128]

def draw_exp():
    badger.pen(FILL_WHITE)
    badger.rectangle(180, 0, 296, 64)

    badger.pen(FILL_BLACK)
    badger.thickness(3)
    badger.text(str(state.exp), 230, 45, scale=2.0, rotation=-90)

    badger.thickness(1)
    badger.text('exp', 260, 40, scale=0.50, rotation=-90)
    if state.mode == 'exp':
        badger.line(268, 45, 268, 12)
    # affected region x, y, w, h
    return [180, 0, 270, 64]

def draw_battery():
    width = 22
    height = 10
    nub_offset = 2
    nub_width = 2
    border_width = 1
    borders = border_width * 2

    badger.thickness(1)

    # Clear inner area.
    badger.pen(FILL_WHITE)
    badger.rectangle(border_width, border_width, height - border_width, width - border_width)

    # Outer rectangle
    badger.pen(FILL_BLACK)
    badger.rectangle(0, 0, height, width)

    # Inner area clear and set to dim
    badger.pen(FILL_BG_LIGHT)
    badger.rectangle(border_width + 1, border_width + 1, height - borders - 1, width - borders - 1)

    # Battery nub
    badger.pen(FILL_BLACK)
    badger.rectangle(nub_offset, width, 6, nub_width)

    # Hole for drained area.
    if state.battery < 1:
        # Totally empty or unplugged
        badger.pen(FILL_BLACK)
        badger.thickness(2)
        badger.line(border_width, border_width, height - border_width, width - border_width)
    else:
        # Fill from right side to the left to indicate a partial or full battery.
        badger.pen(FILL_BLACK)
        bar_px = state.battery * int((width - borders) / NUM_BATT_BARS)
        badger.rectangle(border_width, border_width, height - border_width, bar_px)

    return [0, 0, 16, 32]

def full_render():
    badger.pen(FILL_WHITE)
    badger.clear()

    draw_battery()
    draw_life()
    draw_poison()
    draw_exp()
    badger.update()
    state.flushed()

def incremental_render():
    if state.is_changed('mode'):
        full_render()
        return True

    updates = []
    if state.is_changed('life'):
        updates.append(draw_life())
    if state.is_changed('poison'):
        updates.append(draw_poison())
    if state.is_changed('exp'):
        updates.append(draw_exp())
    if state.is_changed('battery'):
        updates.append(draw_battery())
    for update in filter(lambda x: x, updates):
        # Flush updates to affected regions.
        badger.partial_update(*update)
        # Sync previous state for next partial refresh.
        state.flushed()
    return len(updates) > 0

_render_reset = 10
if REFRESH_RATE == badger2040.UPDATE_TURBO:
    _render_reset = 5

# Start at _render_reset to force a refresh at boot.
_render_counter = _render_reset

def render():
    global _render_counter

    # Refresh the entire screen occasionally.
    # Because we're using turbo updates the screen
    # collects jank.
    if _render_counter >= _render_reset:
        full_render()
        _render_counter = 0
    else:
        updated = incremental_render()
        if updated:
            # Count the render pass if we did work
            _render_counter += 1
# }}}

#
# Main Program Loop
#
badger = badger2040.Badger2040()

# Initial Render done slow to wipe screen better.
badger.update_speed(badger2040.UPDATE_MEDIUM)
read_battery()
render()
badger.update_speed(REFRESH_RATE)


sleep_value = 0.5
if REFRESH_RATE in [badger2040.UPDATE_FAST, badger2040.UPDATE_TURBO]:
    sleep_value = 0.3

while True:
    current_time = utime.ticks_ms()
    # Wait 500ms since the last update as refreshing the
    # display blocks other actions and causes button presses
    # to misbehave.
    if current_time - last_press > 500:
        read_battery()
        render()
    time.sleep(sleep_value)
