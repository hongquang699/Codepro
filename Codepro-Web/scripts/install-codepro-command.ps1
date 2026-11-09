$projectScript = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'codepro.ps1'))
$commandDir = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\', '/')
$profilePath = $PROFILE.CurrentUserAllHosts
$profileDir = Split-Path -Parent $profilePath
New-Item -ItemType Directory -Path $profileDir -Force | Out-Null

$begin = '# BEGIN CodeProOJ terminal command'
$end = '# END CodeProOJ terminal command'
$existing = if (Test-Path -LiteralPath $profilePath) {
    [System.IO.File]::ReadAllText($profilePath)
} else {
    ''
}

$escapedPath = $projectScript.Replace("'", "''")
$block = @"
$begin
function global:codepro { & '$escapedPath' @args }
$end
"@
$pattern = '(?s)' + [regex]::Escape($begin) + '.*?' + [regex]::Escape($end)
if ([regex]::IsMatch($existing, $pattern)) {
    $updated = [regex]::Replace($existing, $pattern, { param($match) $block })
} else {
    $updated = $existing.TrimEnd("`r", "`n") + "`r`n" + $block + "`r`n"
}
[System.IO.File]::WriteAllText($profilePath, $updated, [System.Text.UTF8Encoding]::new($false))

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$entries = @($userPath -split ';' | Where-Object { $_ })
if (-not ($entries | Where-Object { $_.TrimEnd('\', '/').Equals($commandDir, [System.StringComparison]::OrdinalIgnoreCase) })) {
    [Environment]::SetEnvironmentVariable('Path', (($entries + $commandDir) -join ';'), 'User')
}
if (-not ($env:Path -split ';' | Where-Object { $_.TrimEnd('\', '/').Equals($commandDir, [System.StringComparison]::OrdinalIgnoreCase) })) {
    $env:Path = "$commandDir;$env:Path"
}

# Older installs wrote this function to a single host profile. Remove that
# copy so every PowerShell host uses the same definition from profile.ps1.
$oldProfilePath = $PROFILE.CurrentUserCurrentHost
if ($oldProfilePath -ne $profilePath -and (Test-Path -LiteralPath $oldProfilePath)) {
    $oldContent = [System.IO.File]::ReadAllText($oldProfilePath)
    if ([regex]::IsMatch($oldContent, $pattern)) {
        $cleaned = [regex]::Replace($oldContent, $pattern, '').Trim("`r", "`n")
        [System.IO.File]::WriteAllText($oldProfilePath, $cleaned + "`r`n", [System.Text.UTF8Encoding]::new($false))
    }
}
Write-Output "Đã cài lệnh codepro vào $profilePath"
Write-Output "Đã đăng ký lệnh CMD trong PATH: $commandDir"
Write-Output 'Mở terminal mới hoặc chạy: . $PROFILE.CurrentUserAllHosts'
