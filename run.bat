@echo off
REM Change directory to the project root
cd /d "%~dp0"

REM Execute the Python script
python ./src/main_infer.py

REM Pause to keep the command prompt open
pause