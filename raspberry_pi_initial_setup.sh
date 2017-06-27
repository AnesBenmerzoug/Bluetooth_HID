#!/bin/bash

# Update and upgrade raspberry pi

printf "\nUpdating and upgrading the Raspberry Pi\n"

sudo apt-get update -y
sudo apt-get updgrade -y
sudo apt-get dist-upgrade -y

# Install necessary packages

printf "\nInstalling the necessary packages\n"

sudo apt-get install python-gobject pi-bluetooth bluez bluez-tools bluez-firmware python-bluez python-dev python-pip -y

printf "\nInstalling evdev for reading and writing input events from the keyboard and mouse\n"

sudo pip install evdev

# DBUS Configuration
sudo cp org.upwork.hidbluetooth.conf /etc/dbus-1/system.d