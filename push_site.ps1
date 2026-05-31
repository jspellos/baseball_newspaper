param(
    [string]$CommitMessage = "Update Baseball Daily edition"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
    throw "This folder is not a Git repository. Initialize it and add the GitHub remote first."
}

& "$ProjectRoot\publish_site.ps1"

git add docs

$PendingChanges = git status --porcelain -- docs
if (-not $PendingChanges) {
    Write-Output "No website changes to publish."
    exit 0
}

git commit -m $CommitMessage
if ($LASTEXITCODE -ne 0) {
    throw "git commit failed with code $LASTEXITCODE."
}

git push
if ($LASTEXITCODE -ne 0) {
    throw "git push failed with code $LASTEXITCODE."
}

Write-Output "Published Baseball Daily site updates to GitHub."

