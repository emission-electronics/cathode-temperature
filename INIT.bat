@ECHO off

ECHO Init python virtual environment (.venv)...
python -m venv .venv

ECHO v
ECHO Activate environment...
call .venv\Scripts\activate

ECHO v
ECHO Install requirements...
pip install -r requirements.txt

ECHO v
ECHO Done.

pause
