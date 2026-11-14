# Nexgrad DevOps PowerShell Execution Helper (Root Wrapper)
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs
)

$CandidatePaths = @(
    "$PSScriptRoot\..\myenv\Scripts\python.exe",
    "$PSScriptRoot\myenv\Scripts\python.exe",
    "C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe"
)

$PythonExe = "python"
foreach ($path in $CandidatePaths) {
    if (Test-Path $path) {
        $PythonExe = (Resolve-Path $path).Path
        break
    }
}

if (-not $CommandArgs -or $CommandArgs.Count -eq 0) {
    Write-Host "Nexgrad DevOps Helper: Provide a manage.py command." -ForegroundColor Cyan
    Write-Host "Examples:"
    Write-Host "  .\run check" -ForegroundColor Green
    Write-Host "  .\run test core ai_assistant" -ForegroundColor Green
    Write-Host "  .\run runserver" -ForegroundColor Green
    Write-Host "  .\run seed" -ForegroundColor Green
    exit 0
}

Push-Location "$PSScriptRoot\backend"
try {
    if ($CommandArgs[0] -eq "seed") {
        & $PythonExe seed_data.py
    } else {
        & $PythonExe manage.py @CommandArgs
    }
} finally {
    Pop-Location
}
