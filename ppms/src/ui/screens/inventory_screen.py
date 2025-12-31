"""
Inventory Management Screen - Update tank stock levels
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QWidget, QMessageBox, QHeaderView,
    QDoubleSpinBox, QFormLayout
)
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from src.config.logger_config import setup_logger

logger = setup_logger(__name__)


class UpdateStockLevelDialog(QDialog):
    """Dialog for updating tank inventory stock levels."""

    def __init__(self, tank_service, fuel_service, db_service, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.tank_service = tank_service
        self.fuel_service = fuel_service
        self.db_service = db_service
        self.tanks = []
        self.fuels = {}
        self.parent_dashboard = parent  # Store reference to parent dashboard
        
        self.setWindowTitle("Update Tank Inventory")
        self.setGeometry(200, 200, 800, 600)
        self.load_data()
        self.init_ui()

    def load_data(self):
        """Load tanks and fuel types."""
        try:
            self.tanks = self.tank_service.list_tanks()
            fuel_list = self.fuel_service.list_fuel_types()
            for fuel in fuel_list:
                self.fuels[fuel.id] = fuel.name
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Header
        header = QLabel("Tank Inventory Management")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(header)

        # Info label
        info_label = QLabel("View and update current fuel inventory levels for each tank")
        layout.addWidget(info_label)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Tank", "Fuel Type", "Capacity (L)", "Current Stock (L)", 
            "Minimum Stock (L)", "Stock %", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnWidth(6, 100)  # Set Actions column width
        layout.addWidget(self.table)

        # Populate table
        self.populate_table()

        # Buttons
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_and_refresh)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def populate_table(self):
        """Populate tanks table."""
        self.table.setRowCount(len(self.tanks))

        for row, tank in enumerate(self.tanks):
            # Tank name
            name_item = QTableWidgetItem(tank.name)
            name_item.setFlags(name_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.table.setItem(row, 0, name_item)

            # Fuel type
            fuel_name = self.fuels.get(tank.fuel_type_id, "Unknown")
            fuel_item = QTableWidgetItem(fuel_name)
            fuel_item.setFlags(fuel_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.table.setItem(row, 1, fuel_item)

            # Capacity
            capacity_item = QTableWidgetItem(f"{tank.capacity:.2f}")
            capacity_item.setFlags(capacity_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.table.setItem(row, 2, capacity_item)

            # Current stock
            current_item = QTableWidgetItem(f"{tank.current_stock:.2f}")
            current_item.setFlags(current_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.table.setItem(row, 3, current_item)

            # Minimum stock
            min_item = QTableWidgetItem(f"{tank.minimum_stock:.2f}")
            min_item.setFlags(min_item.flags() & ~0x2)  # Qt.ItemIsEditable
            self.table.setItem(row, 4, min_item)

            # Stock percentage
            if isinstance(tank, dict):
                # If tank is a dictionary
                percentage = (tank.get('current_stock', 0) / tank.get('capacity', 1)) * 100 if tank.get('capacity', 0) > 0 else 0
            else:
                # If tank is an object
                percentage = tank.stock_percentage if hasattr(tank, 'stock_percentage') else \
                    (tank.current_stock / tank.capacity * 100) if tank.capacity > 0 else 0
            
            percentage_item = QTableWidgetItem(f"{percentage:.1f}%")
            percentage_item.setFlags(percentage_item.flags() & ~0x2)  # Qt.ItemIsEditable
            # Color code: red if low, yellow if medium, green if good
            if percentage < 25:
                percentage_item.setBackground(QColor("#ffcccc"))
            elif percentage < 50:
                percentage_item.setBackground(QColor("#ffffcc"))
            else:
                percentage_item.setBackground(QColor("#ccffcc"))
            self.table.setItem(row, 5, percentage_item)

            # Actions - Update button
            update_btn = QPushButton("Update")
            update_btn.setMaximumWidth(80)
            update_btn.clicked.connect(lambda checked, t=tank: self.update_tank_stock(t))
            self.table.setCellWidget(row, 6, update_btn)

    def update_tank_stock(self, tank):
        """Update stock level for a specific tank."""
        dialog = UpdateTankStockDialog(tank, self)
        if dialog.exec_() == QDialog.Accepted:
            old_stock = tank.current_stock
            new_stock = dialog.get_stock_level()
            quantity_added = new_stock - old_stock
            
            try:
                success, message = self.db_service.update_document(
                    'tanks',
                    tank.id,
                    {
                        'current_stock': new_stock,
                        'last_reading_date': datetime.now().isoformat()
                    }
                )
                
                if success:
                    # Show warning about purchase entry requirement
                    QMessageBox.warning(
                        self, 
                        "Purchase Entry Required", 
                        f"Tank inventory has been updated. You must record the purchase entry to settle the account head."
                    )
                    
                    # Show information window with option to record purchase
                    info_dialog = InventoryUpdateInfoDialog(
                        tank, 
                        old_stock, 
                        new_stock, 
                        quantity_added,
                        self.parent_dashboard,
                        self
                    )
                    info_dialog.exec_()
                    
                    self.load_and_refresh()
                else:
                    QMessageBox.warning(self, "Error", message)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update stock: {str(e)}")

    def load_and_refresh(self):
        """Reload data and refresh table."""
        self.load_data()
        self.populate_table()


class UpdateTankStockDialog(QDialog):
    """Dialog for updating a single tank's stock level."""

    def __init__(self, tank, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.tank = tank
        self.setWindowTitle(f"Update {tank.name} Stock Level")
        self.setGeometry(300, 300, 400, 250)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()

        # Tank info
        layout.addRow("Tank:", QLabel(self.tank.name))
        layout.addRow("Capacity (L):", QLabel(f"{self.tank.capacity:.2f}"))
        layout.addRow("Minimum Stock (L):", QLabel(f"{self.tank.minimum_stock:.2f}"))

        layout.addRow(QLabel(""))  # Spacer

        # Current stock input
        self.stock_input = QDoubleSpinBox()
        self.stock_input.setRange(0, self.tank.capacity)
        self.stock_input.setDecimals(2)
        self.stock_input.setValue(self.tank.current_stock)
        self.stock_input.setSuffix(" L")
        layout.addRow("New Stock Level (L):", self.stock_input)

        # Warning if below minimum
        if self.tank.current_stock < self.tank.minimum_stock:
            warning_label = QLabel(f"⚠️ Current stock is below minimum ({self.tank.minimum_stock:.2f}L)")
            warning_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addRow(warning_label)

        layout.addRow(QLabel(""))  # Spacer

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Update")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)

        self.setLayout(layout)

    def validate_and_accept(self):
        """Validate and accept."""
        stock = self.stock_input.value()
        
        if stock > self.tank.capacity:
            QMessageBox.warning(
                self, 
                "Validation Error", 
                f"Stock level cannot exceed tank capacity ({self.tank.capacity:.2f}L)"
            )
            return

        self.accept()

    def get_stock_level(self):
        """Get the new stock level."""
        return self.stock_input.value()


class InventoryUpdateInfoDialog(QDialog):
    """Dialog showing inventory update information and option to record purchase."""

    def __init__(self, tank, old_stock, new_stock, quantity_added, parent_dashboard, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.tank = tank
        self.old_stock = old_stock
        self.new_stock = new_stock
        self.quantity_added = quantity_added
        self.parent_dashboard = parent_dashboard
        self.purchase_recorded = False
        
        self.setWindowTitle("Inventory Update - Record Purchase")
        self.setGeometry(300, 300, 500, 400)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("Tank Inventory Updated")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Information section
        info_layout = QFormLayout()
        
        info_layout.addRow("Tank:", QLabel(self.tank.name))
        info_layout.addRow("Quantity Added (L):", QLabel(f"{self.quantity_added:.2f}"))
        info_layout.addRow("Previous Stock (L):", QLabel(f"{self.old_stock:.2f}"))
        info_layout.addRow("Current Stock (L):", QLabel(f"{self.new_stock:.2f}"))
        info_layout.addRow("Tank Capacity (L):", QLabel(f"{self.tank.capacity:.2f}"))
        
        layout.addLayout(info_layout)

        # Status message
        status_label = QLabel("⚠️ You must now record the purchase entry to settle the account head.")
        status_label.setStyleSheet("color: #FF6B6B; font-weight: bold; padding: 10px; background-color: #FFE0E0; border-radius: 4px;")
        layout.addWidget(status_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        
        purchase_btn = QPushButton("📝 Record Purchase")
        purchase_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0b7dda; }"
        )
        purchase_btn.clicked.connect(self.open_purchase_dialog)
        button_layout.addWidget(purchase_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #6C757D; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #5A6268; }"
        )
        close_btn.clicked.connect(self.close_dialog)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def open_purchase_dialog(self):
        """Open record purchase dialog with pre-filled values."""
        if self.parent_dashboard:
            # Create a purchase dialog and pre-fill with tank and quantity
            from src.ui.screens.dashboard_screen import RecordPurchaseDialog
            
            purchase_dialog = RecordPurchaseDialog(
                self.parent_dashboard.fuel_service,
                self.parent_dashboard.tank_service,
                self.parent_dashboard.db_service,
                self.parent_dashboard.account_head_service,
                self
            )
            
            # Pre-fill the first row with tank and quantity
            if purchase_dialog.table.rowCount() > 0:
                # Set tank combo
                tank_combo = purchase_dialog.table.cellWidget(0, 0)
                if tank_combo:
                    # Find and select the tank
                    for i in range(tank_combo.count()):
                        if tank_combo.itemData(i) == self.tank.id:
                            tank_combo.setCurrentIndex(i)
                            break
                
                # Set supplier name (empty for user to fill)
                supplier_item = purchase_dialog.table.item(0, 1)
                if supplier_item:
                    supplier_item.setText("")
                
                # Set quantity
                qty_item = purchase_dialog.table.item(0, 2)
                if qty_item:
                    qty_item.setText(f"{self.quantity_added:.2f}")
                
                # Unit cost (empty for user to fill)
                cost_item = purchase_dialog.table.item(0, 3)
                if cost_item:
                    cost_item.setText("")
                
                # Trigger calculation
                purchase_dialog.on_cell_changed(qty_item)
            
            # Show purchase dialog
            purchase_dialog.exec_()
            
            # After purchase dialog closes, mark as recorded and close this dialog
            self.purchase_recorded = True
            QMessageBox.information(
                self,
                "Success",
                "Purchase entry dialog closed. Account head settlement is complete."
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Cannot access purchase dialog")

    def close_dialog(self):
        """Close the dialog."""
        if self.purchase_recorded:
            self.accept()
        else:
            reply = QMessageBox.warning(
                self,
                "Unsettled Account Head",
                "Purchase entry has not been recorded. The account head remains unsettled.\n\nAre you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.reject()
