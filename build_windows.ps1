$ErrorActionPreference = "Stop"

function Invoke-ProjectPython {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$PythonArgs
    )

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source @PythonArgs
        return
    }

    $launcher = Get-Command py -ErrorAction Stop
    & $launcher.Source -3.12 @PythonArgs
}

if (-not (Test-Path ".venv")) {
    Invoke-ProjectPython -m venv .venv
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
