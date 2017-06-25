#!/usr/bin/python
#
# Bluetooth keyboard emulator DBUS Service
# 
# Adapted from https://www.gadgetdaily.xyz/create-a-cool-sliding-and-scrollable-mobile-menu/
#		   and http://yetanotherpointlesstechblog.blogspot.de/2016/04/emulating-bluetooth-keyboard-with.html
#

from __future__ import absolute_import, print_function

import os
import sys
import dbus
import dbus.service
import dbus.mainloop.glib
from bluetooth import *
import xml.etree.ElementTree as ET

import gtk
from dbus.mainloop.glib import DBusGMainLoop

#
# define a bluez 5 profile object for our keyboard
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
# create a bluetooth device to emulate a HID keyboard,
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
    SDP_RECORD_PATH = sys.path[0] + "/sdp_record.xml"  # file path of the sdp record to laod
    UUID = "00001124-0000-1000-8000-00805f9b34fb"

    def __init__(self):

        print("Setting up Bluetooth device")

        self.init_bt_device()
        self.init_bluez_profile()

    # configure the bluetooth hardware device
    def init_bt_device(self):

        print("Starting Bluetooth Initilization")

        os.system("sudo /etc/init.d/bluetooth stop &>/dev/null &") # Stopping bluetooth daemon
        os.system("sudo /usr/sbin/bluetoothd --nodetach --debug -p time &>/dev/null &") # Starting bluetooth daemon without plugins

        os.system("sudo hciconfig hci0 up") # Turning on bluetooth device

        print("Configuring for name " + BluetoothDevice.MY_DEV_NAME)

        # set the device class to a keybord and set the name
        #os.system("hciconfig hcio class 0x002540") # Keyboard
        # os.system("hciconfig hcio class 0x002580")  # Mouse
        os.system("sudo hciconfig hcio class 0x0025C0") # Keyboard/Mouse Combo
        os.system("sudo hciconfig hcio name " + BluetoothDevice.MY_DEV_NAME)

        # make the device discoverable
        os.system("sudo hciconfig hcio piscan")

    # set up a bluez profile to advertise device capabilities from a loaded service record
    def init_bluez_profile(self):

        print("Configuring Bluez Profile")

        # setup profile options
        service_record = self.read_sdp_service_record()

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

    # read and return an sdp record from a file
    def read_sdp_service_record(self):

        print("Reading service record")

        try:
            fh = open(BluetoothDevice.SDP_RECORD_PATH, "r")
        except:
            sys.exit("Could not open the sdp record. Exiting...")

        return fh.read()



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

    # send a string to the bluetooth host machine
    def send_string(self, message):

        # print("Sending "+message)
        self.cinterrupt.send(message)

    def close(self):
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
        print("Received Keyboard Input, sending it via Bluetooth")
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

        print("Received Mouse Input, sending it via Bluetooth")
        cmd_str = ""
        cmd_str += chr(0xA1)
        cmd_str += chr(0x02)
        cmd_str += chr(buttons)
        cmd_str += chr(rel_move[0])
        cmd_str += chr(rel_move[1])
        cmd_str += chr(0x00)
        cmd_str += chr(0x00)
        cmd_str += chr(0x00)

        self.device.send_string(cmd_str)

    @dbus.service.method('org.freedesktop.DBus.Introspectable', out_signature='s')
    def Introspect(self):
        return ET.tostring(ET.parse('/home/pi/Bluetooth_HID_Keyboard/Bluetooth_HID/dbus/org.upwork.hidbluetooth.introspection').getroot(), encoding='utf8', method='xml')

    def close(self):
        self.device.close()

# main routine
if __name__ == "__main__":
    # we can only run as root
    if not os.geteuid() == 0:
        sys.exit("Only root can run this script")

    try:
        DBusGMainLoop(set_as_default=True)
        myservice = BluetoothService()
        gtk.main()
    except KeyboardInterrupt:
        myservice.close()