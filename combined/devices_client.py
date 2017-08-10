#!/usr/bin/python
#
# Reads local mouse and keyboard events and forwards them to the BluetoothService using DBUS
#
#

import time
from select import select

import dbus
import dbus.mainloop.glib
import dbus.service
import evdev  # used to get input from the keyboard
from evdev import InputDevice, ecodes

import keymap  # used to map evdev input to hide key codes


class Device:
    def __init__(self):
        # the structure for a bluetooth keyboard input report (size is 10 bytes)
        self.keyboard_state = [
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

        # the structure for a bluetooth mouse input report (size is 6 bytes)
        self.mouse_state = [
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

        print("Waiting for Keyboard and Mouse")

        # keep trying to find a keyboard and/or a mouse
        self.keyboard = None
        self.mouse = None

        have_keyboard = False
        have_mouse = False
        count = 0
        NUMBER_OF_TRIES = 100

        while not (have_keyboard and have_mouse) and count < NUMBER_OF_TRIES:
            try:
                # loop through all devices and try and get a keyboard and/or a mouse
                devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
                for device in reversed(devices):
                    if not have_keyboard:
                        if "keyboard" in device.name.lower():
                            print("Found a Keyboard with the keyword 'keyboard'")
                            print("device name is " + device.name)
                            print(device.fn)
                            self.keyboard = InputDevice(device.fn)
                            have_keyboard = True
                        elif "gh60" in device.name.lower():
                            print("Found a Keyboard with the keyword 'gh60'")
                            print("device name is " + device.name)
                            print(device.fn)
                            self.keyboard = InputDevice(device.fn)
                            have_keyboard = True
                    if not have_mouse:
                        if "mouse" in device.name.lower():
                            print("Found a Mouse with the keyword 'mouse'")
                            print("device name is " + device.name)
                            print(device.fn)
                            self.mouse = InputDevice(device.fn)
                            have_mouse = True
            except OSError:
                print("Keyboard and/or Mouse not found, waiting 3 seconds and retrying")
                time.sleep(3)
            finally:
                count += 1

        if not (have_keyboard or have_mouse):
            print("No devices were found.")
            return
        else:
            if have_keyboard and have_mouse:
                print("Keyboard and Mouse found")
            elif have_keyboard:
                print("Keyboard found")
            else:
                print("Mouse found")
            print("Starting event loop")
            self.combined_event_loop()

    ####################################################################################################################

    # take care of mouse buttons
    def change_state_button(self, event):
        if event.code == ecodes.BTN_LEFT:
            print("Left Mouse Button Pressed")
            self.mouse_state[2] = event.value
        elif event.code == ecodes.BTN_RIGHT:
            print("Right Mouse Button Pressed")
            self.mouse_state[2] = 2 * event.value
        elif event.code == ecodes.BTN_MIDDLE:
            print("Middle Mouse Button Pressed")
            self.mouse_state[2] = 3 * event.value
        self.mouse_state[3] = 0x00
        self.mouse_state[4] = 0x00
        self.mouse_state[5] = 0x00

    # take care of mouse movements
    def change_state_movement(self, event):
        if event.code == ecodes.REL_X:
            self.mouse_state[3] = event.value & 0xFF
        elif event.code == ecodes.REL_Y:
            self.mouse_state[4] = event.value & 0xFF
        elif event.code == ecodes.REL_WHEEL:
            self.mouse_state[5] = event.value & 0xFF

    # forward mouse events to the dbus service
    def send_mouse_input(self):
        self.iface.send_mouse(self.mouse_state[2], self.mouse_state[3:6])
        
    ####################################################################################################################
        
    def change_keyboard_state(self, event):
        evdev_code = ecodes.KEY[event.code]
        modkey_element = keymap.modkey(evdev_code)

        if modkey_element > 0:
            if self.keyboard_state[2][modkey_element] == 0:
                self.keyboard_state[2][modkey_element] = 1
            else:
                self.keyboard_state[2][modkey_element] = 0

        else:

            # Get the keycode of the key
            hex_key = keymap.convert(ecodes.KEY[event.code])
            print("Key " + str(ecodes.KEY[event.code]) + " was pressed")
            # Loop through elements 4 to 9 of the input report structure
            for i in range(4, 10):
                if self.keyboard_state[i] == hex_key and event.value == 0:
                    # Code 0 so we need to depress it
                    self.keyboard_state[i] = 0x00
                elif self.keyboard_state[i] == 0x00 and event.value == 1:
                    # if the current space is empty and the key is being pressed
                    self.keyboard_state[i] = hex_key
                    break

    # forward keyboard events to the dbus service
    def send_keyboard_input(self):
        bin_str = ""
        element = self.keyboard_state[2]
        for bit in element:
            bin_str += str(bit)
        self.iface.send_keys(int(bin_str, 2), self.keyboard_state[4:10])

    ####################################################################################################################

    # poll for keyboard and mouse events
    def combined_event_loop(self):
        print("Starting combined event loop")
        devices = {dev.fd: dev for dev in [self.keyboard, self.mouse] if dev is not None}
        while True:
            r, w, e = select(devices, [], [])
            for fd in r:
                if devices[fd] == self.keyboard:
                    for event in self.keyboard.read():
                        # only bother if we hit a key and its an up or down event
                        if event.type == ecodes.EV_KEY and event.value < 2:
                            self.change_keyboard_state(event)
                            try:
                                self.send_keyboard_input()
                            except:
                                break

                else:
                    for event in self.mouse.read():
                        if event.type == ecodes.EV_KEY and event.value < 2:
                            self.change_state_button(event)
                        elif event.type == ecodes.EV_REL:
                            self.change_state_movement(event)
                        try:
                            self.send_mouse_input()
                        except :
                            break

########################################################################################################################

if __name__ == "__main__":
    print("Setting up Keyboard and Mouse")
    Device()


