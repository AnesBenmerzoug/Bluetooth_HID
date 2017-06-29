#!/bin/bash

cmd1="sudo ifconfig wlan0 down"

cmd2="sudo /etc/init.d/bluetooth stop"

cmd3="sudo /usr/sbin/bluetoothd --nodetach --debug -p time"

cmd4="sudo hciconfig hci0 up"

###########################################################################

$cmd1 &>/dev/null &

sleep 1

$cmd2 &>/dev/null &

$cmd3 &>/dev/null &

sleep 1

$cmd4 &>/dev/null &

sleep 1

$cmd4 &>/dev/null &