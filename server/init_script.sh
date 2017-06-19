#!/bin/bash

sudo /etc/init.d/bluetooth stop
sudo /usr/sbin/bluetoothd --nodetach --debug -p time