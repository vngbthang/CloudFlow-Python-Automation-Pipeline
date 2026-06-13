$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

$PythonExe = "python"

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "Activating .venv..."
    . .\.venv\Scripts\Activate.ps1
    $PythonExe = ".\.venv\Scripts\python.exe"
} else {
    Write-Host "No .venv found. Create one with:"
    Write-Host "  python -m venv .venv"
    Write-Host "Then install dependencies with:"
    Write-Host "  pip install -r requirements.txt"
}

if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) {
    throw "Python was not found in PATH."
}

try {
    & $PythonExe -c "import boto3, pandas, sqlalchemy, psycopg2" | Out-Null
} catch {
    Write-Host "Dependencies may be missing. Run:"
    Write-Host "  pip install -r requirements.txt"
    throw
}

Write-Host "Starting Docker services..."
docker compose up -d

Write-Host "Running CloudFlow pipeline..."
& $PythonExe src\run_pipeline.py
if ($LASTEXITCODE -ne 0) {
    throw "CloudFlow pipeline failed."
}
