@echo off
nuitka --standalone --mingw64 --show-progress --enable-plugin=pyqt5 --output-dir=p --windows-icon-from-ico=lawyer.ico attorney.py
pause