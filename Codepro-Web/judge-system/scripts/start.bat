@echo off
echo ========================================================
echo Starting CodeProOJ Judge Server on Port 9999
echo ========================================================

cd /d "%~dp0\.."
if not exist logs mkdir logs
if not exist storage\executables mkdir storage\executables
if not exist storage\submissions mkdir storage\submissions
if not exist storage\results mkdir storage\results

python judge-server\main.py
