from Tkinter import *
import os
import sys
import dbus
import dbus.service
import dbus.mainloop.glib
from bluetooth import *
import xml.etree.ElementTree as ET

import gtk
from dbus.mainloop.glib import DBusGMainLoop

import subprocess
import multiprocessing


#####################################################################################################

#
# define a bluez 5 profile object for our keyboard/mouse
#
class BluetoothBluezProfile(dbus.service.Object):
    fd = -1

    @dbus.service.method("org.bluez.Profile1",
                         in_signature="", out_signature="")
    def Release(self):
        print("Release")
        mainloop.quit()

    @dbus.service.method("org.bluez.Profile1",
                         in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel")

    @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        self.fd = fd.take()
        print("NewConnection(%s, %d)" % (path, self.fd))
        for key in properties.keys():
            if key == "Version" or key == "Features":
                print("  %s = 0x%04x" % (key, properties[key]))
            else:
                print("  %s = %s" % (key, properties[key]))

    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, path):
        print("RequestDisconnection(%s)" % (path))

        if (self.fd > 0):
            os.close(self.fd)
            self.fd = -1

    def __init__(self, bus, path):
        dbus.service.Object.__init__(self, bus, path)


#
# create a bluetooth device to emulate a HID keyboard/mouse,
# advertize a SDP record using our bluez profile class
#
class BluetoothDevice():
    # change these constants
    MY_ADDRESS = "B8:27:EB:B6:8C:21"
    MY_DEV_NAME = "Bluetooth_Keyboard/Mouse"

    # define some constants
    P_CTRL = 17  # Service port - must match port configured in SDP record
    P_INTR = 19  # Service port - must match port configured in SDP record #Interrrupt port
    PROFILE_DBUS_PATH = "/bluez/upwork/hidbluetooth_profile"  # dbus path of  the bluez profile we will create
    SDP_RECORD_PATH = sys.path[0] + "/sdp_record.xml"  # file path of the sdp record to load
    UUID = "00001124-0000-1000-8000-00805f9b34fb"

    def __init__(self):

        print("Setting up Bluetooth device")

        self.init_bt_device()
        self.init_bluez_profile()

    # configure the bluetooth hardware device
    def init_bt_device(self):

        print("Configuring for name " + BluetoothDevice.MY_DEV_NAME)

        # set the device class to a keybord/mouse combo and set the name
        # os.system("sudo hciconfig hcio class 0x25C0") # Keyboard/Mouse Combo in Limited Discoverable Mode
        os.system("sudo hciconfig hcio class 0x05C0")  # Keyboard/Mouse Combo in General Discoverable Mode
        os.system("sudo hciconfig hcio name " + BluetoothDevice.MY_DEV_NAME)

        # make the device discoverable
        os.system("sudo hciconfig hcio piscan")

    # set up a bluez profile to advertise device capabilities from a loaded service record
    def init_bluez_profile(self):

        print("Configuring Bluez Profile")

        # read service record from a file
        print("Reading service record")

        with open(BluetoothDevice.SDP_RECORD_PATH, "r") as fh:
            service_record = fh.read()

        if not service_record:
            sys.exit("Could not open the sdp record. Exiting...")

        # setup profile options
        opts = {
            "ServiceRecord": service_record,
            "Role": "server",
            "RequireAuthentication": False,
            "RequireAuthorization": False
        }

        # retrieve a proxy for the bluez profile interface
        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"), "org.bluez.ProfileManager1")

        profile = BluetoothBluezProfile(bus, BluetoothDevice.PROFILE_DBUS_PATH)

        manager.RegisterProfile(BluetoothDevice.PROFILE_DBUS_PATH, BluetoothDevice.UUID, opts)

        print("Profile registered ")

    # listen for incoming client connections

    # ideally this would be handled by the Bluez 5 profile
    # but that didn't seem to work
    def listen(self):

        print("Waiting for connections")
        self.scontrol = BluetoothSocket(L2CAP)
        self.sinterrupt = BluetoothSocket(L2CAP)

        # bind these sockets to a port - port zero to select next available
        self.scontrol.bind((self.MY_ADDRESS, self.P_CTRL))
        self.sinterrupt.bind((self.MY_ADDRESS, self.P_INTR))

        # Start listening on the server sockets
        self.scontrol.listen(1)  # Limit of 1 connection
        self.sinterrupt.listen(1)

        self.ccontrol, cinfo = self.scontrol.accept()
        print("Got a connection on the control channel from " + cinfo[0])

        self.cinterrupt, cinfo = self.sinterrupt.accept()
        print("Got a connection on the interrupt channel from " + cinfo[0])

        global connection_status_queue
        connection_status_queue.put("Connected")

    # send a string to the bluetooth host machine
    def send_string(self, message):
        try:
            self.cinterrupt.send(message)
        except:
            self.close()
            self.listen()

    def close(self):
        global connection_status_queue
        connection_status_queue.put("Disconnected")
        self.scontrol.close()
        self.sinterrupt.close()


