@ECHO off

call .venv\Scripts\activate.bat
python roi_camera_capture\main.py

ECHO Application closed successfully.

pause
