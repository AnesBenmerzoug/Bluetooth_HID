#!/bin/bash

echo "Bluetooth Initilization"

cmd1="sudo /etc/init.d/bluetooth stop"

cmd2="sudo /usr/sbin/bluetoothd --nodetach --debug -p time"

cmd3="sudo hciconfig hci"

$cmd1 &>/dev/null &

$cmd2 &>/dev/null &

$cmd3 &>/dev/null &