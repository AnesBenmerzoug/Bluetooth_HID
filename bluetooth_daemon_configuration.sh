#!/bin/bash

cmd1="sudo service dbus restart"

cmd2="sudo rfkill block bluetooth"

cmd3="sudo service bluetooth stop"

cmd4="sudo rfkill block wlan"

cmd5="sudo ifconfig wlan0 down"

cmd6="sudo /etc/init.d/bluetooth stop"

cmd7="sudo /usr/sbin/bluetoothd --nodetach --debug -p time"

cmd8="sudo rfkill unblock bluetooth"

cmd9="sudo hciconfig hci0 up"

###########################################################################

echo "Starting Bluetooth Daemon Configuration"

$cmd1 &>/dev/null &

sleep 1

$cmd2 &>/dev/null &

$cmd3 &>/dev/null &

$cmd4 &>/dev/null &

$cmd5 &>/dev/null &

sleep 1

$cmd6 &>/dev/null &

sleep 1

$cmd7 &>/dev/null &

sleep 1

$cmd8 &>/dev/null &

$cmd9 &>/dev/null &

echo "Finished Bluetooth Daemon Configuration"