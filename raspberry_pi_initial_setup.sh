#!/bin/bash

printf "\nStarting The Raspberry Pi Initial Setup.\n\n"

# Update and upgrade raspberry pi

printf "\nUpdating and upgrading the Raspberry Pi\n\n"

sudo apt-get update -y
sudo apt-get updgrade -y
sudo apt-get dist-upgrade

# Install necessary packages

printf "\nInstalling the necessary packages\n\n"

sudo apt-get install python-gobject pi-bluetooth bluez bluez-tools bluez-firmware python-bluez python-dev python-pip -y

printf "\nInstalling evdev for reading/writing input events from the keyboard/mouse\n\n"

sudo pip install evdev

# DBUS Configuration

printf"\nConfiguring the DBus service\n\n"

sudo cp org.upwork.hidbluetooth.conf /etc/dbus-1/system.d

print "\nRestarting the DBus service\n\n"

sudo service dbus restart

printf "\nFinished The Raspberry Pi Initial Setup.\n\n"