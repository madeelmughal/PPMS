"""
Expense Management Screen - Record and manage daily expenses
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QDialog, QFormLayout,
    QMessageBox, QHeaderView, QComboBox, QDoubleSpinBox, QTextEdit,
    QDateEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor
from src.services.database_service import DatabaseService, AccountHeadService
from src.models import Expense
from src.utils.validators import validate_currency
from src.ui.widgets.custom_widgets import apply_dialog_styling
from src.config.logger_config import setup_logger
from datetime import datetime, date

logger = setup_logger(__name__)


class ExpenseDialog(QDialog):
    """Dialog for adding/editing expenses."""

    def __init__(self, parent=None, expense=None, payment_methods=None):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            expense: Existing Expense to edit (None for new)
            payment_methods: List of payment method names from account heads
        """
        super().__init__(parent)
        self.expense = expense
        self.payment_methods = payment_methods if payment_methods is not None else []
        self.setWindowTitle("New Expense" if expense is None else f"Edit Expense #{expense.id}")
        self.setGeometry(200, 200, 500, 400)
        self.init_ui()
        apply_dialog_styling(self)

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()

        # Expense category
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Salary",
            "Utilities",
            "Maintenance",
            "Repairs",
            "Supplies",
            "Rent",
            "Insurance",
            "Miscellaneous"
        ])
        if self.expense and self.expense.category:
            index = self.category_combo.findText(self.expense.category)
            self.category_combo.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Category:", self.category_combo)

        # Description
        self.description_input = QLineEdit()
        if self.expense:
            self.description_input.setText(self.expense.description or "")
        layout.addRow("Description:", self.description_input)

        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 10000000)
        self.amount_input.setDecimals(2)
        self.amount_input.setSuffix(" Rs")
        if self.expense:
            self.amount_input.setValue(float(self.expense.amount))
        layout.addRow("Amount (Rs):", self.amount_input)

        # Date
        self.date_input = QDateEdit()
        self.date_input.setDate(
            QDate.fromString(self.expense.expense_date[:10], "yyyy-MM-dd")
            if self.expense and self.expense.expense_date
            else QDate.currentDate()
        )
        layout.addRow("Expense Date:", self.date_input)

        # Payment method - loaded from account heads
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(self.payment_methods)
        if self.expense and self.expense.payment_method:
            index = self.payment_combo.findText(self.expense.payment_method)
            self.payment_combo.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Payment Method:", self.payment_combo)

        # Vendor/Payee
        self.vendor_input = QLineEdit()
        if self.expense and self.expense.vendor_name:
            self.vendor_input.setText(self.expense.vendor_name)
        layout.addRow("Vendor/Payee:", self.vendor_input)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        if self.expense and self.expense.notes:
            self.notes_input.setPlainText(self.expense.notes)
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
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Amount must be greater than 0")
            return

        if not self.description_input.text():
            QMessageBox.warning(self, "Validation Error", "Description is required")
            return

        self.accept()

    def get_expense(self) -> Expense:
        """
        Get the expense from the dialog.

        Returns:
            Expense object
        """
        return Expense(
            id=self.expense.id if self.expense else None,
            category=self.category_combo.currentText(),
            description=self.description_input.text(),
            amount=str(self.amount_input.value()),
            expense_date=self.date_input.date().toString("yyyy-MM-dd"),
            payment_method=self.payment_combo.currentText(),
            vendor_name=self.vendor_input.text() or None,
            notes=self.notes_input.toPlainText() or None,
            created_at=self.expense.created_at if self.expense else datetime.now().isoformat(),
            created_by=self.expense.created_by if self.expense else ""
        )


