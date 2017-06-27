#!/bin/bash

# Update and upgrade raspberry pi

sudo apt-get update -y
sudo apt-get updgrade -y
sudo apt-get dist-upgrade -y

# Install necessary packages

sudo apt-get install python-gobject pi-bluetooth bluez bluez-tools bluez-firmware python-bluez python-dev python-pip -y
sudo pip install evdev -y

# DBUS Configuration
sudo cp org.upwork.hidbluetooth.conf /etc/dbus-1/system.d