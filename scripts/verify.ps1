$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

$PythonExe = "python"

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "Activating .venv..."
    . .\.venv\Scripts\Activate.ps1
    $PythonExe = ".\.venv\Scripts\python.exe"
}

Write-Host "Running Python compile check..."
& $PythonExe -m py_compile src\processor.py src\report.py src\run_pipeline.py src\worker.py src\upload_file.py src\create_resources.py src\database.py src\utils.py src\logger.py
if ($LASTEXITCODE -ne 0) {
    throw "Python compile check failed."
}

Write-Host "Running pytest..."
& $PythonExe -m pytest
if ($LASTEXITCODE -ne 0) {
    throw "pytest failed."
}

Write-Host "Running Ruff..."
& $PythonExe -m ruff check src tests
if ($LASTEXITCODE -ne 0) {
    throw "Ruff check failed."
}

Write-Host "Running Black check..."
& $PythonExe -m black --check src tests
if ($LASTEXITCODE -ne 0) {
    throw "Black check failed."
}

Write-Host "Generated output reports:"
if (Test-Path "data\output") {
    Get-ChildItem data\output -Filter *.csv | Select-Object Name, Length, LastWriteTime
} else {
    Write-Host "data\output does not exist yet. Run .\scripts\run_pipeline.ps1 first."
}
