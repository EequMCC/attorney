@echo off
nuitka --standalone --mingw64 --show-progress --windows-disable-console --output-dir=p output_docx.py
pause