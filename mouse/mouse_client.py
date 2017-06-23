#!/usr/bin/python
#
# Reads local mouse events and forwards them to the btk_server DBUS service
#
#

import os  # used to call external commands
import sys  # used to exit the script
import dbus
import dbus.service
import dbus.mainloop.glib
import time
import evdev  # used to get input from the mouse
from evdev import InputDevice, ecodes

#define a client to listen to local mouse events
class Mouse():
    def __init__(self):
        # the structure for a bluetooth mouse input report (size is 10 bytes)

        self.state = [
            0xA1,  # this is an input report
            0x02,  # Usage report = Mouse
            # Bit array for Button
            [0,  # Button 1
             0,  # Button 2
             0,  # Button 3
             0,  # Button 4
             0,  # Button 5
             0,  # Unused
             0,  # Unused
             0],  # Unused
            0x00,  # X
            0x00,  # Y
            0x00,  # Unused
            0x00,  # Unused
            0x00,  # Unused
        ]

        print "Setting up DBus Client"

        self.bus = dbus.SystemBus()
        self.bluetoothservice = self.bus.get_object('org.upwork.HidBluetooth', '/org/upwork/HidBluetooth')
        self.iface = dbus.Interface(self.bluetoothservice, 'org.upwork.HidBluetooth')

        print "Waiting for mouse"

        # keep trying to find a mouse
        have_dev = False
        while have_dev == False:
            try:
                # try and get a mouse - loop through all devices and try to find a mouse
                devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
                for device in devices:
                    if "mouse" in device.name.lower():
                        self.dev = InputDevice(device.fn)
                        have_dev = True
            except OSError:
                print "Mouse not found, waiting 3 seconds and retrying"
                time.sleep(3)
        print "Mouse Found"

    def change_state_button(self, event):
        evdev_code = ecodes.KEY[event.code]
        print evdev_code
        if evdev_code == ecodes.BTN_LEFT:
            print "Left Mouse Button Pressed"
        elif evdev_code == ecodes.BTN_RIGHT:
            print "Right Mouse Button Pressed"
        elif evdev_code == ecodes.BTN_MIDDLE:
            print "Middle Mouse Button Pressed"

    def change_state_movement(self, event):
        print event

    # poll for mouse events
    def event_loop(self):
        for event in self.dev.read_loop():
            if event.type == ecodes.EV_KEY and event.value < 2:
                self.change_state_button(event)
                self.send_input()
            elif event.type == ecodes.EV_REL[0] or event.type == ecodes.EV_REL[1]:
                self.change_state_movement(event)
                self.send_input()

    # forward mouse events to the dbus service
    def send_input(self):

        bin_str = ""
        element = self.state[2]
        for bit in element:
            bin_str += str(bit)

        self.iface.send_mouse(int(bin_str, 2), self.state[3], self.state[4])

if __name__ == "__main__":

    print "Setting up mouse"
    mouse = Mouse()

    print "starting event loop"
    mouse.event_loop()