import badger2040
import machine
import time
import utime

badger = badger2040.Badger2040()

# Application State {{{
MODES = ('life', 'poison', 'exp')

class State:
    _prev_state = None

    def __init__(self, mode='life', life=40, poison=0, exp=0):
        self.mode = mode
        self.life = life
        self.poison = poison
        self.exp = exp

    def flushed(self):
        """
        Call when updates to the UI are applied so that
        we can 'diff' the next render more efficiently.
        """
        self._prev_state = State(
            mode=self.mode,
            life=self.life,
            poison=self.poison,
            exp=self.exp
        )

    def reset(self):
        self.mode = 'life'
        self.life = 40
        self.poison = 0
        self.exp = 0

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

# Button definitions {{{
button_a = machine.Pin(badger2040.BUTTON_A, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_b = machine.Pin(badger2040.BUTTON_B, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_c = machine.Pin(badger2040.BUTTON_C, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_up = machine.Pin(badger2040.BUTTON_UP, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_down = machine.Pin(badger2040.BUTTON_DOWN, machine.Pin.IN, machine.Pin.PULL_DOWN)
# }}}

# Button handler wiring {{{
button_a.irq(trigger=machine.Pin.IRQ_FALLING, handler=next_mode)
button_b.irq(trigger=machine.Pin.IRQ_FALLING, handler=reset)
# button_c.irq(trigger=machine.Pin.IRQ_RISING, handler=button)

button_up.irq(trigger=machine.Pin.IRQ_FALLING, handler=increment)
button_down.irq(trigger=machine.Pin.IRQ_FALLING, handler=decrement)
# }}}

# Drawing {{{
def draw_life():
    badger.pen(16)
    badger.rectangle(0, 0, 130, 128)

    badger.pen(0)
    badger.thickness(6)
    if state.life < 10:
        badger.text(str(state.life), 70, 90, scale=3.0, rotation=-90)
    elif state.life < 100:
        badger.text(str(state.life), 70, 120, scale=3.0, rotation=-90)
    else:
        badger.text(str(state.life), 90, 125, scale=2.0, rotation=-90)

    badger.thickness(1)
    badger.text('health', 120, 85, scale=0.50, rotation=-90)
    if state.mode == 'life':
        badger.line(126, 88, 126, 40)

    # affected region x, y, w, h
    return [10, 0, 128, 128]

def draw_poison():
    badger.pen(16)
    badger.rectangle(180, 64, 296, 128)

    value = state.poison
    if value >= 10:
        value = 'X'

    badger.pen(0)
    badger.thickness(3)
    badger.text(str(value), 230, 115, scale=2.0, rotation=-90)

    badger.thickness(1)
    badger.text('poison', 260, 120, scale=0.50, rotation=-90)
    if state.mode == 'poison':
        badger.line(268, 120, 268, 75)
    return [180, 64, 270, 128]

def draw_exp():
    badger.pen(16)
    badger.rectangle(180, 0, 296, 64)

    badger.pen(0)
    badger.thickness(3)
    badger.text(str(state.exp), 230, 45, scale=2.0, rotation=-90)

    badger.thickness(1)
    badger.text('exp', 260, 40, scale=0.50, rotation=-90)
    if state.mode == 'exp':
        badger.line(268, 45, 268, 12)
    # affected region x, y, w, h
    return [180, 0, 270, 64]

def full_render():
    badger.pen(15)
    badger.clear()

    draw_life()
    draw_poison()
    draw_exp()
    badger.update()
    state.flushed()

def incremental_render():
    if state.is_changed('mode'):
        full_render()
        return

    updates = []
    if state.is_changed('life'):
        updates.append(draw_life())
    if state.is_changed('poison'):
        updates.append(draw_poison())
    if state.is_changed('exp'):
        updates.append(draw_exp())
    for update in filter(lambda x: x, updates):
        # Flush updates to affected regions.
        badger.partial_update(*update)
        # Sync previous state for next partial refresh.
        state.flushed()
# }}}

#
# Main Program Loop
#
badger.update_speed(badger2040.UPDATE_FAST)
full_render()

while True:
    current_time = utime.ticks_ms()
    # Wait 500ms since the last update as refreshing the
    # display blocks other actions and causes button presses
    # to misbehave.
    if current_time - last_press > 500:
        incremental_render()
    time.sleep(0.3)
