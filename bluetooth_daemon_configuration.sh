#!/bin/bash

cmd1="sudo service dbus restart"

cmd3="sudo service bluetooth stop"

cmd4="sudo /etc/init.d/bluetooth stop"

cmd6="sudo /usr/sbin/bluetoothd --nodetach --debug -p time"

cmd7="sudo hciconfig hci0 up"

###########################################################################

echo "Bluetooth Daemon Configuration"

$cmd1 &>/dev/null &

sleep 0.2

$cmd3 &>/dev/null &

sleep 0.2

$cmd4 &>/dev/null &

sleep 0.2

$cmd6 &>/dev/null &

sleep 0.2

$cmd7 &>/dev/null &

