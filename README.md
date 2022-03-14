# Badger2040 - Life counter

A Magic the Gathering focused game counter that runs on the badger2040. I'm hoping to have both the software and CAD models that enable making a compact and robust digital life counter that builds on a MicroPython runtime and the badger2040 hardware.

### Status

This project is an early proof of concept. How this project behaves, performs, and appearances are all in flux.

Currently working on getting the following working:

* Multi-category tracking. Going to start with a fixed set of counters (life, infect, experience) as those are most commonly used in commander. The display 'widgets' could be handled more abstractly in the future.
* Input handling and screen refreshing. I would like to get a smooth UX between the button handling and screen updates. I still need to improve debouncing and tuning refresh delays to reduce lag.
* Graphics. Currently, I'm only using text, but I would like to get an icon sheet or some graphics for the categories and perhaps even have icons only be a display mode.

Future Roadmap:

* Custom categories. Pick your mix of top 3 or 4 counters. This could be a flash time decision, or some UX could be built to select and sort categories.
* Persistent configuration. After categories and layout are chosen those choices should persist.
* Options. Could have preferences for:
    * icons/icons+text display modes
    * dark/light theme

### Flashing

1. install `rshell` with `pip install rshell`
2. Plug the device in.
3. activate `rshell` in this directory.
4. In the rshell prompt `cp main.py /main.py`


## References

- API docs for badger2040 https://github.com/pimoroni/pimoroni-pico/tree/main/micropython/modules/badger2040
- Rshell docs https://github.com/dhylands/rshell
