"""
Main Application Entry Point
PyQt5 PPMS Application
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt
from src.config.firebase_config import FirebaseConfig, AppConfig
from src.config.logger_config import setup_logger
from src.ui.screens.login_screen import LoginScreen
from src.ui.screens.dashboard_screen import DashboardScreen

logger = setup_logger(__name__)


class PPMSApplication(QMainWindow):
    """Main PPMS application window."""

    def __init__(self):
        """Initialize application."""
        super().__init__()
        self.setWindowTitle(AppConfig.WINDOW_TITLE)
        self.setGeometry(0, 0, AppConfig.WINDOW_WIDTH, AppConfig.WINDOW_HEIGHT)

        # Maximize window
        self.showMaximized()

        # Initialize Firebase
        try:
            FirebaseConfig.initialize()
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            self.show_error_and_exit("Firebase Initialization Failed", str(e))

        # Create stacked widget for screen management
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create screens
        self.login_screen = LoginScreen()
        self.dashboard_screen = None

        # Connect signals
        self.login_screen.login_success.connect(self.on_login_success)
        self.login_screen.login_failed.connect(self.on_login_failed)

        # Add login screen
        self.stacked_widget.addWidget(self.login_screen)
        self.stacked_widget.setCurrentWidget(self.login_screen)

        logger.info("PPMS Application initialized")

    def center_window(self):
        """Center window on screen."""
        screen_geometry = self.screen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def on_login_success(self, user):
        """Handle successful login."""
        logger.info(f"User logged in: {user.email}")

        # Create dashboard screen
        self.dashboard_screen = DashboardScreen(user)
        self.dashboard_screen.logout_requested.connect(self.on_logout)

        # Add to stacked widget
        self.stacked_widget.addWidget(self.dashboard_screen)
        self.stacked_widget.setCurrentWidget(self.dashboard_screen)

    def on_login_failed(self, message: str):
        """Handle login failure."""
        logger.warning(f"Login failed: {message}")

    def on_logout(self):
        """Handle logout."""
        logger.info("User logged out")

        # Remove dashboard screen
        if self.dashboard_screen:
            self.stacked_widget.removeWidget(self.dashboard_screen)
            self.dashboard_screen = None

        # Clear login inputs
        self.login_screen.clear_inputs()

        # Show login screen
        self.stacked_widget.setCurrentWidget(self.login_screen)

    def show_error_and_exit(self, title: str, message: str):
        """Show error dialog and exit."""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)
        sys.exit(1)

    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Application closing")
        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = PPMSApplication()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
