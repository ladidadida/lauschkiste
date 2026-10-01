#!/usr/bin/env bash

echo "Entering setup.inc.sh"

echo "Disabling the login shell on the serial port, enabling the serial port hardware"
sudo raspi-config nonint do_serial_cons 1
sudo raspi-config nonint do_serial_hw 0

echo -e "\nREBOOT for changes to take effect!\n"
