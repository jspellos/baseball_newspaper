param(
    [string]$EditionDate = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$HtmlPath = Join-Path $ProjectRoot "output\daily\$EditionDate.html"
$PdfDirectory = Join-Path $ProjectRoot "output\pdf"
$PdfPath = Join-Path $PdfDirectory "$EditionDate.pdf"

if (-not (Test-Path $HtmlPath)) {
    throw "HTML edition not found: $HtmlPath"
}

$BrowserCandidates = @(
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)

$Browser = $BrowserCandidates |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

if (-not $Browser) {
    throw "Could not find Microsoft Edge or Google Chrome for PDF export."
}

New-Item -ItemType Directory -Path $PdfDirectory -Force | Out-Null

$ResolvedHtml = (Resolve-Path $HtmlPath).Path
$HtmlUrl = ([System.Uri]$ResolvedHtml).AbsoluteUri
$BrowserStdout = Join-Path $env:TEMP "baseball-newspaper-pdf-stdout.txt"
$BrowserStderr = Join-Path $env:TEMP "baseball-newspaper-pdf-stderr.txt"

$BrowserProcess = Start-Process `
    -FilePath $Browser `
    -ArgumentList @(
        "--headless",
        "--disable-gpu",
        "--log-level=3",
        "--no-pdf-header-footer",
        "--print-to-pdf=$PdfPath",
        $HtmlUrl
    ) `
    -RedirectStandardOutput $BrowserStdout `
    -RedirectStandardError $BrowserStderr `
    -NoNewWindow `
    -PassThru `
    -Wait

if ($BrowserProcess.ExitCode -ne 0) {
    throw "PDF browser process exited with code $($BrowserProcess.ExitCode)."
}

if (-not (Test-Path $PdfPath)) {
    throw "PDF browser process completed, but no PDF was written."
}

Write-Output "Wrote $PdfPath"
