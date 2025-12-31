"""
Settings & User Management Screen - Admin user and system settings
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QDialog, QFormLayout,
    QMessageBox, QHeaderView, QComboBox, QTextEdit, QTabWidget,
    QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from src.services.database_service import DatabaseService, AccountHeadService
from src.services.auth_service import AuthenticationService
from src.models import User, UserRole
from src.utils.validators import validate_email, validate_phone
from src.config.logger_config import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class UserDialog(QDialog):
    """Dialog for creating/editing users."""

    def __init__(self, parent=None, user=None):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            user: Existing User to edit (None for new)
        """
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("New User" if user is None else f"Edit {user.name}")
        self.setGeometry(200, 200, 500, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()

        # Name
        self.name_input = QLineEdit()
        if self.user:
            self.name_input.setText(self.user.name)
        layout.addRow("Full Name:", self.name_input)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setReadOnly(self.user is not None)
        if self.user:
            self.email_input.setText(self.user.email)
        layout.addRow("Email:", self.email_input)

        # Phone
        self.phone_input = QLineEdit()
        if self.user:
            self.phone_input.setText(self.user.phone or "")
        layout.addRow("Phone:", self.phone_input)

        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "ADMIN",
            "MANAGER",
            "OPERATOR",
            "ACCOUNTANT"
        ])
        if self.user:
            index = self.role_combo.findText(self.user.role)
            self.role_combo.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Role:", self.role_combo)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive"])
        if self.user:
            status = "Active" if self.user.is_active else "Inactive"
            index = self.status_combo.findText(status)
            self.status_combo.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Status:", self.status_combo)

        # Password (only for new users)
        if not self.user:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            layout.addRow("Password:", self.password_input)

            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.Password)
            layout.addRow("Confirm Password:", self.confirm_input)
        else:
            self.password_label = QLabel("(Password can be reset separately)")
            layout.addRow("Password:", self.password_label)

        # Permissions
        layout.addRow(QLabel("Permissions:"))
        self.record_sales_check = QCheckBox("Record Sales")
        if self.user and "record_sales" in (self.user.permissions or []):
            self.record_sales_check.setChecked(True)
        layout.addRow(self.record_sales_check)

        self.manage_fuel_check = QCheckBox("Manage Fuel")
        if self.user and "manage_fuel" in (self.user.permissions or []):
            self.manage_fuel_check.setChecked(True)
        layout.addRow(self.manage_fuel_check)

        self.manage_customers_check = QCheckBox("Manage Customers")
        if self.user and "manage_customers" in (self.user.permissions or []):
            self.manage_customers_check.setChecked(True)
        layout.addRow(self.manage_customers_check)

        self.record_expenses_check = QCheckBox("Record Expenses")
        if self.user and "record_expenses" in (self.user.permissions or []):
            self.record_expenses_check.setChecked(True)
        layout.addRow(self.record_expenses_check)

        self.view_reports_check = QCheckBox("View Reports")
        if self.user and "view_reports" in (self.user.permissions or []):
            self.view_reports_check.setChecked(True)
        layout.addRow(self.view_reports_check)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def validate_and_accept(self):
        """Validate inputs before accepting."""
        if not self.name_input.text():
            QMessageBox.warning(self, "Validation Error", "Name is required")
            return

        if not self.email_input.text():
            QMessageBox.warning(self, "Validation Error", "Email is required")
            return

        if not validate_email(self.email_input.text()):
            QMessageBox.warning(self, "Validation Error", "Invalid email format")
            return

        if self.phone_input.text() and not validate_phone(self.phone_input.text()):
            QMessageBox.warning(self, "Validation Error", "Invalid phone format")
            return

        if not self.user:
            if not hasattr(self, 'password_input') or not self.password_input.text():
                QMessageBox.warning(self, "Validation Error", "Password is required")
                return

            if self.password_input.text() != self.confirm_input.text():
                QMessageBox.warning(self, "Validation Error", "Passwords do not match")
                return

            if len(self.password_input.text()) < 8:
                QMessageBox.warning(self, "Validation Error", "Password must be at least 8 characters")
                return

        self.accept()

    def get_user(self) -> User:
        """
        Get the user from the dialog.

        Returns:
            User object
        """
        permissions = []
        if self.record_sales_check.isChecked():
            permissions.append("record_sales")
        if self.manage_fuel_check.isChecked():
            permissions.append("manage_fuel")
        if self.manage_customers_check.isChecked():
            permissions.append("manage_customers")
        if self.record_expenses_check.isChecked():
            permissions.append("record_expenses")
        if self.view_reports_check.isChecked():
            permissions.append("view_reports")

        return User(
            id=self.user.id if self.user else None,
            name=self.name_input.text(),
            email=self.email_input.text(),
            phone=self.phone_input.text() or None,
            role=self.role_combo.currentText(),
            is_active=self.status_combo.currentText() == "Active",
            permissions=permissions,
            created_at=self.user.created_at if self.user else datetime.now().isoformat(),
            created_by=self.user.created_by if self.user else ""
        )

    def get_password(self) -> str:
        """Get password for new users."""
        if hasattr(self, 'password_input'):
            return self.password_input.text()
        return None


