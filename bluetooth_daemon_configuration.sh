#!/bin/bash

cmd1="sudo service dbus restart"

cmd2="sudo rfkill block bluetooth"

cmd3="sudo service bluetooth stop"

cmd4="sudo ifconfig wlan0 down"

cmd5="sudo /etc/init.d/bluetooth stop"

cmd6="sudo /usr/sbin/bluetoothd --nodetach --debug -p time"

cmd7="sudo hciconfig hci0 up"

###########################################################################

$cmd1 &>/dev/null &

sleep 1

$cmd2 &>/dev/null &

sleep 1

$cmd3 &>/dev/null &

$cmd4 &>/dev/null &

sleep 1

$cmd5 &>/dev/null &

sleep 1

$cmd6 &>/dev/null &

sleep 1

$cmd7 &>/dev/null &