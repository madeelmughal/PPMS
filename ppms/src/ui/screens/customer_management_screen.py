"""
Customer Management Screen - Manage customers and credit accounts
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QDialog, QFormLayout,
    QMessageBox, QHeaderView, QComboBox, QDoubleSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from src.services.database_service import CustomerService, DatabaseService
from src.models import Customer
from src.utils.validators import validate_email, validate_phone
from src.config.logger_config import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class CustomerDialog(QDialog):
    """Dialog for adding/editing customers."""

    def __init__(self, parent=None, customer=None):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            customer: Existing Customer to edit (None for new)
        """
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("New Customer" if customer is None else f"Edit {customer.name}")
        self.setGeometry(200, 200, 500, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()

        # Customer name
        self.name_input = QLineEdit()
        if self.customer:
            self.name_input.setText(self.customer.name)
        layout.addRow("Customer Name:", self.name_input)

        # Phone
        self.phone_input = QLineEdit()
        if self.customer:
            self.phone_input.setText(self.customer.phone or "")
        layout.addRow("Phone Number:", self.phone_input)

        # Email
        self.email_input = QLineEdit()
        if self.customer:
            self.email_input.setText(self.customer.email or "")
        layout.addRow("Email:", self.email_input)

        # Address
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        if self.customer and self.customer.address:
            self.address_input.setPlainText(self.customer.address)
        layout.addRow("Address:", self.address_input)

        # City
        self.city_input = QLineEdit()
        if self.customer and self.customer.city:
            self.city_input.setText(self.customer.city)
        layout.addRow("City:", self.city_input)

        # Credit limit
        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setRange(0, 1000000)
        self.credit_limit_input.setDecimals(2)
        self.credit_limit_input.setSuffix(" Rs")
        if self.customer:
            self.credit_limit_input.setValue(float(self.customer.credit_limit or 0))
        layout.addRow("Credit Limit (Rs):", self.credit_limit_input)

        # Customer type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Retail", "Wholesale", "Corporate"])
        if self.customer and self.customer.customer_type:
            index = self.type_combo.findText(self.customer.customer_type)
            self.type_combo.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Customer Type:", self.type_combo)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        if self.customer and self.customer.notes:
            self.notes_input.setPlainText(self.customer.notes)
        layout.addRow("Notes:", self.notes_input)

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
            QMessageBox.warning(self, "Validation Error", "Customer name is required")
            return

        if self.email_input.text() and not validate_email(self.email_input.text()):
            QMessageBox.warning(self, "Validation Error", "Invalid email format")
            return

        if self.phone_input.text() and not validate_phone(self.phone_input.text()):
            QMessageBox.warning(self, "Validation Error", "Invalid phone format")
            return

        self.accept()

    def get_customer(self) -> Customer:
        """
        Get the customer from the dialog.

        Returns:
            Customer object
        """
        return Customer(
            id=self.customer.id if self.customer else None,
            name=self.name_input.text(),
            phone=self.phone_input.text() or None,
            email=self.email_input.text() or None,
            address=self.address_input.toPlainText() or None,
            city=self.city_input.text() or None,
            credit_limit=str(self.credit_limit_input.value()),
            outstanding_balance=self.customer.outstanding_balance if self.customer else "0",
            customer_type=self.type_combo.currentText(),
            notes=self.notes_input.toPlainText() or None,
            created_at=self.customer.created_at if self.customer else datetime.now().isoformat(),
            created_by=self.customer.created_by if self.customer else ""
        )


class CustomerManagementScreen(QWidget):
    """Customer management screen for managing customer accounts and credit."""

    def __init__(self, user):
        """Initialize customer management screen."""
        super().__init__()
        self.user = user
        self.customer_service = CustomerService()
        self.db_service = DatabaseService()

        self.setWindowTitle("Customer Management")
        self.setGeometry(100, 100, 1200, 700)

        self.customers = []

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout()

        # Header
        header = QLabel("Customer Management")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        # Summary layout
        summary_layout = QHBoxLayout()

        self.total_customers_label = QLabel("Total Customers: 0")
        self.total_credit_label = QLabel("Total Outstanding Credit: Rs. 0")
        self.active_accounts_label = QLabel("Active Accounts: 0")

        summary_layout.addWidget(self.total_customers_label)
        summary_layout.addWidget(self.total_credit_label)
        summary_layout.addWidget(self.active_accounts_label)
        summary_layout.addStretch()

        main_layout.addLayout(summary_layout)

        # Search layout
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, phone, or email...")
        self.search_input.textChanged.connect(self.filter_customers)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Customers table
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(8)
        self.customer_table.setHorizontalHeaderLabels([
            "Name", "Phone", "Email", "City", "Type",
            "Credit Limit (Rs)", "Outstanding (Rs)", "Actions"
        ])
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.customer_table)

        # Buttons
        button_layout = QHBoxLayout()
        add_customer_btn = QPushButton("Add Customer")
        add_customer_btn.clicked.connect(self.add_customer)
        button_layout.addWidget(add_customer_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def load_data(self):
        """Load customers from database."""
        try:
            self.customers = self.customer_service.get_all_customers()
            self.populate_customer_table(self.customers)
            self.update_summary()

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def populate_customer_table(self, customers):
        """Populate customer table."""
        self.customer_table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            # Name
            self.customer_table.setItem(row, 0, QTableWidgetItem(customer.name))

            # Phone
            phone_text = customer.phone or "---"
            self.customer_table.setItem(row, 1, QTableWidgetItem(phone_text))

            # Email
            email_text = customer.email or "---"
            self.customer_table.setItem(row, 2, QTableWidgetItem(email_text))

            # City
            city_text = customer.city or "---"
            self.customer_table.setItem(row, 3, QTableWidgetItem(city_text))

            # Type
            self.customer_table.setItem(row, 4, QTableWidgetItem(customer.customer_type))

            # Credit limit
            self.customer_table.setItem(row, 5, QTableWidgetItem(f"Rs. {customer.credit_limit}"))

            # Outstanding balance
            outstanding = float(customer.outstanding_balance or 0)
            outstanding_item = QTableWidgetItem(f"Rs. {outstanding:,.2f}")
            if outstanding > 0:
                outstanding_item.setForeground(QColor("red"))
            self.customer_table.setItem(row, 6, outstanding_item)

            # Actions
            action_layout = QHBoxLayout()
            edit_btn = QPushButton("Edit")
            view_btn = QPushButton("View Details")
            delete_btn = QPushButton("Delete")

            edit_btn.clicked.connect(lambda checked, c=customer: self.edit_customer(c))
            view_btn.clicked.connect(lambda checked, c=customer: self.view_customer_details(c))
            delete_btn.clicked.connect(lambda checked, c=customer: self.delete_customer(c))

            action_widget = QWidget()
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(view_btn)
            action_layout.addWidget(delete_btn)
            action_widget.setLayout(action_layout)

            self.customer_table.setCellWidget(row, 7, action_widget)

    def filter_customers(self):
        """Filter customers based on search input."""
        search_text = self.search_input.text().lower()
        filtered = [
            c for c in self.customers
            if search_text in c.name.lower()
            or (c.phone and search_text in c.phone)
            or (c.email and search_text in c.email.lower())
        ]
        self.populate_customer_table(filtered)

    def update_summary(self):
        """Update summary statistics."""
        total_customers = len(self.customers)
        total_credit = sum(float(c.outstanding_balance or 0) for c in self.customers)
        active_accounts = sum(
            1 for c in self.customers
            if float(c.outstanding_balance or 0) > 0
        )

        self.total_customers_label.setText(f"Total Customers: {total_customers}")
        self.total_credit_label.setText(f"Total Outstanding Credit: Rs. {total_credit:,.2f}")
        self.active_accounts_label.setText(f"Active Accounts: {active_accounts}")

    def add_customer(self):
        """Add a new customer."""
        dialog = CustomerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                customer = dialog.get_customer()
                success, message = self.customer_service.add_customer(customer)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error adding customer: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to add customer: {str(e)}")

    def edit_customer(self, customer):
        """Edit an existing customer."""
        dialog = CustomerDialog(self, customer)
        if dialog.exec_() == QDialog.Accepted:
            try:
                updated_customer = dialog.get_customer()
                success, message = self.customer_service.update_customer(
                    customer.id, updated_customer
                )

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error updating customer: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to update customer: {str(e)}")

    def view_customer_details(self, customer):
        """View detailed information for a customer."""
        details = f"""
Customer Details
================

Name: {customer.name}
Phone: {customer.phone or 'N/A'}
Email: {customer.email or 'N/A'}
Address: {customer.address or 'N/A'}
City: {customer.city or 'N/A'}
Customer Type: {customer.customer_type}

Credit Information
==================
Credit Limit: Rs. {customer.credit_limit}
Outstanding Balance: Rs. {customer.outstanding_balance}

Notes: {customer.notes or 'No notes'}
        """
        QMessageBox.information(self, f"{customer.name} - Details", details)

    def delete_customer(self, customer):
        """Delete a customer."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete Customer #{customer.id}?\nName: {customer.name}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success, message = self.customer_service.delete_customer(customer.id)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error deleting customer: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete customer: {str(e)}")
