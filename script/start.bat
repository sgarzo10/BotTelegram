@ECHO OFF
cd %~dp0
cd ../src
START "" /B pythonw3 bot.py >NUL 2>NUL
exit 0