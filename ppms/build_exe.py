#!/usr/bin/env python
"""
PPMS Build Script - Creates standalone executable using PyInstaller
Run this script to build the application into a single .exe file

Usage:
    python build_exe.py
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

def check_pyinstaller():
    """Check if PyInstaller is installed, install if not."""
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} found")
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

def build_exe():
    """Build the executable."""
    print("\n" + "="*50)
    print(f"Building {APP_NAME} Standalone Executable")
    print("="*50 + "\n")
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Check PyInstaller
    check_pyinstaller()
    
    # Clean previous builds
    clean_build()
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",  # No console window
        "--noconfirm",  # Replace output without asking
    ]
    
    if ONE_FILE:
        cmd.append("--onefile")
    
    if ICON_FILE and os.path.exists(ICON_FILE):
        cmd.extend(["--icon", ICON_FILE])
    
    # Add data files
    # Include .env.example as template
    if os.path.exists(".env.example"):
        cmd.extend(["--add-data", ".env.example;."])
    
    # Hidden imports that PyInstaller might miss
    hidden_imports = [
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.sip",
        "matplotlib",
        "matplotlib.backends.backend_qt5agg",
        "firebase_admin",
        "google.cloud.firestore",
        "dotenv",
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Add paths
    cmd.extend(["--paths", "src"])
    
    # Main script
    cmd.append(MAIN_SCRIPT)
    
    print("Running PyInstaller with command:")
    print(" ".join(cmd))
    print("\nThis may take several minutes...\n")
    
    # Run PyInstaller
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print("\n" + "="*50)
        print("✓ BUILD SUCCESSFUL!")
        print("="*50)
        
        if ONE_FILE:
            exe_path = os.path.join("dist", f"{APP_NAME}.exe")
        else:
            exe_path = os.path.join("dist", APP_NAME, f"{APP_NAME}.exe")
        
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\nExecutable created: {os.path.abspath(exe_path)}")
            print(f"Size: {size_mb:.1f} MB")
            print(f"\nYou can now copy {APP_NAME}.exe to any Windows computer and run it!")
            print("Data will be stored in 'PPMS_Data' folder next to the exe.")
        
        return True
    else:
        print("\n✗ Build failed!")
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
