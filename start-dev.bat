@echo off
chcp 65001 >nul
echo ========================================================
echo        Khoi dong he thong CodeProOJ (Local Dev)
echo ========================================================

echo [1/4] Khoi dong Django API Backend (Port 8000)...
start "CodeProOJ - Django API (8000)" cmd /k "python manage.py runserver 127.0.0.1:8000"

ping 127.0.0.1 -n 3 >nul

echo [2/4] Khoi dong Judge Server ^& Workers (Port 9999)...
start "CodeProOJ - Judge Server (9999)" cmd /k "python judge-system/judge-server/main.py"

ping 127.0.0.1 -n 2 >nul

echo [3/4] Khoi dong Web Gateway (Port 8888)...
start "CodeProOJ - Web Gateway (8888)" cmd /k "node apps/web/server.js"

ping 127.0.0.1 -n 2 >nul

echo [4/4] Khoi dong Anti-Cheat Worker...
start "CodeProOJ - Anti-Cheat Worker" cmd /k "python manage.py run_anticheat_worker"

echo.
echo ========================================================
echo He thong da duoc khoi dong day du!
echo - Web Gateway:   http://localhost:8888
echo - Admin Portal:  http://localhost:8888/admin
echo - Django API:    http://127.0.0.1:8000
echo - Judge Health:  http://127.0.0.1:9999/api/v1/health
echo ========================================================
