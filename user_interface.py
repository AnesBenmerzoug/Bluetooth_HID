from Tkinter import *
import dbus
import dbus.service
import dbus.mainloop.glib

import subprocess
import multiprocessing

#####################################################################################################

connection_status_message = "Disconnected"

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
        print index


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
        self.bluetooth_status_label = Label(self.frame1, textvariable=self.bluetooth_status, bg="red").pack(fill=X,
                                                                                                            expand=True,
                                                                                                            side=LEFT,
                                                                                                            padx=10,
                                                                                                            pady=10)

        self.frame2 = Frame(self, bg=background)
        self.frame2.pack(side="top", fill="both", expand=True)

        Label(self.frame2, text="Connection Status: ", bg=background).pack(side=LEFT, padx=10, pady=10)
        self.connection_status_label = Label(self.frame2, textvariable=self.connection_status, bg="red").pack(fill=X,
                                                                                                              expand=True,
                                                                                                              side=LEFT,
                                                                                                              padx=10,
                                                                                                              pady=10)

    def update_bluetooth_status(self, status):
        if status == "Enabled":
            self.bluetooth_status.set("Enabled")
        # self.bluetooth_status_label.configure(bg="green")
        elif status == "Disabled":
            self.bluetooth_status.set("Disabled")
        # self.bluetooth_status_label.configure(bg="red")
        return

    def update_connection_status(self, status):
        self.connection_status.set(status)


class PageTwo(Frame):
    def __init__(self, master, background="white"):
        Frame.__init__(self, master, bg=background)

        self.container = Frame(self, bg=background)
        self.container.pack(side="top")

        self.buttons = []

        for i in xrange(9):
            self.buttons.append(Button(self.container, text=str(i + 1),
                                       command=lambda row=i / 3, column=i % 3: self.on_press(row, column)))
            self.buttons[i].bind("<ButtonRelease>", self.on_release)
            self.buttons[i].grid(row=i / 3, column=i % 3, padx=20, pady=20)

        self.bus = dbus.SystemBus()
        self.bluetoothservice = self.bus.get_object('org.upwork.HidBluetoothService', "/org/upwork/HidBluetoothService")
        self.iface = dbus.Interface(self.bluetoothservice, 'org.upwork.HidBluetoothService')

    def on_press(self, row, column):
        button_id = row * 3 + column + 1
        print "button " + str(button_id) + " was pressed"
        #self.iface.send_keys(0, [button_id, 0, 0, 0, 0, 0])

    def on_release(self, event):
        #self.iface.send_keys(0, [0, 0, 0, 0, 0, 0])


def update(application, keyboard, mouse, bluetooth, queue):
    try:
        application.update_idletasks()
        application.update()

        if "UP" in subprocess.check_output("hciconfig hci0 | grep UP", shell=True):
            application.pageOne.update_bluetooth_status("Enabled")
        else:
            application.pageOne.update_bluetooth_status("Disabled")

        global connection_status_message

        try:
            application.pageOne.update_connection_status(queue.get())
        except:
            pass

        return True
    except:
        keyboard.terminate()
        mouse.terminate()
        bluetooth.terminate()
        return False


def create_keyboard_process():
    subprocess.Popen("python keyboard_client.py", shell="True")
    return

def create_mouse_process():
    subprocess.Popen("python mouse_client.py", shell="True")
    return

def create_bluetooth_server_process(queue):
    subprocess.Popen("sudo python bluetooth_emulator_server.py queue", shell="True")
    return

if __name__ == "__main__":
    root = Tk()
    root.minsize(300, 400)
    root.maxsize(300, 400)
    main_application = App(root)

    queue = multiprocessing.Queue()

    keyboardProcess = multiprocessing.Process(target=create_keyboard_process)
    mouseProcess = multiprocessing.Process(target=create_mouse_process)
    bluetoothProcess = multiprocessing.Process(target=create_bluetooth_server_process, args=(queue,))

    keyboardProcess.start()
    mouseProcess.start()
    bluetoothProcess.start()

    while True:
        update(main_application, keyboardProcess, mouseProcess, bluetoothProcess, queue)

    print "Closing Application"
