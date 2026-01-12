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
    SalesService, FuelService, TankService, NozzleService, DatabaseService, AccountHeadService
)
from src.models import Sale, Reading
from src.utils.validators import validate_currency
from src.config.logger_config import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class SaleDialog(QDialog):
    """Dialog for recording a fuel sale."""

    def __init__(self, parent=None, fuel_types=None, nozzles=None, sale=None, payment_methods=None, current_opening_reading=None):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            fuel_types: List of available FuelType objects
            nozzles: List of available Nozzle objects
            sale: Existing Sale to edit (None for new)
            payment_methods: List of payment method names from account heads
            current_opening_reading: Current opening reading for nozzle (for dynamic calculation)
        """
        super().__init__(parent)
        self.fuel_types = fuel_types or []
        self.nozzles = nozzles or []
        self.sale = sale
        self.payment_methods = payment_methods if payment_methods is not None else []
        self.current_opening_reading = current_opening_reading or 0.0
        self.setWindowTitle("Record Sale" if sale is None else f"Edit Sale #{sale.id}")
        self.setGeometry(200, 200, 500, 600)
        
        # Apply stylesheet to fix visibility issues
        self.setStyleSheet(
            "QLineEdit { color: black; background-color: white; border: 1px solid #ccc; padding: 3px; }"
            "QLineEdit:focus { background-color: white; color: black; border: 2px solid #2196F3; }"
            "QDoubleSpinBox { color: black; background-color: white; border: 1px solid #ccc; padding: 2px; }"
            "QDoubleSpinBox:focus { background-color: white; color: black; border: 2px solid #2196F3; }"
            "QComboBox { color: black; background-color: white; border: 1px solid #ccc; padding: 2px; }"
            "QComboBox:focus { background-color: white; color: black; border: 2px solid #2196F3; }"
            "QTextEdit { color: black; background-color: white; border: 1px solid #ccc; }"
            "QTextEdit:focus { background-color: white; color: black; border: 2px solid #2196F3; }"
        )
        
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
        self.nozzle_combo.currentIndexChanged.connect(self.update_opening_reading)
        layout.addRow("Nozzle:", self.nozzle_combo)

        # Fuel type
        self.fuel_combo = QComboBox()
        for fuel in self.fuel_types:
            self.fuel_combo.addItem(fuel.name, fuel.id)
        if self.sale:
            index = self.fuel_combo.findData(self.sale.fuel_type_id)
            self.fuel_combo.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Fuel Type:", self.fuel_combo)

        # Opening Reading
        self.opening_reading_input = QDoubleSpinBox()
        self.opening_reading_input.setRange(0, 999999)
        self.opening_reading_input.setDecimals(2)
        if self.sale and hasattr(self.sale, 'opening_reading'):
            self.opening_reading_input.setValue(float(self.sale.opening_reading))
        else:
            self.opening_reading_input.setValue(float(self.current_opening_reading))
        layout.addRow("Opening Reading:", self.opening_reading_input)

        # Closing Reading
        self.closing_reading_input = QDoubleSpinBox()
        self.closing_reading_input.setRange(0, 999999)
        self.closing_reading_input.setDecimals(2)
        if self.sale and hasattr(self.sale, 'closing_reading'):
            self.closing_reading_input.setValue(float(self.sale.closing_reading))
        self.closing_reading_input.valueChanged.connect(self.update_quantity_from_readings)
        layout.addRow("Closing Reading:", self.closing_reading_input)

        # Quantity (Liters)
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0, 100000)
        self.quantity_input.setDecimals(2)
        self.quantity_input.setSuffix(" L")
        if self.sale:
            self.quantity_input.setValue(float(self.sale.quantity))
        self.quantity_input.valueChanged.connect(self.update_closing_reading_from_quantity)
        layout.addRow("Quantity (Liters):", self.quantity_input)

        # Unit price
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setRange(0, 10000)
        self.unit_price_input.setDecimals(2)
        self.unit_price_input.setSuffix(" Rs/L")
        if self.sale:
            self.unit_price_input.setValue(float(self.sale.unit_price))
        layout.addRow("Unit Price (Rs/L):", self.unit_price_input)

        # Payment method - loaded from account heads
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(self.payment_methods)
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

    def update_opening_reading(self):
        """Update opening reading when nozzle changes."""
        nozzle_id = self.nozzle_combo.currentData()
        if nozzle_id:
            nozzle = next((n for n in self.nozzles if n.id == nozzle_id), None)
            if nozzle:
                current_reading = nozzle.closing_reading if nozzle.closing_reading > 0 else nozzle.opening_reading
                self.opening_reading_input.setValue(float(current_reading))
                self.current_opening_reading = float(current_reading)

    def update_quantity_from_readings(self):
        """Calculate quantity from opening and closing readings."""
        opening = self.opening_reading_input.value()
        closing = self.closing_reading_input.value()
        if closing >= opening:
            calculated_qty = closing - opening
            # Only update if user manually changed closing reading
            self.quantity_input.blockSignals(True)
            self.quantity_input.setValue(calculated_qty)
            self.quantity_input.blockSignals(False)

    def update_closing_reading_from_quantity(self):
        """Calculate closing reading from quantity."""
        opening = self.opening_reading_input.value()
        quantity = self.quantity_input.value()
        calculated_closing = opening + quantity
        # Only update if user manually changed quantity
        self.closing_reading_input.blockSignals(True)
        self.closing_reading_input.setValue(calculated_closing)
        self.closing_reading_input.blockSignals(False)

    def validate_and_accept(self):
        """Validate inputs before accepting."""
        if self.quantity_input.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0")
            return

        if self.unit_price_input.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Unit price must be greater than 0")
            return

        if self.opening_reading_input.value() < 0:
            QMessageBox.warning(self, "Validation Error", "Opening reading must be >= 0")
            return

        if self.closing_reading_input.value() <= self.opening_reading_input.value():
            QMessageBox.warning(self, "Validation Error", "Closing reading must be greater than opening reading")
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
            opening_reading=str(self.opening_reading_input.value()),
            closing_reading=str(self.closing_reading_input.value()),
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
        self.account_head_service = AccountHeadService()

        self.setWindowTitle("Sales Entry")
        self.setGeometry(100, 100, 1200, 700)

        self.sales = []
        self.fuel_types = []
        self.nozzles = []
        self.payment_methods = []

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

            # Load payment methods from account heads
            self.payment_methods = self.account_head_service.get_payment_methods()

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
            nozzle_item = QTableWidgetItem(nozzle_text)
            nozzle_item.setFlags(nozzle_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.sales_table.setItem(row, 0, nozzle_item)

            # Fuel type
            fuel = next(
                (f for f in self.fuel_types if f.id == sale.fuel_type_id),
                None
            )
            fuel_text = fuel.name if fuel else "Unknown"
            fuel_item = QTableWidgetItem(fuel_text)
            fuel_item.setFlags(fuel_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.sales_table.setItem(row, 1, fuel_item)

            # Quantity
            qty_item = QTableWidgetItem(f"{sale.quantity} L")
            qty_item.setFlags(qty_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.sales_table.setItem(row, 2, qty_item)

            # Unit price
            price_item = QTableWidgetItem(f"Rs. {sale.unit_price}")
            price_item.setFlags(price_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.sales_table.setItem(row, 3, price_item)

            # Total amount
            total_item = QTableWidgetItem(f"Rs. {sale.total_amount}")
            total_item.setFlags(total_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.sales_table.setItem(row, 4, total_item)

            # Payment method
            payment_item = QTableWidgetItem(sale.payment_method)
            payment_item.setFlags(payment_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.sales_table.setItem(row, 5, payment_item)

            # Customer
            customer_text = sale.customer_name or "Walk-in"
            customer_item = QTableWidgetItem(customer_text)
            customer_item.setFlags(customer_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.sales_table.setItem(row, 6, customer_item)

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
        # Get current nozzle opening reading
        current_opening_reading = 0.0
        
        dialog = SaleDialog(self, self.fuel_types, self.nozzles, payment_methods=self.payment_methods, current_opening_reading=current_opening_reading)
        if dialog.exec_() == QDialog.Accepted:
            try:
                sale = dialog.get_sale()
                
                # Get nozzle and fuel details for inventory check
                nozzle = next((n for n in self.nozzles if n.id == sale.nozzle_id), None)
                if not nozzle:
                    QMessageBox.warning(self, "Error", "Nozzle not found")
                    return
                
                fuel = next((f for f in self.fuel_types if f.id == sale.fuel_type_id), None)
                if not fuel:
                    QMessageBox.warning(self, "Error", "Fuel type not found")
                    return
                
                # Get tank and check inventory
                tanks = self.tank_service.list_tanks()
                tank = next((t for t in tanks if t.fuel_type_id == fuel.id), None)
                if not tank:
                    QMessageBox.warning(self, "Error", f"No tank configured for {fuel.name}")
                    return
                
                quantity = float(sale.quantity)
                if tank.current_stock < quantity:
                    QMessageBox.warning(self, "Insufficient Inventory", 
                        f"Insufficient {fuel.name} inventory.\nAvailable: {tank.current_stock:.2f}L\nRequired: {quantity:.2f}L")
                    return
                
                # Record sale
                success, message = self.sales_service.add_sale(sale, self.user.id)

                if success:
                    # Update nozzle closing reading to match the sale's closing reading
                    closing_reading = float(sale.closing_reading)
                    nozzle.closing_reading = closing_reading
                    self.nozzle_service.update_nozzle(nozzle.id, nozzle)
                    
                    # Update tank inventory
                    new_stock = tank.current_stock - quantity
                    stock_success, stock_msg = self.tank_service.update_tank_stock(tank.id, new_stock)
                    
                    if stock_success:
                        QMessageBox.information(self, "Success", f"Sale recorded successfully!\nInventory updated.")
                        self.load_data()
                    else:
                        QMessageBox.warning(self, "Warning", f"Sale recorded but inventory update failed: {stock_msg}")
                        self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error adding sale: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to add sale: {str(e)}")

    def edit_sale(self, sale):
        """Edit an existing sale."""
        dialog = SaleDialog(self, self.fuel_types, self.nozzles, sale, payment_methods=self.payment_methods)
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
            f"Are you sure you want to delete this sale (Rs. {sale.total_amount})?\nInventory will be restored.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Get fuel and tank info to restore inventory
                fuel = next((f for f in self.fuel_types if f.id == sale.fuel_type_id), None)
                if not fuel:
                    QMessageBox.warning(self, "Error", "Fuel type not found")
                    return
                
                tanks = self.tank_service.list_tanks()
                tank = next((t for t in tanks if t.fuel_type_id == fuel.id), None)
                if not tank:
                    QMessageBox.warning(self, "Error", f"Tank for {fuel.name} not found")
                    return
                
                # Delete sale
                success, message = self.sales_service.delete_sale(sale.id)

                if success:
                    # Restore tank inventory
                    quantity = float(sale.quantity)
                    new_stock = tank.current_stock + quantity
                    stock_success, stock_msg = self.tank_service.update_tank_stock(tank.id, new_stock)
                    
                    if stock_success:
                        QMessageBox.information(self, "Success", f"Sale deleted successfully!\nInventory restored: +{quantity:.2f}L")
                        self.load_data()
                    else:
                        QMessageBox.warning(self, "Warning", f"Sale deleted but inventory restore failed: {stock_msg}")
                        self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error deleting sale: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete sale: {str(e)}")
