"""
Login Screen - Professional Two-Panel Design
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtGui import QIcon, QPalette
from src.services.auth_service import AuthenticationService


class LoginScreen(QWidget):
    """Professional two-panel login screen UI."""

    login_success = pyqtSignal(object)  # Emits user object
    login_failed = pyqtSignal(str)  # Emits error message

    def __init__(self):
        """Initialize login screen."""
        super().__init__()
        self.auth_service = AuthenticationService()
        self.init_ui()

    def init_ui(self):
        """Initialize UI components with professional two-panel design."""
        self.setWindowTitle("PPMS - Login")
        self.setGeometry(100, 100, 1024, 680)
        
        # Set window style
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
        """)

        # Main horizontal layout for two panels
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== LEFT PANEL (White) =====
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(15)

        # Logo/Brand
        logo_label = QLabel("PPMS")
        logo_font = QFont("Arial", 20, QFont.Bold)
        logo_label.setFont(logo_font)
        logo_label.setStyleSheet("color: #0052CC;")
        left_layout.addWidget(logo_label)

        # Spacing
        left_layout.addSpacing(20)

        # Heading
        heading = QLabel("Log in to your Account")
        heading_font = QFont("Arial", 22, QFont.Bold)
        heading.setFont(heading_font)
        heading.setStyleSheet("color: #1a1a1a;")
        left_layout.addWidget(heading)

        # Subheading
        subheading = QLabel("Welcome back! Select method to log in:")
        subheading_font = QFont("Arial", 10)
        subheading.setFont(subheading_font)
        subheading.setStyleSheet("color: #666666;")
        left_layout.addWidget(subheading)

        left_layout.addSpacing(10)

        # Email field
        email_label = QLabel("Email")
        email_label.setFont(QFont("Arial", 10, QFont.Bold))
        email_label.setStyleSheet("color: #1a1a1a;")
        left_layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        self.email_input.setMinimumHeight(40)
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid #0052CC;
                background-color: white;
            }
        """)
        left_layout.addWidget(self.email_input)

        # Password field
        password_label = QLabel("Password")
        password_label.setFont(QFont("Arial", 10, QFont.Bold))
        password_label.setStyleSheet("color: #1a1a1a;")
        left_layout.addWidget(password_label)

        password_layout = QHBoxLayout()
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(0)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px 40px 10px 10px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid #0052CC;
                background-color: white;
            }
        """)
        password_layout.addWidget(self.password_input)

        # Show/Hide password button inside field
        show_pwd_btn = QPushButton("👁")
        show_pwd_btn.setMaximumWidth(35)
        show_pwd_btn.setMinimumHeight(40)
        show_pwd_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #999999;
                padding-right: 5px;
                margin-right: -40px;
            }
            QPushButton:hover {
                color: #666666;
            }
        """)
        show_pwd_btn.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(show_pwd_btn)

        left_layout.addLayout(password_layout)

        # Remember me and Forgot password row
        remember_forgot_layout = QHBoxLayout()
        remember_forgot_layout.setSpacing(10)

        self.remember_me = QCheckBox("Remember me")
        self.remember_me.setFont(QFont("Arial", 9))
        self.remember_me.setStyleSheet("color: #1a1a1a;")
        remember_forgot_layout.addWidget(self.remember_me)

        remember_forgot_layout.addStretch()

        forgot_btn = QPushButton("Forgot Password?")
        forgot_btn.setFont(QFont("Arial", 9))
        forgot_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0052CC;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #0040a0;
            }
        """)
        forgot_btn.clicked.connect(self.handle_forgot_password)
        remember_forgot_layout.addWidget(forgot_btn)

        left_layout.addLayout(remember_forgot_layout)

        # Login button
        self.login_btn = QPushButton("Log in")
        self.login_btn.setMinimumHeight(44)
        self.login_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0052CC;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #0041a3;
            }
            QPushButton:pressed {
                background-color: #003080;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        left_layout.addWidget(self.login_btn)

        # Create account link
        create_account_layout = QHBoxLayout()
        create_account_layout.setSpacing(5)

        account_text = QLabel("Don't have an account?")
        account_text.setFont(QFont("Arial", 9))
        account_text.setStyleSheet("color: #666666;")
        create_account_layout.addWidget(account_text)

        create_btn = QPushButton("Create an account")
        create_btn.setFont(QFont("Arial", 9))
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0052CC;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #0040a0;
            }
        """)
        create_btn.clicked.connect(self.handle_create_account)
        create_account_layout.addWidget(create_btn)
        create_account_layout.addStretch()

        left_layout.addLayout(create_account_layout)
        left_layout.addStretch()

        left_panel.setLayout(left_layout)

        # ===== RIGHT PANEL (Blue Gradient) =====
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0052CC,
                    stop:1 #003366
                );
                border-radius: 10px;
            }
        """)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setSpacing(20)

        # Placeholder for banner content
        right_layout.addStretch()

        # Banner heading
        banner_heading = QLabel("Connect with every application.")
        banner_heading_font = QFont("Arial", 24, QFont.Bold)
        banner_heading.setFont(banner_heading_font)
        banner_heading.setStyleSheet("color: white;")
        banner_heading.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(banner_heading)

        # Banner subtext
        banner_subtext = QLabel("Everything you need in an easily customizable dashboard.")
        banner_subtext_font = QFont("Arial", 11)
        banner_subtext.setFont(banner_subtext_font)
        banner_subtext.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        banner_subtext.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(banner_subtext)

        right_layout.addStretch()

        # Dots indicator (placeholder)
        dots_layout = QHBoxLayout()
        dots_layout.addStretch()
        for i in range(3):
            dot = QLabel("●" if i == 0 else "○")
            dot.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 12px;")
            dot.setAlignment(Qt.AlignCenter)
            dots_layout.addWidget(dot)
        dots_layout.addStretch()
        right_layout.addLayout(dots_layout)

        right_panel.setLayout(right_layout)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

        self.setLayout(main_layout)

        # Connect Enter key to login
        self.password_input.returnPressed.connect(self.handle_login)

    def toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def handle_login(self):
        """Handle login button click."""
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please enter email and password")
            return

        # Attempt login
        success, message, user = self.auth_service.login_with_email_password(email, password)

        if success:
            self.login_success.emit(user)
        else:
            self.login_failed.emit(message)
            QMessageBox.critical(self, "Login Failed", message)

    def handle_forgot_password(self):
        """Handle forgot password click."""
        QMessageBox.information(
            self,
            "Password Reset",
            "Please contact your administrator to reset your password."
        )

    def handle_create_account(self):
        """Handle create account click."""
        QMessageBox.information(
            self,
            "Create Account",
            "Account creation coming soon! Please contact your administrator."
        )

    def clear_inputs(self):
        """Clear input fields."""
        self.email_input.clear()
        self.password_input.clear()
