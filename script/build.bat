cd ../src
pyinstaller.exe bot.py --onefile
del bot.spec
rmdir /s /q "build"
pause