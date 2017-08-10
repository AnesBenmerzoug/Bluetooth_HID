#!/usr/bin/python
#
# Reads local mouse events and forwards them to the btk_server DBUS service
#
#

import dbus
import dbus.service
import dbus.mainloop.glib
import time
import evdev  # used to get input from the mouse
from evdev import InputDevice, ecodes


# define a client to listen to local mouse events
class Mouse:
    def __init__(self):
        # the structure for a bluetooth mouse input report (size is 6 bytes)

        self.state = [
            0xA1,  # this is an input report
            0x02,  # Usage report = Mouse
            0x00,  # Bit array for Buttons ( Bits 0...4 : Buttons 1...5, Bits 5...7 : Unused )
            0x00,  # Rel X
            0x00,  # Rel Y
            0x00,  # Mouse Wheel
        ]

        print("Setting up DBus Client")

        self.bus = dbus.SystemBus()
        self.bluetoothservice = self.bus.get_object('org.upwork.HidBluetoothService', "/org/upwork/HidBluetoothService")
        self.iface = dbus.Interface(self.bluetoothservice, 'org.upwork.HidBluetoothService')

        print("Waiting for mouse")

        # keep trying to find a mouse
        have_dev = False
        count = 0
        NUMBER_OF_TRIES = 100

        while have_dev is False and count < NUMBER_OF_TRIES:
            try:
                # try and get a mouse - loop through all devices and try to find a mouse
                devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
                for device in reversed(devices):
                    if "mouse" in device.name.lower():
                        print("Found a keyboard with the keyword 'mouse'")
                        print("device name is " + device.name)
                        self.dev = InputDevice(device.fn)
                        have_dev = True
                        break
            except OSError:
                print("Mouse not found, waiting 3 seconds and retrying")
                time.sleep(3)
            count += 1
        
        if not have_dev:
            print("Mouse not found after " + str(NUMBER_OF_TRIES) + " tries.")
            return
        else:
            print("Mouse Found")
            print("Starting mouse event loop")
            self.event_loop()

    # take care of mouse buttons
    def change_state_button(self, event):
        if event.code == ecodes.BTN_LEFT:
            print("Left Mouse Button Pressed")
            self.state[2] = event.value
        elif event.code == ecodes.BTN_RIGHT:
            print("Right Mouse Button Pressed")
            self.state[2] = 2 * event.value
        elif event.code == ecodes.BTN_MIDDLE:
            print("Middle Mouse Button Pressed")
            self.state[2] = 3 * event.value
        self.state[3] = 0x00
        self.state[4] = 0x00
        self.state[5] = 0x00

    # take care of mouse movements
    def change_state_movement(self, event):
        if event.code == ecodes.REL_X:
            self.state[3] = event.value & 0xFF
        elif event.code == ecodes.REL_Y:
            self.state[4] = event.value & 0xFF
        elif event.code == ecodes.REL_WHEEL:
            self.state[5] = event.value & 0xFF

    # poll for mouse events
    def event_loop(self):
        for event in self.dev.read_loop():
            if event.type == ecodes.EV_KEY and event.value < 2:
                self.change_state_button(event)
            elif event.type == ecodes.EV_REL:
                self.change_state_movement(event)
            try:
                self.send_input()
            except:
                print("Couldn't send mouse movement/button press")
                return

    # forward mouse events to the dbus service
    def send_input(self):
        self.iface.send_mouse(self.state[2], self.state[3:6])


if __name__ == "__main__":
    print("Setting up mouse")
    Mouse()
