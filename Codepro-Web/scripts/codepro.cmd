@echo off
powershell.exe -NoLogo -NoProfile -File "%~dp0codepro.ps1" %*
exit /b %ERRORLEVEL%
