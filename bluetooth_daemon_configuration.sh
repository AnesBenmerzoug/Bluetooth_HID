#!/bin/bash

cmd1="sudo service dbus restart"

cmd2="sudo rfkill block wlan"

cmd3="sudo ifconfig wlan0 down"

cmd4="sudo rfkill block bluetooth"

cmd5="sudo service bluetooth stop"

cmd6="sudo /usr/sbin/bluetoothd --nodetach --debug -p time"

cmd7="sudo hciconfig hci0 up"

###########################################################################

echo "Starting Bluetooth Daemon Configuration"

$cmd1 &>/dev/null &

sleep 0.2

$cmd2 &>/dev/null &

$cmd3 &>/dev/null &

$cmd4 &>/dev/null &

$cmd5 &>/dev/null &

sleep 0.2

$cmd6 &>/dev/null &

sleep 0.2

$cmd7 &>/dev/null &

echo "Finished Bluetooth Daemon Configuration"