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
class Mouse():
    def __init__(self):
        # the structure for a bluetooth mouse input report (size is 6 bytes)

        self.state = [
            0xA1,  # this is an input report
            0x02,  # Usage report = Mouse
            # Bit array for Button
            [0,  # Button 1
             0,  # Button 2
             0,  # Button 3
             #1,  # Button 4
             0,  # Button 4
             0,  # Button 5
             0,  # Unused
             0,  # Unused
             0],  # Unused
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
                for device in devices:
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
        print(event.code)
        if event.code == ecodes.BTN_LEFT:
            print("Left Mouse Button Pressed")
            self.state[2][0] = event.value
            self.state[2][1] = 0x00
            self.state[2][2] = 0x00
        elif event.code == ecodes.BTN_RIGHT:
            print("Right Mouse Button Pressed")
            self.state[2][0] = 0x00
            self.state[2][1] = event.value
            self.state[2][2] = 0x00
        elif event.code == ecodes.BTN_MIDDLE:
            print("Middle Mouse Button Pressed")
            self.state[2][0] = 0x00
            self.state[2][1] = 0x00
            self.state[2][2] = event.value

    # take care of mouse movements
    def change_state_movement(self, event):
        if event.code == ecodes.REL_X:
            print("X Movement")
            #self.state[3] = min(abs(event.value), 127)
            #self.state[2][4] = 0 if event.value >= 0 else 1 # sign of the value
            self.state[3] = event.value & 0xFF
            print("Rel X = " + str(self.state[3]) + ", " + str(self.state[2][4]))
        elif event.code == ecodes.REL_Y:
            print("Y Movement")
            self.state[4] = event.value & 0xFF
            #self.state[4] = min(abs(event.value), 127)
            #self.state[2][5] = 0 if event.value >= 0 else 1 # sign of the value
            print("Rel Y = " + str(self.state[4]) + ", " + str(self.state[2][5]))
        elif event.code == ecodes.REL_WHEEL:
            print("Wheel Movement")
            self.state[5] = event.value & 0xFF
            #self.state[5] = 0x01 if event.value > 0 else 0x1F if event.value < 0 else 0
            print("Rel Wheel = " + str(self.state[5]))
        else:
            print("Movement Stopped")
            #self.state[2][4] = 0
            #self.state[2][5] = 0
            self.state[3] = 0x00
            self.state[4] = 0x00
            self.state[5] = 0x00


    # poll for mouse events
    def event_loop(self):
        print("event loop")
        for event in self.dev.read_loop():
            print(event)
            if event.type == ecodes.EV_KEY and event.value < 2:
                self.change_state_button(event)
                self.send_input()
            elif event.type == ecodes.EV_REL:
                self.change_state_movement(event)
                self.send_input()

    # forward mouse events to the dbus service
    def send_input(self):

        bin_str = ""
        element = self.state[2]
        for bit in element:
            bin_str += str(bit)
        try:
            self.iface.send_mouse(int(bin_str, 2), self.state[3:6])
        except:
            return

if __name__ == "__main__":
    print("Setting up mouse")
    mouse = Mouse()
