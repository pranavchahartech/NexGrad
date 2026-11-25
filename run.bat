@echo off
REM Nexgrad DevOps Execution Utility (Root Wrapper)
setlocal

set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%..\myenv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%..\myenv\Scripts\python.exe"
) else if exist "C:\Users\SANJAY\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PYTHON_EXE=C:\Users\SANJAY\AppData\Local\Programs\Python\Python313\python.exe"
) else if exist "C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe" (
    set "PYTHON_EXE=C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe"
) else (
    set "PYTHON_EXE=python"
)

if "%1"=="" (
    echo Nexgrad DevOps Helper
    echo Usage: run [manage.py command]
    echo Examples:
    echo   run check
    echo   run test core ai_assistant
    echo   run runserver
    echo   run seed
    exit /b 0
)

pushd "%SCRIPT_DIR%backend"
if "%1"=="seed" (
    "%PYTHON_EXE%" seed_data.py
) else (
    "%PYTHON_EXE%" manage.py %*
)
popd
endlocal
