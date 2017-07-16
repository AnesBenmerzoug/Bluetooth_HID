from Tkinter import *
import os
import sys

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
            self.radio_buttons.append(Radiobutton(self.buttons_frame, variable=self.buttons_variable, activebackground="green", bg="white",
                                                  selectcolor="green", relief="sunken", command=self.change_screen, value=i, indicatoron=0))
            self.radio_buttons[i].pack(fill=X, expand=True, side=LEFT, padx=10, pady=10)

        self.change_screen()

        self.inner_frame = Frame(self, bg=background)
        self.inner_frame.pack(side="top", fill=X, expand=True)
        self.pageOne = PageOne(self.inner_frame).pack(side="top")

    def change_screen(self):
        index = self.buttons_variable.get()
        print index

class PageOne(Frame):

    def __init__(self, master, background="white"):
        Frame.__init__(self, master, bg=background)

        self.bluetooth_status = StringVar()
        self.bluetooth_status.set("Disabled")
        self.connection_status = StringVar()
        self.connection_status.set("Disconnected")

        self.frame1 = Frame(self, bg=background)
        self.frame1.pack(fill=X)

        Label(self.frame1, text="Bluetooth Status: ", bg=background).pack(side=LEFT, padx=(10,20), pady=10)
        Label(self.frame1, textvariable=self.bluetooth_status, bg="red").pack(fill=X, expand=True, side=LEFT, padx=10, pady=10)

        self.frame2 = Frame(self, bg=background)
        self.frame2.pack(fill=X)

        Label(self.frame2, text="Connection Status: ", bg=background).pack(side=LEFT, padx=10, pady=10)
        Label(self.frame2, textvariable=self.connection_status, bg="red").pack(fill=X, expand=True, side=LEFT, padx=10, pady=10)

if __name__ == "__main__":
    root = Tk()
    root.minsize(300, 400)
    root.maxsize(300, 400)
    App(root).mainloop()
