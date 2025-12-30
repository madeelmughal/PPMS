"""
Shift Management Screen - Manage operator shifts and reconciliation
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QDialog, QFormLayout,
    QMessageBox, QHeaderView, QComboBox, QDoubleSpinBox, QTextEdit,
    QDateTimeEdit, QTimeEdit, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime, QTime
from PyQt5.QtGui import QFont, QColor
from src.services.database_service import DatabaseService
from src.models import Shift, User
from src.config.logger_config import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class ShiftDialog(QDialog):
    """Dialog for opening/closing shifts."""

    def __init__(self, parent=None, shift=None, users=None, is_closing=False):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            shift: Existing Shift to edit (None for new)
            users: List of available User objects
            is_closing: True if closing a shift
        """
        super().__init__(parent)
        self.shift = shift
        self.users = users or []
        self.is_closing = is_closing
        self.setWindowTitle(
            f"Close Shift #{shift.id}" if is_closing and shift
            else "Open New Shift" if not shift
            else f"Edit Shift #{shift.id}"
        )
        self.setGeometry(200, 200, 500, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()

        if not self.is_closing:
            # Operator selection
            self.operator_combo = QComboBox()
            for user in self.users:
                self.operator_combo.addItem(user.name, user.id)
            if self.shift and self.shift.operator_id:
                index = self.operator_combo.findData(self.shift.operator_id)
                self.operator_combo.setCurrentIndex(index if index >= 0 else 0)
            layout.addRow("Operator:", self.operator_combo)

            # Opening cash
            self.opening_cash_input = QDoubleSpinBox()
            self.opening_cash_input.setRange(0, 1000000)
            self.opening_cash_input.setDecimals(2)
            self.opening_cash_input.setSuffix(" Rs")
            if self.shift and self.shift.opening_cash:
                self.opening_cash_input.setValue(float(self.shift.opening_cash))
            layout.addRow("Opening Cash (Rs):", self.opening_cash_input)

            # Opening time
            self.opening_time_input = QDateTimeEdit()
            if self.shift and self.shift.shift_start:
                self.opening_time_input.setDateTime(
                    QDateTime.fromString(self.shift.shift_start, "yyyy-MM-dd HH:mm:ss")
                )
            else:
                self.opening_time_input.setDateTime(QDateTime.currentDateTime())
            layout.addRow("Opening Time:", self.opening_time_input)

            # Notes
            self.notes_input = QTextEdit()
            self.notes_input.setMaximumHeight(80)
            if self.shift and self.shift.notes:
                self.notes_input.setPlainText(self.shift.notes)
            layout.addRow("Notes:", self.notes_input)

        else:
            # Closing time
            self.closing_time_input = QDateTimeEdit()
            self.closing_time_input.setDateTime(QDateTime.currentDateTime())
            layout.addRow("Closing Time:", self.closing_time_input)

            # Closing cash
            self.closing_cash_input = QDoubleSpinBox()
            self.closing_cash_input.setRange(0, 1000000)
            self.closing_cash_input.setDecimals(2)
            self.closing_cash_input.setSuffix(" Rs")
            layout.addRow("Closing Cash (Rs):", self.closing_cash_input)

            # Expected sales
            self.expected_sales_input = QDoubleSpinBox()
            self.expected_sales_input.setRange(0, 10000000)
            self.expected_sales_input.setDecimals(2)
            self.expected_sales_input.setSuffix(" Rs")
            self.expected_sales_input.setReadOnly(True)
            layout.addRow("Expected Sales (Rs):", self.expected_sales_input)

            # Variance
            self.variance_input = QDoubleSpinBox()
            self.variance_input.setRange(-10000000, 10000000)
            self.variance_input.setDecimals(2)
            self.variance_input.setSuffix(" Rs")
            self.variance_input.setReadOnly(True)
            layout.addRow("Variance (Rs):", self.variance_input)

            # Closure notes
            self.closure_notes_input = QTextEdit()
            self.closure_notes_input.setMaximumHeight(80)
            layout.addRow("Closure Notes:", self.closure_notes_input)

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
        if not self.is_closing:
            if self.opening_cash_input.value() < 0:
                QMessageBox.warning(self, "Validation Error", "Opening cash cannot be negative")
                return
        else:
            if self.closing_cash_input.value() < 0:
                QMessageBox.warning(self, "Validation Error", "Closing cash cannot be negative")
                return

        self.accept()

    def get_shift_data(self) -> dict:
        """
        Get the shift data from the dialog.

        Returns:
            Dictionary with shift data
        """
        if not self.is_closing:
            return {
                "operator_id": self.operator_combo.currentData(),
                "opening_cash": str(self.opening_cash_input.value()),
                "shift_start": self.opening_time_input.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
                "notes": self.notes_input.toPlainText() or None
            }
        else:
            return {
                "shift_end": self.closing_time_input.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
                "closing_cash": str(self.closing_cash_input.value()),
                "closure_notes": self.closure_notes_input.toPlainText() or None,
                "status": "closed"
            }


class ShiftManagementScreen(QWidget):
    """Shift management screen for operator shifts and reconciliation."""

    def __init__(self, user):
        """Initialize shift management screen."""
        super().__init__()
        self.user = user
        self.db_service = DatabaseService()

        self.setWindowTitle("Shift Management")
        self.setGeometry(100, 100, 1200, 700)

        self.shifts = []
        self.users = []

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout()

        # Header
        header = QLabel("Shift Management")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        # Summary layout
        summary_layout = QHBoxLayout()

        self.active_shifts_label = QLabel("Active Shifts: 0")
        self.today_shift_hours_label = QLabel("Total Hours Today: 0 hrs")
        self.shift_count_label = QLabel("Today's Shifts: 0")

        summary_layout.addWidget(self.active_shifts_label)
        summary_layout.addWidget(self.today_shift_hours_label)
        summary_layout.addWidget(self.shift_count_label)
        summary_layout.addStretch()

        main_layout.addLayout(summary_layout)

        # Filter layout
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Status:")
        self.status_filter = QComboBox()
        self.status_filter.addItem("All", "")
        self.status_filter.addItems(["Open", "Closed"])
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()

        main_layout.addLayout(filter_layout)

        # Shifts table
        self.shifts_table = QTableWidget()
        self.shifts_table.setColumnCount(9)
        self.shifts_table.setHorizontalHeaderLabels([
            "Operator", "Opening Time", "Closing Time", "Status",
            "Opening Cash (Rs)", "Closing Cash (Rs)", "Hours", "Sales (Rs)", "Actions"
        ])
        self.shifts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.shifts_table)

        # Buttons
        button_layout = QHBoxLayout()
        open_shift_btn = QPushButton("Open New Shift")
        open_shift_btn.clicked.connect(self.open_shift)
        button_layout.addWidget(open_shift_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def load_data(self):
        """Load shifts and users from database."""
        try:
            # Load shifts
            self.shifts = self.db_service.list_documents("shifts")

            # Load users
            user_docs = self.db_service.list_documents("users")
            self.users = [User(**doc) if isinstance(doc, dict) else doc for doc in user_docs]

            self.populate_shifts_table(self.shifts)
            self.update_summary()

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def populate_shifts_table(self, shifts):
        """Populate shifts table."""
        self.shifts_table.setRowCount(len(shifts))

        for row, shift_data in enumerate(shifts):
            shift = Shift(**shift_data) if isinstance(shift_data, dict) else shift_data

            # Operator
            operator = next(
                (u for u in self.users if u.id == shift.operator_id),
                None
            )
            operator_text = operator.name if operator else "Unknown"
            self.shifts_table.setItem(row, 0, QTableWidgetItem(operator_text))

            # Opening time
            opening_time = shift.shift_start[:16] if shift.shift_start else "---"
            self.shifts_table.setItem(row, 1, QTableWidgetItem(opening_time))

            # Closing time
            closing_time = shift.shift_end[:16] if shift.shift_end else "---"
            self.shifts_table.setItem(row, 2, QTableWidgetItem(closing_time))

            # Status
            status_text = shift.status.upper() if shift.status else "OPEN"
            status_item = QTableWidgetItem(status_text)
            status_color = QColor("green") if shift.status == "open" else QColor("gray")
            status_item.setForeground(status_color)
            self.shifts_table.setItem(row, 3, status_item)

            # Opening cash
            opening_cash = f"Rs. {shift.opening_cash}" if shift.opening_cash else "---"
            self.shifts_table.setItem(row, 4, QTableWidgetItem(opening_cash))

            # Closing cash
            closing_cash = f"Rs. {shift.closing_cash}" if shift.closing_cash else "---"
            self.shifts_table.setItem(row, 5, QTableWidgetItem(closing_cash))

            # Hours
            if shift.shift_start and shift.shift_end:
                start = datetime.fromisoformat(shift.shift_start)
                end = datetime.fromisoformat(shift.shift_end)
                hours = (end - start).total_seconds() / 3600
                hours_text = f"{hours:.1f} hrs"
            else:
                hours_text = "---"
            self.shifts_table.setItem(row, 6, QTableWidgetItem(hours_text))

            # Sales
            sales_text = f"Rs. {shift.sales_amount}" if shift.sales_amount else "---"
            self.shifts_table.setItem(row, 7, QTableWidgetItem(sales_text))

            # Actions
            action_layout = QHBoxLayout()

            if shift.status == "open":
                close_btn = QPushButton("Close Shift")
                close_btn.clicked.connect(lambda checked, s=shift: self.close_shift(s))
                action_layout.addWidget(close_btn)
            else:
                view_btn = QPushButton("View Details")
                view_btn.clicked.connect(lambda checked, s=shift: self.view_shift_details(s))
                action_layout.addWidget(view_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, s=shift: self.delete_shift(s))
            action_layout.addWidget(delete_btn)

            action_widget = QWidget()
            action_layout.addStretch()
            action_widget.setLayout(action_layout)

            self.shifts_table.setCellWidget(row, 8, action_widget)

    def apply_filters(self):
        """Apply status filter to shifts."""
        selected_status = self.status_filter.currentData()
        if selected_status:
            filtered = [
                s for s in self.shifts
                if isinstance(s, dict) and s.get('status') == selected_status.lower()
                or (not isinstance(s, dict) and s.status == selected_status.lower())
            ]
        else:
            filtered = self.shifts

        self.populate_shifts_table(filtered)

    def update_summary(self):
        """Update summary statistics."""
        active = sum(
            1 for s in self.shifts
            if isinstance(s, dict) and s.get('status') == 'open'
            or (not isinstance(s, dict) and s.status == 'open')
        )

        from datetime import date
        today = date.today().isoformat()
        today_shifts = [
            s for s in self.shifts
            if isinstance(s, dict) and s.get('shift_start', '')[:10] == today
            or (not isinstance(s, dict) and s.shift_start[:10] == today)
        ]

        total_hours = 0
        for shift_data in today_shifts:
            shift = Shift(**shift_data) if isinstance(shift_data, dict) else shift_data
            if shift.shift_start and shift.shift_end:
                try:
                    start = datetime.fromisoformat(shift.shift_start)
                    end = datetime.fromisoformat(shift.shift_end)
                    total_hours += (end - start).total_seconds() / 3600
                except:
                    pass

        self.active_shifts_label.setText(f"Active Shifts: {active}")
        self.today_shift_hours_label.setText(f"Total Hours Today: {total_hours:.1f} hrs")
        self.shift_count_label.setText(f"Today's Shifts: {len(today_shifts)}")

    def open_shift(self):
        """Open a new shift."""
        dialog = ShiftDialog(self, users=self.users)
        if dialog.exec_() == QDialog.Accepted:
            try:
                shift_data = dialog.get_shift_data()
                shift_data.update({
                    "status": "open",
                    "created_at": datetime.now().isoformat(),
                    "created_by": self.user.id
                })

                success, message = self.db_service.create_document(
                    "shifts",
                    f"shift_{datetime.now().timestamp()}",
                    shift_data,
                    self.user.id
                )

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error opening shift: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to open shift: {str(e)}")

    def close_shift(self, shift):
        """Close an open shift."""
        dialog = ShiftDialog(self, shift, is_closing=True)
        if dialog.exec_() == QDialog.Accepted:
            try:
                closure_data = dialog.get_shift_data()
                success, message = self.db_service.update_document(
                    "shifts",
                    shift.id,
                    closure_data
                )

                if success:
                    QMessageBox.information(self, "Success", "Shift closed successfully")
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error closing shift: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to close shift: {str(e)}")

    def view_shift_details(self, shift):
        """View detailed information for a shift."""
        operator = next(
            (u for u in self.users if u.id == shift.operator_id),
            None
        )
        operator_name = operator.name if operator else "Unknown"

        hours = "---"
        if shift.shift_start and shift.shift_end:
            try:
                start = datetime.fromisoformat(shift.shift_start)
                end = datetime.fromisoformat(shift.shift_end)
                hours = f"{(end - start).total_seconds() / 3600:.1f} hrs"
            except:
                pass

        details = f"""
Shift Details
=============

Operator: {operator_name}
Status: {shift.status.upper()}

Start Time: {shift.shift_start or 'N/A'}
End Time: {shift.shift_end or 'N/A'}
Duration: {hours}

Cash In Hand
============
Opening: Rs. {shift.opening_cash or '0'}
Closing: Rs. {shift.closing_cash or '0'}

Sales During Shift: Rs. {shift.sales_amount or '0'}

Notes: {shift.notes or 'No notes'}
        """
        QMessageBox.information(self, f"Shift Details", details)

    def delete_shift(self, shift):
        """Delete a shift."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this shift?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success, message = self.db_service.delete_document("shifts", shift.id)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error deleting shift: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete shift: {str(e)}")