class SettingsManagementScreen(QWidget):
    """Settings and user management screen for administrators."""

    def __init__(self, user):
        """Initialize settings management screen."""
        super().__init__()
        self.user = user
        self.db_service = DatabaseService()
        self.auth_service = AuthenticationService()
        self.account_head_service = AccountHeadService()

        self.setWindowTitle("Settings & User Management")
        self.setGeometry(100, 100, 1200, 700)

        self.users = []
        self.account_heads = []

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout()

        # Header
        header = QLabel("Settings & User Management")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        # Tab widget
        tabs = QTabWidget()

        # User Management tab
        users_widget = QWidget()
        users_layout = QVBoxLayout()

        # Summary
        summary_layout = QHBoxLayout()
        self.total_users_label = QLabel("Total Users: 0")
        self.active_users_label = QLabel("Active Users: 0")
        summary_layout.addWidget(self.total_users_label)
        summary_layout.addWidget(self.active_users_label)
        summary_layout.addStretch()
        users_layout.addLayout(summary_layout)

        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            "Name", "Email", "Phone", "Role", "Status", "Actions"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        users_layout.addWidget(self.users_table)

        # Buttons
        user_btn_layout = QHBoxLayout()
        add_user_btn = QPushButton("Add User")
        add_user_btn.clicked.connect(self.add_user)
        user_btn_layout.addWidget(add_user_btn)
        user_btn_layout.addStretch()
        users_layout.addLayout(user_btn_layout)

        users_widget.setLayout(users_layout)
        tabs.addTab(users_widget, "User Management")

        # System Settings tab
        settings_widget = QWidget()
        settings_layout = QVBoxLayout()

        settings_label = QLabel("System Settings")
        settings_label.setFont(QFont("Arial", 12, QFont.Bold))
        settings_layout.addWidget(settings_label)

        # Business name
        form_layout = QFormLayout()

        self.business_name_input = QLineEdit()
        form_layout.addRow("Business Name:", self.business_name_input)

        # Business address
        self.business_address_input = QTextEdit()
        self.business_address_input.setMaximumHeight(80)
        form_layout.addRow("Business Address:", self.business_address_input)

        # Tax rate
        self.tax_rate_input = QSpinBox()
        self.tax_rate_input.setRange(0, 100)
        self.tax_rate_input.setSuffix("%")
        form_layout.addRow("Default Tax Rate:", self.tax_rate_input)

        # Backup location
        backup_layout = QHBoxLayout()
        self.backup_input = QLineEdit()
        backup_btn = QPushButton("Browse...")
        backup_btn.clicked.connect(self.select_backup_location)
        backup_layout.addWidget(self.backup_input)
        backup_layout.addWidget(backup_btn)
        form_layout.addRow("Backup Location:", backup_layout)

        # Save settings button
        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.clicked.connect(self.save_system_settings)
        form_layout.addRow(save_settings_btn)

        settings_layout.addLayout(form_layout)
        settings_layout.addStretch()

        settings_widget.setLayout(settings_layout)
        tabs.addTab(settings_widget, "System Settings")

        # Audit Log tab
        audit_widget = QWidget()
        audit_layout = QVBoxLayout()

        audit_label = QLabel("Audit Log")
        audit_label.setFont(QFont("Arial", 12, QFont.Bold))
        audit_layout.addWidget(audit_label)

        # Audit table
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(5)
        self.audit_table.setHorizontalHeaderLabels([
            "Date/Time", "User", "Action", "Module", "Details"
        ])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.audit_table.setReadOnly(True)
        audit_layout.addWidget(self.audit_table)

        audit_widget.setLayout(audit_layout)
        tabs.addTab(audit_widget, "Audit Log")

        # Account Heads (Payment Methods) tab
        account_heads_widget = QWidget()
        account_heads_layout = QVBoxLayout()

        ah_label = QLabel("Account Heads / Payment Methods")
        ah_label.setFont(QFont("Arial", 12, QFont.Bold))
        account_heads_layout.addWidget(ah_label)

        ah_info_label = QLabel("Define payment methods that appear in Sales and Expense screens.")
        account_heads_layout.addWidget(ah_info_label)

        # Account heads table
        self.account_heads_table = QTableWidget()
        self.account_heads_table.setColumnCount(4)
        self.account_heads_table.setHorizontalHeaderLabels([
            "Name", "Description", "Status", "Actions"
        ])
        self.account_heads_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        account_heads_layout.addWidget(self.account_heads_table)

        # Buttons
        ah_btn_layout = QHBoxLayout()
        add_ah_btn = QPushButton("Add Payment Method")
        add_ah_btn.clicked.connect(self.add_account_head)
        ah_btn_layout.addWidget(add_ah_btn)
        ah_btn_layout.addStretch()
        account_heads_layout.addLayout(ah_btn_layout)

        account_heads_widget.setLayout(account_heads_layout)
        tabs.addTab(account_heads_widget, "Payment Methods")

        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

    def load_data(self):
        """Load users and settings from database."""
        try:
            # Load users
            user_docs = self.db_service.list_documents("users")
            self.users = [User(**doc) if isinstance(doc, dict) else doc for doc in user_docs]
            self.populate_users_table()
            self.update_summary()

            # Load audit logs
            audit_docs = self.db_service.list_documents("audit_logs")
            self.populate_audit_table(audit_docs)

            # Load account heads (payment methods)
            self.account_heads = self.account_head_service.list_account_heads()
            if not self.account_heads:
                # Initialize default payment methods if none exist
                self.account_head_service.initialize_default_payment_methods(self.user.id)
                self.account_heads = self.account_head_service.list_account_heads()
            self.populate_account_heads_table()

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def populate_users_table(self):
        """Populate users table."""
        self.users_table.setRowCount(len(self.users))

        for row, user in enumerate(self.users):
            # Name
            name_item = QTableWidgetItem(user.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 0, name_item)

            # Email
            email_item = QTableWidgetItem(user.email)
            email_item.setFlags(email_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 1, email_item)

            # Phone
            phone_text = user.phone or "---"
            phone_item = QTableWidgetItem(phone_text)
            phone_item.setFlags(phone_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 2, phone_item)

            # Role
            role_item = QTableWidgetItem(user.role)
            role_item.setFlags(role_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(row, 3, role_item)

            # Status
            status_text = "Active" if user.is_active else "Inactive"
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            status_color = QColor("green") if user.is_active else QColor("red")
            status_item.setForeground(status_color)
            self.users_table.setItem(row, 4, status_item)

            # Actions
            action_layout = QHBoxLayout()
            edit_btn = QPushButton("Edit")
            reset_pwd_btn = QPushButton("Reset Password")
            delete_btn = QPushButton("Delete")

            edit_btn.clicked.connect(lambda checked, u=user: self.edit_user(u))
            reset_pwd_btn.clicked.connect(lambda checked, u=user: self.reset_password(u))
            delete_btn.clicked.connect(lambda checked, u=user: self.delete_user(u))

            action_widget = QWidget()
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(reset_pwd_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addStretch()
            action_widget.setLayout(action_layout)

            self.users_table.setCellWidget(row, 5, action_widget)

    def populate_audit_table(self, audit_logs):
        """Populate audit log table."""
        self.audit_table.setRowCount(len(audit_logs))

        for row, log_data in enumerate(audit_logs):
            log = log_data if isinstance(log_data, dict) else log_data.__dict__

            # Date/Time
            timestamp = log.get('timestamp', log.get('created_at', '---'))
            timestamp_item = QTableWidgetItem(timestamp[:16])
            timestamp_item.setFlags(timestamp_item.flags() & ~Qt.ItemIsEditable)
            self.audit_table.setItem(row, 0, timestamp_item)

            # User
            user = log.get('user_id', '---')
            user_item = QTableWidgetItem(user)
            user_item.setFlags(user_item.flags() & ~Qt.ItemIsEditable)
            self.audit_table.setItem(row, 1, user_item)

            # Action
            action = log.get('action', '---')
            action_item = QTableWidgetItem(action)
            action_item.setFlags(action_item.flags() & ~Qt.ItemIsEditable)
            self.audit_table.setItem(row, 2, action_item)

            # Module
            module = log.get('module', '---')
            module_item = QTableWidgetItem(module)
            module_item.setFlags(module_item.flags() & ~Qt.ItemIsEditable)
            self.audit_table.setItem(row, 3, module_item)

            # Details
            details = log.get('details', '---')
            if isinstance(details, dict):
                details = str(details)
            details_item = QTableWidgetItem(details[:50])
            details_item.setFlags(details_item.flags() & ~Qt.ItemIsEditable)
            self.audit_table.setItem(row, 4, details_item)

    def update_summary(self):
        """Update summary statistics."""
        total = len(self.users)
        active = sum(1 for u in self.users if u.is_active)

        self.total_users_label.setText(f"Total Users: {total}")
        self.active_users_label.setText(f"Active Users: {active}")

    def add_user(self):
        """Add a new user."""
        dialog = UserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                user = dialog.get_user()
                password = dialog.get_password()

                # Register user with Firebase
                success, message = self.auth_service.register_user(user.email, password)

                if success:
                    # Create user document
                    user_doc = {
                        "name": user.name,
                        "email": user.email,
                        "phone": user.phone,
                        "role": user.role,
                        "is_active": user.is_active,
                        "permissions": user.permissions,
                        "created_at": datetime.now().isoformat(),
                        "created_by": self.user.id
                    }

                    success, message = self.db_service.create_document(
                        "users",
                        success.split(":")[-1].strip(),  # Use Firebase UID
                        user_doc,
                        self.user.id
                    )

                    if success:
                        QMessageBox.information(self, "Success", "User created successfully")
                        self.load_data()
                    else:
                        QMessageBox.warning(self, "Error", message)
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error adding user: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to add user: {str(e)}")

    def edit_user(self, user):
        """Edit an existing user."""
        dialog = UserDialog(self, user)
        if dialog.exec_() == QDialog.Accepted:
            try:
                updated_user = dialog.get_user()

                user_doc = {
                    "name": updated_user.name,
                    "email": updated_user.email,
                    "phone": updated_user.phone,
                    "role": updated_user.role,
                    "is_active": updated_user.is_active,
                    "permissions": updated_user.permissions,
                    "updated_at": datetime.now().isoformat()
                }

                success, message = self.db_service.update_document(
                    "users",
                    user.id,
                    user_doc
                )

                if success:
                    QMessageBox.information(self, "Success", "User updated successfully")
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error updating user: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to update user: {str(e)}")

    def reset_password(self, user):
        """Reset password for a user."""
        reply = QMessageBox.question(
            self,
            "Reset Password",
            f"Send password reset email to {user.email}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success, message = self.auth_service.reset_password(user.email)

                if success:
                    QMessageBox.information(self, "Success", message)
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error resetting password: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to reset password: {str(e)}")

    def delete_user(self, user):
        """Delete a user."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{user.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success, message = self.db_service.delete_document("users", user.id)

                if success:
                    QMessageBox.information(self, "Success", "User deleted successfully")
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error deleting user: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete user: {str(e)}")

    def select_backup_location(self):
        """Select backup location."""
        from PyQt5.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Location")
        if folder:
            self.backup_input.setText(folder)

    def save_system_settings(self):
        """Save system settings."""
        try:
            settings = {
                "business_name": self.business_name_input.text(),
                "business_address": self.business_address_input.toPlainText(),
                "tax_rate": str(self.tax_rate_input.value()),
                "backup_location": self.backup_input.text(),
                "updated_at": datetime.now().isoformat(),
                "updated_by": self.user.id
            }

            success, message = self.db_service.update_document(
                "settings",
                "system",
                settings
            )

            if success:
                QMessageBox.information(self, "Success", "Settings saved successfully")
            else:
                QMessageBox.warning(self, "Error", message)

        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def populate_account_heads_table(self):
        """Populate account heads (payment methods) table."""
        self.account_heads_table.setRowCount(len(self.account_heads))

        for row, ah_data in enumerate(self.account_heads):
            ah = ah_data if isinstance(ah_data, dict) else ah_data.__dict__

            # Name
            name_item = QTableWidgetItem(ah.get('name', ''))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.account_heads_table.setItem(row, 0, name_item)

            # Description
            desc = ah.get('description', '') or '---'
            desc_item = QTableWidgetItem(desc)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            self.account_heads_table.setItem(row, 1, desc_item)

            # Status
            is_active = ah.get('is_active', True)
            status_text = "Active" if is_active else "Inactive"
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            status_color = QColor("green") if is_active else QColor("red")
            status_item.setForeground(status_color)
            self.account_heads_table.setItem(row, 2, status_item)

            # Actions
            action_layout = QHBoxLayout()
            edit_btn = QPushButton("Edit")
            delete_btn = QPushButton("Delete")

            edit_btn.clicked.connect(lambda checked, a=ah: self.edit_account_head(a))
            delete_btn.clicked.connect(lambda checked, a=ah: self.delete_account_head(a))

            action_widget = QWidget()
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addStretch()
            action_widget.setLayout(action_layout)

            self.account_heads_table.setCellWidget(row, 3, action_widget)

    def add_account_head(self):
        """Add a new account head (payment method)."""
        dialog = AccountHeadDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                name, description = dialog.get_values()
                success, message = self.account_head_service.create_account_head(
                    name=name,
                    description=description,
                    user_id=self.user.id
                )

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error adding payment method: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to add payment method: {str(e)}")

    def edit_account_head(self, account_head):
        """Edit an existing account head (payment method)."""
        dialog = AccountHeadDialog(self, account_head)
        if dialog.exec_() == QDialog.Accepted:
            try:
                name, description = dialog.get_values()
                success, message = self.account_head_service.update_account_head(
                    account_head_id=account_head.get('id'),
                    name=name,
                    description=description
                )

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error updating payment method: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to update payment method: {str(e)}")

    def delete_account_head(self, account_head):
        """Delete (deactivate) an account head (payment method)."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete payment method '{account_head.get('name')}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success, message = self.account_head_service.delete_account_head(
                    account_head.get('id')
                )

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error deleting payment method: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete payment method: {str(e)}")


class AccountHeadDialog(QDialog):
    """Dialog for adding/editing account heads (payment methods)."""

    def __init__(self, parent=None, account_head=None):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            account_head: Existing account head dict to edit (None for new)
        """
        super().__init__(parent)
        self.account_head = account_head
        self.setWindowTitle("New Payment Method" if account_head is None else f"Edit {account_head.get('name', '')}")
        self.setGeometry(200, 200, 400, 200)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()

        # Name
        self.name_input = QLineEdit()
        if self.account_head:
            self.name_input.setText(self.account_head.get('name', ''))
        layout.addRow("Name:", self.name_input)

        # Description
        self.description_input = QLineEdit()
        if self.account_head:
            self.description_input.setText(self.account_head.get('description', ''))
        layout.addRow("Description:", self.description_input)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def validate_and_accept(self):
        """Validate inputs before accepting."""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Name is required")
            return

        self.accept()

    def get_values(self):
        """Get values from the dialog."""
        return self.name_input.text().strip(), self.description_input.text().strip()
