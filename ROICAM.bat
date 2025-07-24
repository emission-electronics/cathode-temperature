@ECHO off

call .venv\Scripts\activate.bat
python src\roi_camera_capture\main.py

ECHO Application closed.

pause
