#!/bin/bash

cd $(dirname "$0")
cd ../src
python3 bot.py 1>/dev/null 2>/dev/null &
sudo pmset -b sleep 0
sudo pmset -b disablesleep 1
exit 0