class ExpenseManagementScreen(QWidget):
    """Expense management screen for recording and tracking expenses."""

    def __init__(self, user):
        """Initialize expense management screen."""
        super().__init__()
        self.user = user
        self.db_service = DatabaseService()
        self.account_head_service = AccountHeadService()

        self.setWindowTitle("Expense Management")
        self.setGeometry(100, 100, 1200, 700)

        self.expenses = []
        self.payment_methods = []

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout()

        # Header
        header = QLabel("Expense Management")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        # Summary layout
        summary_layout = QHBoxLayout()

        self.today_expenses_label = QLabel("Today's Expenses: Rs. 0")
        self.monthly_expenses_label = QLabel("Monthly Expenses: Rs. 0")
        self.category_summary_label = QLabel("Categories: 0")

        summary_layout.addWidget(self.today_expenses_label)
        summary_layout.addWidget(self.monthly_expenses_label)
        summary_layout.addWidget(self.category_summary_label)
        summary_layout.addStretch()

        main_layout.addLayout(summary_layout)

        # Filter layout
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Category Filter:")
        self.category_filter = QComboBox()
        self.category_filter.addItem("All", "")
        self.category_filter.addItems([
            "Salary", "Utilities", "Maintenance", "Repairs",
            "Supplies", "Rent", "Insurance", "Miscellaneous"
        ])
        self.category_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.category_filter)
        filter_layout.addStretch()

        main_layout.addLayout(filter_layout)

        # Expenses table
        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(8)
        self.expense_table.setHorizontalHeaderLabels([
            "Date", "Category", "Description", "Vendor",
            "Amount (Rs)", "Payment Method", "Notes", "Actions"
        ])
        self.expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.expense_table)

        # Buttons
        button_layout = QHBoxLayout()
        add_expense_btn = QPushButton("Add Expense")
        add_expense_btn.clicked.connect(self.add_expense)
        button_layout.addWidget(add_expense_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def load_data(self):
        """Load expenses from database."""
        try:
            # Get all expenses (can be filtered)
            self.expenses = self.db_service.list_documents("expenses")
            
            # Load payment methods from account heads
            self.payment_methods = self.account_head_service.get_payment_methods()
            
            self.populate_expense_table(self.expenses)
            self.update_summary()

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def populate_expense_table(self, expenses):
        """Populate expense table."""
        self.expense_table.setRowCount(len(expenses))

        for row, expense_data in enumerate(expenses):
            expense = Expense(**expense_data) if isinstance(expense_data, dict) else expense_data

            # Date
            date_text = expense.expense_date[:10] if expense.expense_date else "---"
            date_item = QTableWidgetItem(date_text)
            date_item.setFlags(date_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.expense_table.setItem(row, 0, date_item)

            # Category
            category_item = QTableWidgetItem(expense.category)
            category_item.setFlags(category_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.expense_table.setItem(row, 1, category_item)

            # Description
            desc_item = QTableWidgetItem(expense.description or "---")
            desc_item.setFlags(desc_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.expense_table.setItem(row, 2, desc_item)

            # Vendor
            vendor_text = expense.vendor_name or "---"
            vendor_item = QTableWidgetItem(vendor_text)
            vendor_item.setFlags(vendor_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.expense_table.setItem(row, 3, vendor_item)

            # Amount
            amount_item = QTableWidgetItem(f"Rs. {expense.amount}")
            amount_item.setFlags(amount_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.expense_table.setItem(row, 4, amount_item)

            # Payment method
            payment_item = QTableWidgetItem(expense.payment_method)
            payment_item.setFlags(payment_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.expense_table.setItem(row, 5, payment_item)

            # Notes
            notes_text = expense.notes[:30] + "..." if expense.notes and len(expense.notes) > 30 else (expense.notes or "---")
            notes_item = QTableWidgetItem(notes_text)
            notes_item.setFlags(notes_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.expense_table.setItem(row, 6, notes_item)

            # Actions
            action_layout = QHBoxLayout()
            edit_btn = QPushButton("Edit")
            delete_btn = QPushButton("Delete")

            edit_btn.clicked.connect(
                lambda checked, e=expense: self.edit_expense(e)
            )
            delete_btn.clicked.connect(
                lambda checked, e=expense: self.delete_expense(e)
            )

            action_widget = QWidget()
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_widget.setLayout(action_layout)

            self.expense_table.setCellWidget(row, 7, action_widget)

    def apply_filters(self):
        """Apply category filter to expenses."""
        selected_category = self.category_filter.currentData()
        if selected_category:
            filtered = [
                e for e in self.expenses
                if isinstance(e, dict) and e.get('category') == selected_category
                or (not isinstance(e, dict) and e.category == selected_category)
            ]
        else:
            filtered = self.expenses

        self.populate_expense_table(filtered)

    def update_summary(self):
        """Update summary statistics."""
        today = date.today().isoformat()
        month_start = date(date.today().year, date.today().month, 1).isoformat()

        today_expenses = sum(
            float(
                e.get('amount', 0) if isinstance(e, dict) else e.amount
            )
            for e in self.expenses
            if isinstance(e, dict) and e.get('expense_date', '')[:10] == today
            or (not isinstance(e, dict) and e.expense_date[:10] == today)
        )

        monthly_expenses = sum(
            float(
                e.get('amount', 0) if isinstance(e, dict) else e.amount
            )
            for e in self.expenses
            if isinstance(e, dict) and e.get('expense_date', '')[:10] >= month_start
            or (not isinstance(e, dict) and e.expense_date[:10] >= month_start)
        )

        categories = set(
            e.get('category') if isinstance(e, dict) else e.category
            for e in self.expenses
        )

        self.today_expenses_label.setText(f"Today's Expenses: Rs. {today_expenses:,.2f}")
        self.monthly_expenses_label.setText(f"Monthly Expenses: Rs. {monthly_expenses:,.2f}")
        self.category_summary_label.setText(f"Categories: {len(categories)}")

    def add_expense(self):
        """Add a new expense."""
        dialog = ExpenseDialog(self, payment_methods=self.payment_methods)
        if dialog.exec_() == QDialog.Accepted:
            try:
                expense = dialog.get_expense()
                success, message = self.db_service.create_document(
                    "expenses",
                    expense.id or f"exp_{datetime.now().timestamp()}",
                    {
                        "category": expense.category,
                        "description": expense.description,
                        "amount": expense.amount,
                        "expense_date": expense.expense_date,
                        "payment_method": expense.payment_method,
                        "vendor_name": expense.vendor_name,
                        "notes": expense.notes,
                        "created_at": datetime.now().isoformat(),
                        "created_by": self.user.id
                    },
                    self.user.id
                )

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error adding expense: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to add expense: {str(e)}")

    def edit_expense(self, expense):
        """Edit an existing expense."""
        dialog = ExpenseDialog(self, expense, payment_methods=self.payment_methods)
        if dialog.exec_() == QDialog.Accepted:
            try:
                updated_expense = dialog.get_expense()
                success, message = self.db_service.update_document(
                    "expenses",
                    expense.id,
                    {
                        "category": updated_expense.category,
                        "description": updated_expense.description,
                        "amount": updated_expense.amount,
                        "expense_date": updated_expense.expense_date,
                        "payment_method": updated_expense.payment_method,
                        "vendor_name": updated_expense.vendor_name,
                        "notes": updated_expense.notes,
                        "updated_at": datetime.now().isoformat()
                    }
                )

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error updating expense: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to update expense: {str(e)}")

    def delete_expense(self, expense):
        """Delete an expense."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this expense (Rs. {expense.amount})?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success, message = self.db_service.delete_document(
                    "expenses",
                    expense.id
                )

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error deleting expense: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete expense: {str(e)}")
