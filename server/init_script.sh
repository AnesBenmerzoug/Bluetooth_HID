#!/bin/bash

sudo /etc/init.d/bluetooth stop

cmd="sudo /usr/sbin/bluetoothd --nodetach --debug -p time"

$cmd &>/dev/null &