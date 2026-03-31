@echo off
cd /d "%~dp0"

:: Try py launcher (Windows Python Launcher)
py --version >nul 2>&1
if %errorlevel% == 0 (
    py supertitle.py
    goto end
)

:: Try python in PATH
python --version >nul 2>&1
if %errorlevel% == 0 (
    python supertitle.py
    goto end
)

:: Try python3 in PATH
python3 --version >nul 2>&1
if %errorlevel% == 0 (
    python3 supertitle.py
    goto end
)

:: Search common install locations
for %%V in (313 312 311 310 39 38) do (
    if exist "C:\Python%%V\python.exe" (
        "C:\Python%%V\python.exe" supertitle.py
        goto end
    )
    if exist "C:\Program Files\Python%%V\python.exe" (
        "C:\Program Files\Python%%V\python.exe" supertitle.py
        goto end
    )
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" supertitle.py
        goto end
    )
)

echo.
echo ============================================================
echo  Python not found on this machine.
echo  Please install Python from: https://www.python.org/downloads
echo  During install, check "Add Python to PATH"
echo ============================================================
echo.
pause

:end
