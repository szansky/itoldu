$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt

$icon = "assets\itoldu.ico"
$iconArgs = @()
if (Test-Path $icon) {
    $iconArgs = @("--icon", $icon)
}

.\.venv\Scripts\pyinstaller.exe `
    --noconfirm `
    --clean `
    --windowed `
    --name "I-Told-U" `
    @iconArgs `
    app.py

Write-Host "Build ready: dist\I-Told-U\I-Told-U.exe"