# define a dbus service that emulates a bluetooth keyboard and mouse
# this will enable different clients to connect to and use
# the service
class BluetoothService(dbus.service.Object):
    def __init__(self):

        print("Setting up service")

        # set up as a dbus service
        bus_name = dbus.service.BusName("org.upwork.HidBluetoothService", bus=dbus.SystemBus())
        dbus.service.Object.__init__(self, bus_name, "/org/upwork/HidBluetoothService")

        # create and setup our device
        self.device = BluetoothDevice()

        # start listening for connections
        self.device.listen()

    @dbus.service.method('org.upwork.HidBluetoothService', in_signature='yay')
    def send_keys(self, modifier_byte, keys):

        print("Sending keyboard keystrokes:")
        for key_code in keys:
            print(str(key_code))

        cmd_str = ""
        cmd_str += chr(0xA1)
        cmd_str += chr(0x01)
        cmd_str += chr(modifier_byte)
        cmd_str += chr(0x00)

        count = 0
        for key_code in keys:
            if count < 6:
                cmd_str += chr(key_code)
            count += 1

        self.device.send_string(cmd_str)

    @dbus.service.method('org.upwork.HidBluetoothService', in_signature='iai')
    def send_mouse(self, buttons, rel_move):

        cmd_str = ""
        cmd_str += chr(0xA1)
        cmd_str += chr(0x02)
        cmd_str += chr(buttons)
        cmd_str += chr(rel_move[0])
        cmd_str += chr(rel_move[1])
        cmd_str += chr(rel_move[2])

        self.device.send_string(cmd_str)

    @dbus.service.method('org.freedesktop.DBus.Introspectable', out_signature='s')
    def Introspect(self):
        return ET.tostring(ET.parse(os.getcwd() + '/org.upwork.hidbluetooth.introspection').getroot(), encoding='utf8',
                           method='xml')

    def close(self):
        try:
            self.device.close()
        except:
            pass


#####################################################################################################


class App(Frame):
    """
    GUI Class
    """

    def __init__(self, master=None, width=200, height=400, background="white"):
        Frame.__init__(self, master, width=width, height=height, bg=background)
        self.pack(side="top", fill=BOTH, expand=True)

        self.buttons_frame = Frame(self, bg="grey")
        self.buttons_frame.pack(side="top", fill=X, expand=False)

        self.buttons_variable = IntVar()
        self.buttons_variable.set(0)

        self.radio_buttons = []

        for i in xrange(4):
            self.radio_buttons.append(
                Radiobutton(self.buttons_frame, variable=self.buttons_variable, activebackground="green", bg="white",
                            selectcolor="green", relief="sunken", command=self.change_screen, value=i, indicatoron=0))
            self.radio_buttons[i].pack(fill=X, expand=True, side=LEFT, padx=10, pady=10)

        self.inner_frame = Frame(self, bg=background)
        self.inner_frame.pack(side="top", fill=X, expand=True)
        self.inner_frame.grid_rowconfigure(0, weight=1)
        self.inner_frame.grid_columnconfigure(0, weight=1)

        self.pageOne = PageOne(self.inner_frame)
        self.pageOne.grid(row=0, column=0, sticky="nsew")

        self.pageTwo = PageTwo(self.inner_frame)
        self.pageTwo.grid(row=0, column=0, sticky="nsew")

        self.change_screen()

    def change_screen(self):
        index = self.buttons_variable.get()
        if index == 0:
            self.pageOne.tkraise()
        elif index == 1:
            self.pageTwo.tkraise()


#############################################################################################################


class BluetoothStatusLabel(Label):
    def __init__(self, master, bg="red"):
        Label.__init__(self, master, bg=bg)
        self.update_text()

    def update_text(self):
        if "UP" in subprocess.check_output("hciconfig hci0 | grep UP", shell=True):
            self.configure(bg="green", text="Enabled")
        else:
            self.configure(bg="red", text="Disabled")
        self.after(1000, self.update_text)


