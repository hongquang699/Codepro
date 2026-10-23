@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo        Khoi dong he thong CodeProOJ (Local Dev)
echo ========================================================

echo [1/4] Khoi dong Django API Backend (Port 8000)...
start "CodeProOJ - Django API (8000)" /D "%~dp0" cmd /k "python -m uvicorn backend.core.asgi:application --host 127.0.0.1 --port 8000 --reload --reload-dir backend --reload-dir websocket --reload-dir security"

echo Cho Django API san sang...
for /L %%I in (1,1,30) do (
    curl.exe --fail --silent --output NUL http://127.0.0.1:8000/ >nul 2>&1
    if not errorlevel 1 goto backend_ready
    timeout /t 1 /nobreak >nul
)
echo [LOI] Django API khong san sang sau 30 giay. Kiem tra cua so backend.
exit /b 1
:backend_ready

echo [2/4] Khoi dong Judge Server ^& Workers (Port 9999)...
start "CodeProOJ - Judge Server (9999)" /D "%~dp0" cmd /k "python judge-system\judge-server\main.py"

ping 127.0.0.1 -n 2 >nul

echo [3/4] Khoi dong Web Gateway (Port 8888)...
start "CodeProOJ - Web Gateway (8888)" /D "%~dp0" cmd /k "node apps\web\server.js"

ping 127.0.0.1 -n 2 >nul

echo [4/4] Khoi dong Anti-Cheat Worker...
start "CodeProOJ - Anti-Cheat Worker" /D "%~dp0" cmd /k "python manage.py run_anticheat_worker"

echo.
echo ========================================================
echo He thong da duoc khoi dong day du!
echo - Web Gateway:   http://localhost:8888
echo - Admin Portal:  http://localhost:8888/admin
echo - Django API:    http://127.0.0.1:8000
echo - Judge Health:  http://127.0.0.1:9999/api/v1/health
echo ========================================================
