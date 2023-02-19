#!/bin/bash

ps -ef | grep bot.py | grep Python | awk '{print $2}' | xargs sudo kill -9 1>/dev/null 2>/dev/null
exit 0