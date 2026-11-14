@echo off
REM Nexgrad Backend Execution Utility
if exist "..\..\myenv\Scripts\python.exe" (
    set "PYTHON_EXE=..\..\myenv\Scripts\python.exe"
) else if exist "..\myenv\Scripts\python.exe" (
    set "PYTHON_EXE=..\myenv\Scripts\python.exe"
) else if exist "C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe" (
    set "PYTHON_EXE=C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe"
) else (
    set "PYTHON_EXE=python"
)

if "%1"=="" (
    echo Usage: run [manage.py command]
    echo Examples:
    echo   run runserver
    echo   run test core ai_assistant
    echo   run seed
    exit /b 0
)

if "%1"=="seed" (
    "%PYTHON_EXE%" seed_data.py
) else (
    "%PYTHON_EXE%" manage.py %*
)