class ConnectionStatusLabel(Label):
    def __init__(self, master, bg="red"):
        Label.__init__(self, master, bg=bg)
        self.text = "Disconnected"
        self.update_text()

    def update_text(self):
        try:
            global connection_status_queue
            self.text = connection_status_queue.get(True, 0.1)
        except:
            pass
        self.configure(text=self.text)
        if self.text == "Connected":
            self.configure(bg="green", text="Connected")
        else:
            self.configure(bg="red", text="Disconnected")
        self.after(1000, self.update_text)


class PageOne(Frame):
    def __init__(self, master, background="white"):
        Frame.__init__(self, master, bg=background)

        self.bluetooth_status = StringVar()
        self.connection_status = StringVar()

        self.bluetooth_status.set("Disabled")
        self.connection_status.set("Disconnected")

        self.frame1 = Frame(self, bg=background)
        self.frame1.pack(side="top", fill="both", expand=True)

        Label(self.frame1, text="Bluetooth Status: ", bg=background).pack(side=LEFT, padx=(10, 20), pady=10)

        BluetoothStatusLabel(self.frame1, bg="red").pack(fill=X,
                                                         expand=True,
                                                         side=LEFT,
                                                         padx=10,
                                                         pady=10)

        self.frame2 = Frame(self, bg=background)
        self.frame2.pack(side="top", fill="both", expand=True)

        Label(self.frame2, text="Connection Status: ", bg=background).pack(side=LEFT, padx=10, pady=10)

        ConnectionStatusLabel(self.frame2, bg="red").pack(fill=X,
                                                          expand=True,
                                                          side=LEFT,
                                                          padx=10,
                                                          pady=10)


##########################################################################################################################


class PageTwo(Frame):
    def __init__(self, master, background="white"):
        Frame.__init__(self, master, bg=background)

        self.container = Frame(self, bg=background)
        self.container.pack(side="top")

        self.buttons = []

        for i in xrange(3):
            for j in xrange(3):
                self.buttons.append(Button(self.container, text=str(i * 3 + j + 1)))
                self.buttons[i * 3 + j].bind("<ButtonPress-1>", self.on_press(i, j))
                self.buttons[i * 3 + j].bind("<ButtonRelease-1>", self.on_release)
                self.buttons[i * 3 + j].grid(row=i, column=j, padx=20, pady=20)

        self.bus = dbus.SystemBus()
        self.bluetoothservice = self.bus.get_object('org.upwork.HidBluetoothService', "/org/upwork/HidBluetoothService")
        self.iface = dbus.Interface(self.bluetoothservice, 'org.upwork.HidBluetoothService')

    def on_press(self, row, column):
        button_id = row * 3 + column + 1
        shift = 29

        def sender(event):
            print("button " + str(button_id) + " was pressed")
            self.iface.send_keys(0x00, [button_id + shift, 0x00, 0x00, 0x00, 0x00, 0x00])

        return sender

    def on_release(self, event):
        print("button was released")
        self.iface.send_keys(0x00, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00])


def create_keyboard_process():
    subprocess.Popen("python keyboard/keyboard_client.py", shell="True")
    return


def create_mouse_process():
    subprocess.Popen("python mouse/mouse_client.py", shell="True")
    return


def create_bluetooth_server_process():
    try:
        DBusGMainLoop(set_as_default=True)
        BluetoothService()
        gtk.main()
    finally:
        return


if __name__ == "__main__":
    connection_status_queue = multiprocessing.Manager().Queue()
    connection_status_queue.put("Disconnected")

    bluetoothProcess = multiprocessing.Process(target=create_bluetooth_server_process)
    bluetoothProcess.start()

    keyboardProcess = multiprocessing.Process(target=create_keyboard_process)
    keyboardProcess.start()

    mouseProcess = multiprocessing.Process(target=create_mouse_process)
    mouseProcess.start()

    root = Tk()
    root.minsize(300, 400)
    root.maxsize(300, 400)
    main_application = App(root)

    try:
        print("Starting user interface main loop")
        main_application.mainloop()
    finally:
        print("Exiting user interface main loop")
        keyboardProcess.terminate()
        mouseProcess.terminate()
        bluetoothProcess.terminate()

    print("Closing Application")
