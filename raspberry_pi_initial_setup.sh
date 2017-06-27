#!/bin/bash

# Update and upgrade raspberry pi

echo "Updating and upgrading the Raspberry Pi"

sudo apt-get update -y
sudo apt-get updgrade -y
sudo apt-get dist-upgrade -y

# Install necessary packages

echo "Installing the necessary packages"

sudo apt-get install python-gobject pi-bluetooth bluez bluez-tools bluez-firmware python-bluez python-dev python-pip -y

echo "Installing evdev for reading and writing input events from the keyboard and mouse"

sudo pip install evdev

# DBUS Configuration
sudo cp org.upwork.hidbluetooth.conf /etc/dbus-1/system.d