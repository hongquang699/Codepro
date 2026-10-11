param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $CommandArgs
)

$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\', '/')
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'manage.py') -PathType Leaf)) {
    Write-Error "Không tìm thấy project CodeProOJ tại: $projectRoot"
    exit 1
}

$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $pythonExe) {
    Write-Error 'Không tìm thấy Python. Hãy cài Python hoặc tạo .venv cho project.'
    exit 1
}

Push-Location -LiteralPath $projectRoot
$previousPythonEncoding = $env:PYTHONIOENCODING
$env:PYTHONIOENCODING = 'utf-8'
try {
    & $pythonExe (Join-Path $projectRoot 'manage.py') site_terminal @CommandArgs
    $exitCode = $LASTEXITCODE
}
finally {
    $env:PYTHONIOENCODING = $previousPythonEncoding
    Pop-Location
}
exit $exitCode
