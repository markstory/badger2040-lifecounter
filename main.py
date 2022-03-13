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
    print(state)

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

#
# Main Program Loop
#
while True:
    if state.refresh:
        state.refresh = False
        badger.pen(15)
        badger.clear()

        badger.pen(0)
        badger.thickness(4)
        badger.text(state.get_value(), 30, 30, 2.0)

        badger.thickness(2)
        badger.text(state.mode, 45, 60, 1.0)
        badger.update()
    time.sleep(0.1)
