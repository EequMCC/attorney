@echo off
nuitka --standalone --mingw64 --show-progress --windows-disable-console --enable-plugin=pyqt5 --output-dir=p getnewlaws.py
pause