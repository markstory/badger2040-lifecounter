import badger2040
import machine
import time

badger = badger2040.Badger2040()

MODES = ('life', 'poison', 'exp')
class State:
    refresh = True
    mode = 'life'
    life = 40
    poison = 0
    exp = 0

    def get_value(self) -> str:
        if state.mode == 'life':
            return str(self.life)
        if state.mode == 'poison':
            return str(self.poison)
        if state.mode == 'exp':
            return str(self.exp)
        return "n/a"

    def __repr__(self):
        return "State<refresh={} mode={} life={} poison={} exp={}>".format(
            self.refresh, self.mode, self.life, self.poison, self.exp
        )

state = State()


# Button handlers {{{
def next_mode(pin):
    state.refresh = True
    try:
        index = MODES.index(state.mode)
    except:
        index = 0
    index = index + 1
    if index >= len(MODES):
        index = 0
    state.mode = MODES[index]

def increment(pin):
    state.refresh = True
    if state.mode == 'life':
        state.life += 1
    elif state.mode == 'poison':
        state.poison += 1
    elif state.mode == 'exp':
        state.exp += 1

def decrement(pin):
    state.refresh = True
    if state.mode == 'life':
        state.life -= 1
    elif state.mode == 'poison':
        state.poison -= 1
    elif state.mode == 'exp':
        state.exp -= 1
# }}}

# Button definitions {{{
button_a = machine.Pin(badger2040.BUTTON_A, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_b = machine.Pin(badger2040.BUTTON_B, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_c = machine.Pin(badger2040.BUTTON_C, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_up = machine.Pin(badger2040.BUTTON_UP, machine.Pin.IN, machine.Pin.PULL_DOWN)
button_down = machine.Pin(badger2040.BUTTON_DOWN, machine.Pin.IN, machine.Pin.PULL_DOWN)
# }}}

# Button handler wiring {{{
button_a.irq(trigger=machine.Pin.IRQ_RISING, handler=next_mode)
# button_b.irq(trigger=machine.Pin.IRQ_RISING, handler=button)
# button_c.irq(trigger=machine.Pin.IRQ_RISING, handler=button)

button_up.irq(trigger=machine.Pin.IRQ_RISING, handler=increment)
button_down.irq(trigger=machine.Pin.IRQ_RISING, handler=decrement)
# }}}

# Drawing {{{
def draw_life():
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

def draw_poison():
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

def draw_exp():
    badger.pen(0)
    badger.thickness(3)
    badger.text(str(state.exp), 230, 45, scale=2.0, rotation=-90)

    badger.thickness(1)
    badger.text('exp', 260, 40, scale=0.50, rotation=-90)
    if state.mode == 'exp':
        badger.line(268, 45, 268, 12)
# }}}

#
# Main Program Loop
#
badger.update_speed(badger2040.UPDATE_FAST)
while True:
    if state.refresh:
        state.refresh = False
        badger.pen(15)
        badger.clear()

        # Draw life
        draw_life()
        draw_poison()
        draw_exp()
        badger.update()

    time.sleep(0.1)
