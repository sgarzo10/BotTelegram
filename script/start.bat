@ECHO OFF
cd %~dp0
cd ../src
START "" /B pythonw bot.py >NUL 2>NUL
exit 0