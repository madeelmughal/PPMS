#!/usr/bin/env python
"""
PPMS Application Launcher
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run app
from src.main import PPMSApplication
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PPMSApplication()
    window.show()
    sys.exit(app.exec_())
