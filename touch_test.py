from evdev import (InputDevice, ecodes)
from select import select

def touch_pos_to_coord(pos):
    x, y = pos
    lcd_x = min(max(0, int(480 * (y - 3750) / (200 - 3750))), 479)
    lcd_y = min(max(0, int(320 * (x - 400) / (3800 - 400))), 319)
    return (lcd_x, lcd_y)


# A mapping of file descriptors (integers) to InputDevice instances.
dev = InputDevice('/dev/input/event0')
touched = False
x = 0
y = 0
while True:
    r, w, c = select([dev.fd], [], [])
    for fd in r:
        for event in dev.read():
            if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                if event.value:
                    touched = True
                    x = y = -1
                else:
                    touched = False
                    print('released')
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    x = event.value
                if event.code == ecodes.ABS_Y:
                    y = event.value
                if touched and x >= 0 and y >= 0:
                    x, y = touch_pos_to_coord((x, y))
                    print('touched ({}, {})'.format(x, y))
                    touched = False 
