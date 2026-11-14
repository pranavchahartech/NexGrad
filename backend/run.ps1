# Nexgrad Backend PowerShell Helper
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs
)

$PythonExe = if (Test-Path "..\..\myenv\Scripts\python.exe") {
    "..\..\myenv\Scripts\python.exe"
} elseif (Test-Path "..\myenv\Scripts\python.exe") {
    "..\myenv\Scripts\python.exe"
} elseif (Test-Path "C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe") {
    "C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe"
} else {
    "python"
}

if (-not $CommandArgs -or $CommandArgs.Count -eq 0) {
    Write-Host "Nexgrad Backend: Provide a manage.py command." -ForegroundColor Cyan
    Write-Host "Examples:"
    Write-Host "  .\run test core ai_assistant" -ForegroundColor Green
    Write-Host "  .\run runserver" -ForegroundColor Green
    exit 0
}

if ($CommandArgs[0] -eq "seed") {
    & $PythonExe seed_data.py
} else {
    & $PythonExe manage.py @CommandArgs
}

