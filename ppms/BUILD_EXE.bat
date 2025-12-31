@echo off
REM ============================================================
REM PPMS Production Build Script
REM ============================================================
REM Run this batch file to build PPMS.exe
REM Build time: 3-5 minutes

cd /d "d:\prog\ppms"

echo.
echo ============================================================
echo    PPMS Production Executable Builder v1.0
echo ============================================================
echo.
echo This will create a production-ready PPMS.exe with:
echo   - All dependencies bundled
echo   - Firebase configuration included
echo   - No Python installation required
echo.
echo Build time: 3-5 minutes
echo.
echo DO NOT close this window!
echo.

REM Check for required files
echo [Checking required files...]
if not exist "serviceAccountKey.json" (
    echo WARNING: serviceAccountKey.json not found!
    echo Firebase features will NOT work without it.
    echo.
)

if not exist ".env" (
    echo INFO: .env file not found, using defaults
)

REM Clean previous builds
echo.
echo [1/4] Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Run build script
echo.
echo [2/4] Running production build...
echo.
D:\prog\.venv\Scripts\python.exe build_exe.py

echo.
echo [3/4] Verifying build...

if exist "dist\PPMS.exe" (
    echo.
    echo ============================================================
    echo                   BUILD SUCCESSFUL!
    echo ============================================================
    echo.
    echo  Production files created:
    echo.
    echo    Executable:  dist\PPMS.exe
    echo    Deploy pkg:  dist\PPMS_Deploy\
    echo.
    echo  DEPLOYMENT:
    echo    1. Copy the 'PPMS_Deploy' folder to target PC
    echo    2. Ensure serviceAccountKey.json is included
    echo    3. Run PPMS.exe
    echo.
    echo  Data will be saved in 'PPMS_Data' folder next to exe.
    echo ============================================================
    
    echo.
    echo [4/4] Opening deployment folder...
    explorer "dist\PPMS_Deploy"
) else (
    echo.
    echo ============================================================
    echo                   BUILD FAILED!
    echo ============================================================
    echo.
    echo  Please check error messages above.
    echo  Common issues:
    echo    - Missing dependencies (run: pip install -r requirements.txt)
    echo    - PyInstaller not installed (run: pip install pyinstaller)
    echo ============================================================
)

echo.
pause
