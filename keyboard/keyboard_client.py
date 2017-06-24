#!/usr/bin/python
#
# Reads local key events and forwards them to the btk_server DBUS service
#
# Adapted from https://www.gadgetdaily.xyz/create-a-cool-sliding-and-scrollable-mobile-menu/
#		   and http://yetanotherpointlesstechblog.blogspot.de/2016/04/emulating-bluetooth-keyboard-with.html
#

import os  # used to call external commands
import sys  # used to exit the script
import dbus
import dbus.service
import dbus.mainloop.glib
import time
import evdev  # used to get input from the keyboard
from evdev import InputDevice, ecodes
import keymap  # used to map evdev input to hide key codes


# Define a client to listen to local key events
class Keyboard():
    def __init__(self):
        # the structure for a bt keyboard input report (size is 10 bytes)

        self.state = [
            0xA1,  # this is an input report
            0x01,  # Usage report = Keyboard
            # Bit array for Modifier keys
            [0,  # Right GUI - Windows Key
             0,  # Right ALT
             0,  # Right Shift
             0,  # Right Control
             0,  # Left GUI
             0,  # Left ALT
             0,  # Left Shift
             0],  # Left Control
            0x00,  # Vendor reserved
            0x00,  # rest is space for 6 keys
            0x00,
            0x00,
            0x00,
            0x00,
            0x00]

        print "Setting up DBus Client"

        self.bus = dbus.SystemBus()
        self.bluetoothservice = self.bus.get_object('org.upwork.HidBluetooth', "/org/upwork/hidbtservice")
        self.iface_keyboard = dbus.Interface(self.bluetoothservice, 'org.upwork.HidBluetooth.keyboard')

        print "Waiting for keyboard"

        # keep trying to key a keyboard
        have_dev = False
        while have_dev == False:
            try:
                # try and get a keyboard - loop through all devices and try to find a keyboard
                devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
                for device in devices:
                    if "keyboard" in device.name.lower():
                        self.dev = InputDevice(device.fn)
                        have_dev = True
            except OSError:
                print "Keyboard not found, waiting 3 seconds and retrying"
                time.sleep(3)
        print "Keyboard Found"

    def change_state(self, event):
        evdev_code = ecodes.KEY[event.code]
        modkey_element = keymap.modkey(evdev_code)

        if modkey_element > 0:
            if self.state[2][modkey_element] == 0:
                self.state[2][modkey_element] = 1
            else:
                self.state[2][modkey_element] = 0

        else:

            # Get the keycode of the key
            hex_key = keymap.convert(ecodes.KEY[event.code])
            # Loop through elements 4 to 9 of the input report structure
            for i in range(4, 10):
                if self.state[i] == hex_key and event.value == 0:
                    # Code 0 so we need to depress it
                    self.state[i] = 0x00
                elif self.state[i] == 0x00 and event.value == 1:
                    # if the current space if empty and the key is being pressed
                    self.state[i] = hex_key
                    break

    # poll for keyboard events
    def event_loop(self):
        for event in self.dev.read_loop():
            # only bother if we hit a key and its an up or down event
            if event.type == ecodes.EV_KEY and event.value < 2:
                self.change_state(event)
                self.send_input()

    # forward keyboard events to the dbus service
    def send_input(self):

        bin_str = ""
        element = self.state[2]
        for bit in element:
            bin_str += str(bit)

        self.iface_keyboard.send_keys(int(bin_str, 2), self.state[4:10])


if __name__ == "__main__":
    print "Setting up keyboard"

    kb = Keyboard()

    print "starting event loop"
    kb.event_loop()
