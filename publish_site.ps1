$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutputRoot = Join-Path $ProjectRoot "output"
$DocsRoot = Join-Path $ProjectRoot "docs"
$OutputDaily = Join-Path $OutputRoot "daily"
$DocsDaily = Join-Path $DocsRoot "daily"

if (-not (Test-Path (Join-Path $OutputRoot "index.html"))) {
    throw "No generated site found. Run build_newspaper.py first."
}

New-Item -ItemType Directory -Path $DocsDaily -Force | Out-Null

Copy-Item -Path (Join-Path $OutputRoot "index.html") -Destination (Join-Path $DocsRoot "index.html") -Force
Copy-Item -Path (Join-Path $OutputRoot "archive.html") -Destination (Join-Path $DocsRoot "archive.html") -Force
Copy-Item -Path (Join-Path $OutputDaily "*.html") -Destination $DocsDaily -Force

Write-Output "Published static site files to $DocsRoot"

