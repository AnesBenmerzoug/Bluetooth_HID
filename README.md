# **This repository is archived and is no longer being maintained**

# Bluetooth_HID

A program used to make a Raspberry Pi emulate a keyboard/mouse Bluetooth HID client.

### Prerequisites

In order to run the program the Raspberry Pi has to be updated and some dependencies have to be installed.

All of that can be done easily by cloning the repository and executing the following command from its root folder:

    $ sudo bash raspberry_pi_initial_setup.sh
    
### Running

In order to run the program you need to first configure the Raspberry Pi's Bluetooth daemon:

    $ sudo bash bluetooth_daemon_configuration.sh
    
and then to run the user_interface python script:

    $ python user_interface.py
