#!/bin/bash

cd $(dirname "$0")
cd ../src
python3 bot.py 1>/dev/null 2>/dev/null &
exit 0