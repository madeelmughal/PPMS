"""
Sales Entry Screen - Record fuel sales for nozzles
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox,
    QLineEdit, QDialog, QFormLayout, QMessageBox, QHeaderView,
    QComboBox, QDateTimeEdit, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
from PyQt5.QtGui import QFont, QColor
from src.services.database_service import (
    SalesService, FuelService, TankService, NozzleService, DatabaseService
)
from src.models import Sale, Reading
from src.utils.validators import validate_currency
from src.config.logger_config import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class SaleDialog(QDialog):
    """Dialog for recording a fuel sale."""

    def __init__(self, parent=None, fuel_types=None, nozzles=None, sale=None):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            fuel_types: List of available FuelType objects
            nozzles: List of available Nozzle objects
            sale: Existing Sale to edit (None for new)
        """
        super().__init__(parent)
        self.fuel_types = fuel_types or []
        self.nozzles = nozzles or []
        self.sale = sale
        self.setWindowTitle("Record Sale" if sale is None else f"Edit Sale #{sale.id}")
        self.setGeometry(200, 200, 500, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()

        # Nozzle
        self.nozzle_combo = QComboBox()
        for nozzle in self.nozzles:
            self.nozzle_combo.addItem(f"Nozzle {nozzle.nozzle_number}", nozzle.id)
        if self.sale:
            index = self.nozzle_combo.findData(self.sale.nozzle_id)
            self.nozzle_combo.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Nozzle:", self.nozzle_combo)

        # Fuel type
        self.fuel_combo = QComboBox()
        for fuel in self.fuel_types:
            self.fuel_combo.addItem(fuel.name, fuel.id)
        if self.sale:
            index = self.fuel_combo.findData(self.sale.fuel_type_id)
            self.fuel_combo.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Fuel Type:", self.fuel_combo)

        # Quantity (Liters)
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0, 100000)
        self.quantity_input.setDecimals(2)
        self.quantity_input.setSuffix(" L")
        if self.sale:
            self.quantity_input.setValue(float(self.sale.quantity))
        layout.addRow("Quantity (Liters):", self.quantity_input)

        # Unit price
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setRange(0, 10000)
        self.unit_price_input.setDecimals(2)
        self.unit_price_input.setSuffix(" Rs/L")
        if self.sale:
            self.unit_price_input.setValue(float(self.sale.unit_price))
        layout.addRow("Unit Price (Rs/L):", self.unit_price_input)

        # Payment method
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Cash", "Card", "Credit", "Check"])
        if self.sale and self.sale.payment_method:
            index = self.payment_combo.findText(self.sale.payment_method)
            self.payment_combo.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Payment Method:", self.payment_combo)

        # Customer name (optional)
        self.customer_input = QLineEdit()
        if self.sale and self.sale.customer_name:
            self.customer_input.setText(self.sale.customer_name)
        layout.addRow("Customer Name (Optional):", self.customer_input)

        # Vehicle number (optional)
        self.vehicle_input = QLineEdit()
        if self.sale and self.sale.vehicle_number:
            self.vehicle_input.setText(self.sale.vehicle_number)
        layout.addRow("Vehicle Number (Optional):", self.vehicle_input)

        # Notes (optional)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        if self.sale and self.sale.notes:
            self.notes_input.setPlainText(self.sale.notes)
        layout.addRow("Notes (Optional):", self.notes_input)

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
        if self.quantity_input.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0")
            return

        if self.unit_price_input.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Unit price must be greater than 0")
            return

        self.accept()

    def get_sale(self) -> Sale:
        """
        Get the sale from the dialog.

        Returns:
            Sale object
        """
        total_amount = self.quantity_input.value() * self.unit_price_input.value()

        return Sale(
            id=self.sale.id if self.sale else None,
            nozzle_id=self.nozzle_combo.currentData(),
            fuel_type_id=self.fuel_combo.currentData(),
            quantity=str(self.quantity_input.value()),
            unit_price=str(self.unit_price_input.value()),
            total_amount=str(total_amount),
            payment_method=self.payment_combo.currentText(),
            customer_name=self.customer_input.text() or None,
            vehicle_number=self.vehicle_input.text() or None,
            notes=self.notes_input.toPlainText() or None,
            sale_date=self.sale.sale_date if self.sale else datetime.now().isoformat(),
            created_at=self.sale.created_at if self.sale else datetime.now().isoformat(),
            created_by=self.sale.created_by if self.sale else ""
        )


