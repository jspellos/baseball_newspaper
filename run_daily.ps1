$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDirectory = Join-Path $ProjectRoot "output\logs"
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$LogPath = Join-Path $LogDirectory "$Timestamp.log"

New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
Set-Location $ProjectRoot

function Write-Log {
    param([string]$Message)
    $Line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    $Line | Tee-Object -FilePath $LogPath -Append
}

try {
    Write-Log "Starting Baseball Daily generation."
    Write-Log "Project root: $ProjectRoot"

    $Python = Get-Command python -ErrorAction Stop
    Write-Log "Python: $($Python.Source)"

    & $Python.Source "build_newspaper.py" 2>&1 |
        ForEach-Object { Write-Log "$_" }

    if ($LASTEXITCODE -ne 0) {
        throw "build_newspaper.py exited with code $LASTEXITCODE."
    }

    & "$ProjectRoot\publish_site.ps1" 2>&1 |
        ForEach-Object { Write-Log "$_" }

    if ($LASTEXITCODE -ne 0) {
        throw "publish_site.ps1 exited with code $LASTEXITCODE."
    }

    Write-Log "Baseball Daily generation completed successfully."
    exit 0
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}
