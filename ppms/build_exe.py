#!/usr/bin/env python
"""
PPMS Build Script - Creates standalone executable using PyInstaller
Run this script to build the application into a single .exe file

Usage:
    python build_exe.py

Production Build Features:
    - All dependencies bundled
    - Firebase service account included
    - Environment configuration included
    - All hidden imports resolved
"""

import os
import sys
import subprocess
import shutil

# Configuration
APP_NAME = "PPMS"
MAIN_SCRIPT = "run.py"
ICON_FILE = None  # Set to "assets/icon.ico" if you have an icon
ONE_FILE = True   # True = single .exe, False = folder with files
VERSION = "3.0.0"

def check_pyinstaller():
    """Check if PyInstaller is installed, install if not."""
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def clean_build():
    """Clean previous build artifacts."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean .spec file
    spec_file = f"{APP_NAME}.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

def get_data_files():
    """Get list of data files to include in the build."""
    data_files = []
    
    # Firebase service account key (REQUIRED for production)
    if os.path.exists("serviceAccountKey.json"):
        data_files.append(("serviceAccountKey.json", "."))
        print("[OK] serviceAccountKey.json found")
    else:
        print("[WARN] WARNING: serviceAccountKey.json not found - Firebase won't work!")
    
    # Environment files
    if os.path.exists(".env"):
        data_files.append((".env", "."))
        print("[OK] .env found")
    if os.path.exists(".env.example"):
        data_files.append((".env.example", "."))
        print("[OK] .env.example found")
    
    # Include data folder structure
    if os.path.exists("data"):
        data_files.append(("data", "data"))
        print("[OK] data folder found")
    
    return data_files

def build_exe():
    """Build the executable."""
    print("\n" + "="*60)
    print(f"  Building {APP_NAME} v{VERSION} - Production Executable")
    print("="*60 + "\n")
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Check PyInstaller
    check_pyinstaller()
    
    # Clean previous builds
    print("\n[1/4] Cleaning previous builds...")
    clean_build()
    
    # Collect data files
    print("\n[2/4] Collecting data files...")
    data_files = get_data_files()
    
    # Build command
    print("\n[3/4] Configuring build...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",  # No console window for GUI app
        "--noconfirm",  # Replace output without asking
        "--clean",  # Clean PyInstaller cache
    ]
    
    if ONE_FILE:
        cmd.append("--onefile")
    
    if ICON_FILE and os.path.exists(ICON_FILE):
        cmd.extend(["--icon", ICON_FILE])
    
    # Add data files
    for src, dest in data_files:
        cmd.extend(["--add-data", f"{src};{dest}"])
    
    # Hidden imports that PyInstaller might miss
    hidden_imports = [
        # PyQt5
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtPrintSupport",
        "PyQt5.sip",
        # Firebase & Google Cloud
        "firebase_admin",
        "firebase_admin.credentials",
        "firebase_admin.db",
        "firebase_admin.firestore",
        "firebase_admin.auth",
        "google.cloud.firestore",
        "google.cloud.firestore_v1",
        "google.auth",
        "google.auth.transport.requests",
        "google.oauth2.credentials",
        "grpc",
        "grpc._cython",
        # Data processing
        "pandas",
        "pandas._libs",
        "pandas._libs.tslibs.base",
        "numpy",
        "openpyxl",
        # PDF generation
        "reportlab",
        "reportlab.lib",
        "reportlab.platypus",
        "reportlab.pdfgen",
        "reportlab.graphics",
        # Image processing
        "PIL",
        "PIL._tkinter_finder",
        # Matplotlib (for charts)
        "matplotlib",
        "matplotlib.pyplot",
        "matplotlib.figure",
        "matplotlib.backends.backend_qt5agg",
        "matplotlib.backends.backend_agg",
        # Utils
        "dotenv",
        "cryptography",
        "json",
        "logging",
        "datetime",
        # Encoding
        "encodings",
        "encodings.utf_8",
        "encodings.ascii",
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Exclude unnecessary modules to reduce size
    excludes = [
        "tkinter",
        "scipy",
        "IPython",
        "notebook",
        "pytest",
    ]
    
    for exc in excludes:
        cmd.extend(["--exclude-module", exc])
    
    # Add paths
    cmd.extend(["--paths", "src"])
    cmd.extend(["--paths", "."])
    
    # Main script
    cmd.append(MAIN_SCRIPT)
    
    print("\n[4/4] Running PyInstaller...")
    print("-" * 60)
    print("Command:", " ".join(cmd[:10]) + " ...")
    print("-" * 60)
    print("\nThis may take several minutes...\n")
    
    # Run PyInstaller
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print("\n" + "="*60)
        print("  [OK] BUILD SUCCESSFUL!")
        print("="*60)
        
        if ONE_FILE:
            exe_path = os.path.join("dist", f"{APP_NAME}.exe")
        else:
            exe_path = os.path.join("dist", APP_NAME, f"{APP_NAME}.exe")
        
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n  Executable: {os.path.abspath(exe_path)}")
            print(f"  Size: {size_mb:.1f} MB")
            print(f"  Version: {VERSION}")
            
            print("\n" + "-"*60)
            print("  DEPLOYMENT INSTRUCTIONS:")
            print("-"*60)
            print(f"  1. Copy {APP_NAME}.exe to the target computer")
            print(f"  2. Copy serviceAccountKey.json to the same folder")
            print(f"  3. Copy .env file to the same folder (if using env vars)")
            print(f"  4. Run {APP_NAME}.exe")
            print(f"\n  Data will be stored in 'PPMS_Data' folder next to the exe.")
            print("="*60)
        
        # Create deployment package
        create_deployment_package(exe_path)
        
        return True
    else:
        print("\n" + "="*60)
        print("  [FAILED] BUILD FAILED!")
        print("="*60)
        print("\nCheck the error messages above for details.")
        return False

def create_deployment_package(exe_path):
    """Create a deployment folder with all necessary files."""
    deploy_dir = os.path.join("dist", "PPMS_Deploy")
    
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # Copy exe
    shutil.copy2(exe_path, deploy_dir)
    
    # Copy required files
    files_to_copy = [
        "serviceAccountKey.json",
        ".env",
        ".env.example",
    ]
    
    for f in files_to_copy:
        if os.path.exists(f):
            shutil.copy2(f, deploy_dir)
    
    # Create README for deployment
    readme_content = f"""PPMS v{VERSION} - Deployment Package
========================================

INSTALLATION:
1. Copy the entire 'PPMS_Deploy' folder to the target computer
2. Ensure all files are in the same directory:
   - PPMS.exe
   - serviceAccountKey.json (REQUIRED)
   - .env (optional - for custom configuration)

RUNNING:
- Double-click PPMS.exe to start the application
- A 'PPMS_Data' folder will be created automatically for local data storage

REQUIREMENTS:
- Windows 10 or later
- Internet connection (for Firebase sync)

TROUBLESHOOTING:
- If the app doesn't start, ensure serviceAccountKey.json is present
- Check 'PPMS_Data/logs' folder for error logs
- Ensure firewall allows outbound connections to Firebase

Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(os.path.join(deploy_dir, "README.txt"), "w") as f:
        f.write(readme_content)
    
    print(f"\n  ✓ Deployment package created: dist/PPMS_Deploy/")

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