class SalesEntryScreen(QWidget):
    """Sales entry screen for recording fuel sales."""

    def __init__(self, user):
        """Initialize sales entry screen."""
        super().__init__()
        self.user = user
        self.sales_service = SalesService()
        self.fuel_service = FuelService()
        self.tank_service = TankService()
        self.nozzle_service = NozzleService()
        self.db_service = DatabaseService()

        self.setWindowTitle("Sales Entry")
        self.setGeometry(100, 100, 1200, 700)

        self.sales = []
        self.fuel_types = []
        self.nozzles = []

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout()

        # Header
        header = QLabel("Sales Entry")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        # Summary layout
        summary_layout = QHBoxLayout()

        self.total_sales_label = QLabel("Total Sales Today: Rs. 0")
        self.total_liters_label = QLabel("Total Liters: 0 L")
        self.transactions_label = QLabel("Transactions: 0")

        summary_layout.addWidget(self.total_sales_label)
        summary_layout.addWidget(self.total_liters_label)
        summary_layout.addWidget(self.transactions_label)
        summary_layout.addStretch()

        main_layout.addLayout(summary_layout)

        # Sales table
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(8)
        self.sales_table.setHorizontalHeaderLabels([
            "Nozzle", "Fuel Type", "Quantity (L)", "Unit Price (Rs/L)",
            "Total Amount (Rs)", "Payment Method", "Customer", "Actions"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.sales_table)

        # Buttons
        button_layout = QHBoxLayout()
        add_sale_btn = QPushButton("Record Sale")
        add_sale_btn.clicked.connect(self.add_sale)
        button_layout.addWidget(add_sale_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def load_data(self):
        """Load sales and related data from database."""
        try:
            # Load fuel types
            self.fuel_types = self.fuel_service.get_all_fuel_types()

            # Load nozzles
            self.nozzles = self.nozzle_service.get_all_nozzles()

            # Load today's sales
            from datetime import date
            today = date.today().isoformat()
            self.sales = self.sales_service.get_sales_by_date(today)

            self.populate_sales_table()
            self.update_summary()

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def populate_sales_table(self):
        """Populate sales table."""
        self.sales_table.setRowCount(len(self.sales))

        for row, sale in enumerate(self.sales):
            # Nozzle
            nozzle = next(
                (n for n in self.nozzles if n.id == sale.nozzle_id),
                None
            )
            nozzle_text = f"Nozzle {nozzle.nozzle_number}" if nozzle else "Unknown"
            self.sales_table.setItem(row, 0, QTableWidgetItem(nozzle_text))

            # Fuel type
            fuel = next(
                (f for f in self.fuel_types if f.id == sale.fuel_type_id),
                None
            )
            fuel_text = fuel.name if fuel else "Unknown"
            self.sales_table.setItem(row, 1, QTableWidgetItem(fuel_text))

            # Quantity
            self.sales_table.setItem(row, 2, QTableWidgetItem(f"{sale.quantity} L"))

            # Unit price
            self.sales_table.setItem(row, 3, QTableWidgetItem(f"Rs. {sale.unit_price}"))

            # Total amount
            self.sales_table.setItem(row, 4, QTableWidgetItem(f"Rs. {sale.total_amount}"))

            # Payment method
            self.sales_table.setItem(row, 5, QTableWidgetItem(sale.payment_method))

            # Customer
            customer_text = sale.customer_name or "Walk-in"
            self.sales_table.setItem(row, 6, QTableWidgetItem(customer_text))

            # Actions
            action_layout = QHBoxLayout()
            edit_btn = QPushButton("Edit")
            delete_btn = QPushButton("Delete")

            edit_btn.clicked.connect(lambda checked, s=sale: self.edit_sale(s))
            delete_btn.clicked.connect(lambda checked, s=sale: self.delete_sale(s))

            action_widget = QWidget()
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_widget.setLayout(action_layout)

            self.sales_table.setCellWidget(row, 7, action_widget)

    def update_summary(self):
        """Update summary statistics."""
        total_sales = sum(float(s.total_amount) for s in self.sales)
        total_liters = sum(float(s.quantity) for s in self.sales)
        transactions = len(self.sales)

        self.total_sales_label.setText(f"Total Sales Today: Rs. {total_sales:,.2f}")
        self.total_liters_label.setText(f"Total Liters: {total_liters:,.2f} L")
        self.transactions_label.setText(f"Transactions: {transactions}")

    def add_sale(self):
        """Add a new sale."""
        dialog = SaleDialog(self, self.fuel_types, self.nozzles)
        if dialog.exec_() == QDialog.Accepted:
            try:
                sale = dialog.get_sale()
                success, message = self.sales_service.add_sale(sale, self.user.id)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error adding sale: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to add sale: {str(e)}")

    def edit_sale(self, sale):
        """Edit an existing sale."""
        dialog = SaleDialog(self, self.fuel_types, self.nozzles, sale)
        if dialog.exec_() == QDialog.Accepted:
            try:
                updated_sale = dialog.get_sale()
                success, message = self.sales_service.update_sale(sale.id, updated_sale)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error updating sale: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to update sale: {str(e)}")

    def delete_sale(self, sale):
        """Delete a sale."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this sale (Rs. {sale.total_amount})?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success, message = self.sales_service.delete_sale(sale.id)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error deleting sale: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete sale: {str(e)}")
