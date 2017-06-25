from Tkinter import *
import dbus
import dbus.service
import dbus.mainloop.glib
import time
import evdev  # used to get input from the keyboard
from evdev import InputDevice, ecodes
import keymap  # used to map evdev input to hide key codes

# Define a client to listen to local key events
class Keyboard():
    """
    KEYBOARD Client Class
    """
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
        self.bluetoothservice = self.bus.get_object('org.upwork.HidBluetoothService', "/org/upwork/HidBluetoothService")
        self.iface = dbus.Interface(self.bluetoothservice, 'org.upwork.HidBluetoothService')

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

        self.iface.send_keys(int(bin_str, 2), self.state[4:10])

# define a client to listen to local mouse events
class Mouse():
    """
    MOUSE Client Class
    """
    def __init__(self):
        # the structure for a bluetooth mouse input report (size is 10 bytes)

        self.state = [
            0xA1,  # this is an input report
            0x02,  # Usage report = Mouse
            # Bit array for Button
            [0,  # Button 1
             0,  # Button 2
             0,  # Button 3
             1,  # Button 4
             0,  # Button 5
             0,  # Unused
             0,  # Unused
             0],  # Unused
            0x00,  # Rel X
            0x00,  # Rel Y
            0x00,  # Unused
            0x00,  # Unused
            0x00,  # Unused
        ]

        print "Setting up DBus Client"

        self.bus = dbus.SystemBus()
        self.bluetoothservice = self.bus.get_object('org.upwork.HidBluetoothService', "/org/upwork/HidBluetoothService")
        self.iface = dbus.Interface(self.bluetoothservice, 'org.upwork.HidBluetoothService')

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

    # take care of mouse buttons
    def change_state_button(self, event):
        print event.code
        if event.code == ecodes.BTN_LEFT:
            print "Left Mouse Button Pressed"
            self.state[2][0] = event.value
            self.state[2][1] = 0x00
            self.state[2][2] = 0x00
        elif event.code == ecodes.BTN_RIGHT:
            print "Right Mouse Button Pressed"
            self.state[2][0] = 0x00
            self.state[2][1] = event.value
            self.state[2][2] = 0x00
        elif event.code == ecodes.BTN_MIDDLE:
            print "Middle Mouse Button Pressed"
            self.state[2][0] = 0x00
            self.state[2][1] = 0x00
            self.state[2][2] = event.value

    # take care of mouse movements
    def change_state_movement(self, event):
        print event
        if event.code == ecodes.REL_X:
            print "X Movement"
            self.state[3] = min(abs(event.value), 127)
            self.state[2][4] = 0 if event.value > 0 else 1 # sign of the value
        elif event.code == ecodes.REL_Y:
            print "Y Movement"
            self.state[4] = min(abs(event.value), 127)
            self.state[2][5] = 0 if event.value > 0 else 1 # sign of the value
        else:
            self.state[2][4] = 0
            self.state[2][5] = 0
            self.state[3] = 0
            self.state[4] = 0


    # poll for mouse events
    def event_loop(self):
        print "event loop"
        for event in self.dev.read_loop():
            print "inside event loop"
            print event
            if event.type == ecodes.EV_KEY and event.value < 2:
                self.change_state_button(event)
                self.send_input()
            elif event.type == ecodes.EV_REL:
                self.change_state_movement(event)
                self.send_input()
        print "going out of the event loop"

    # forward mouse events to the dbus service
    def send_input(self):

        bin_str = ""
        element = self.state[2]
        for bit in element:
            bin_str += str(bit)

        try:
            self.iface.send_mouse(int(bin_str, 2), self.state[3:5])
        except:
            pass

#####################################################################################################

class App(Frame):
    """
    GUI CLass
    """
    def __init__(self, master=None, width=200, height=400, background="white"):
        Frame.__init__(self, master, width=width, height=height, bg=background)
        self.pack(side="top", fill=BOTH, expand=True)

        self.buttons_frame = Frame(self, bg=background)
        self.buttons_frame.pack(side="top", fill=X, expand=False)

        self.buttons_variable = IntVar()
        self.buttons_variable.set(0)

        for i in xrange(4):
            Radiobutton(self.buttons_frame, variable=self.buttons_variable, value=i, indicatoron=0).pack(fill=X, expand=True, side=LEFT, padx=10, pady=10)

        self.inner_frame = Frame(self, bg=background)
        self.inner_frame.pack(side="top", fill=X, expand=True)
        self.pageOne = PageOne(self.inner_frame)

        self.mouse = Mouse()
        self.keyboard = Keyboard()

class PageOne(Frame):

    def __init__(self, master, background="white"):
        Frame.__init__(self, master, bg=background)

        self.bluetooth_status = StringVar()
        self.bluetooth_status.set("Disabled")
        self.connection_status = StringVar()
        self.connection_status.set("Disconnected")

        self.frame1 = Frame(self, bg=background)
        self.frame1.pack(fill=X)

        Label(self.frame1, text="Bluetooth Status", bg=background).pack(side=LEFT, padx=(10,20), pady=10)
        Label(self.frame1, textvariable=self.bluetooth_status, bg=background).pack(fill=X, expand=True, side=LEFT, padx=10, pady=10)

        self.frame2 = Frame(self, bg=background)
        self.frame2.pack(fill=X)

        Label(self.frame2, text="Connection Status", bg=background).pack(side=LEFT, padx=10, pady=10)
        Label(self.frame2, textvariable=self.connection_status, bg=background).pack(fill=X, expand=True, side=LEFT, padx=10, pady=10)

if __name__ == "__main__":
    root = Tk()
    root.minsize(300, 400)
    App(root).mainloop()
