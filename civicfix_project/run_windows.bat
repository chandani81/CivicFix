@echo off
REM CivicFix - one-command start for Windows
REM Usage: just double-click this file (run_windows.bat)

cd /d "%~dp0backend"

echo ==^> Setting up backend...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo ==^> Running database migrations (MySQL by default)...
python manage.py migrate
if errorlevel 1 (
    echo.
    echo !! Migration failed. This is almost always because the MySQL database
    echo    doesn't exist yet, or the credentials in backend\.env are wrong.
    echo.
    echo    Fix option 1 (create the MySQL database):
    echo      mysql -u root -p -e "CREATE DATABASE civicfix CHARACTER SET utf8mb4;"
    echo      then check DB_USER/DB_PASSWORD/DB_HOST/DB_PORT in backend\.env
    echo.
    echo    Fix option 2 (skip MySQL entirely for this demo):
    echo      open backend\.env and set USE_SQLITE=True, then re-run this script
    echo.
    pause
    exit /b 1
)

python manage.py seed_departments
python manage.py seed_demo

echo ==^> Starting backend on http://127.0.0.1:8000 ...
start "CivicFix Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python manage.py runserver"

cd /d "%~dp0frontend"
echo ==^> Starting frontend on http://127.0.0.1:5500 ...
start "CivicFix Frontend" cmd /k "cd /d %~dp0frontend && python -m http.server 5500"

timeout /t 3 /nobreak >nul
start http://127.0.0.1:5500/index.html

echo.
echo CivicFix is running in two new windows (Backend + Frontend).
echo Close those windows to stop the servers.
pause
