@echo off
REM ============================================
REM PPMS Standalone Executable Builder
REM ============================================
REM Run this batch file to build PPMS.exe
REM The build takes 3-5 minutes

cd /d "d:\prog\ppms"

echo.
echo ========================================
echo    Building PPMS Standalone Executable
echo ========================================
echo.
echo This will create a single PPMS.exe file
echo that runs on any Windows PC without
echo requiring Python installation.
echo.
echo Build time: 3-5 minutes
echo.
echo DO NOT close this window!
echo.

REM Clean previous builds
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Run PyInstaller
echo [1/2] Analyzing dependencies...
D:\prog\.venv\Scripts\python.exe -m PyInstaller --name PPMS --windowed --onefile --noconfirm --clean --paths src run.py

echo.
echo [2/2] Verifying build...

if exist "dist\PPMS.exe" (
    echo.
    echo ========================================
    echo         BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Your standalone executable is ready:
    echo.
    echo    d:\prog\ppms\dist\PPMS.exe
    echo.
    echo Copy this file to any Windows PC
    echo and double-click to run!
    echo.
    echo Data will be saved in PPMS_Data folder
    echo next to the exe file.
    echo ========================================
) else (
    echo.
    echo ========================================
    echo         BUILD FAILED!
    echo ========================================
    echo Please check error messages above.
)

echo.
pause
