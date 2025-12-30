"""
Fuel Management Screen - Manage fuel types and tank inventory
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QSpinBox,
    QDoubleSpinBox, QLineEdit, QDialog, QFormLayout, QMessageBox,
    QHeaderView, QComboBox, QDateEdit, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor
from src.services.database_service import FuelService, TankService, DatabaseService
from src.models import FuelType, Tank
from src.utils.validators import validate_currency
from src.config.logger_config import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class FuelTypeDialog(QDialog):
    """Dialog for adding/editing fuel types."""

    def __init__(self, parent=None, fuel_type=None):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            fuel_type: Existing FuelType to edit (None for new)
        """
        super().__init__(parent)
        self.fuel_type = fuel_type
        self.setWindowTitle("Fuel Type" if fuel_type is None else f"Edit {fuel_type.name}")
        self.setGeometry(200, 200, 400, 300)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()

        # Fuel name
        self.name_input = QLineEdit()
        if self.fuel_type:
            self.name_input.setText(self.fuel_type.name)
        layout.addRow("Fuel Name:", self.name_input)

        # Current rate
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0, 10000)
        self.rate_input.setDecimals(2)
        self.rate_input.setSuffix(" Rs/L")
        if self.fuel_type:
            self.rate_input.setValue(float(self.fuel_type.current_rate))
        layout.addRow("Current Rate:", self.rate_input)

        # Tax percentage
        self.tax_input = QDoubleSpinBox()
        self.tax_input.setRange(0, 100)
        self.tax_input.setDecimals(2)
        self.tax_input.setSuffix(" %")
        if self.fuel_type:
            self.tax_input.setValue(float(self.fuel_type.tax_percentage))
        else:
            self.tax_input.setValue(5.0)
        layout.addRow("Tax (%):", self.tax_input)

        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        if self.fuel_type and self.fuel_type.description:
            self.description_input.setPlainText(self.fuel_type.description)
        layout.addRow("Description:", self.description_input)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def get_fuel_type(self) -> FuelType:
        """
        Get the fuel type from the dialog.

        Returns:
            FuelType object
        """
        return FuelType(
            id=self.fuel_type.id if self.fuel_type else None,
            name=self.name_input.text(),
            current_rate=str(self.rate_input.value()),
            tax_percentage=str(self.tax_input.value()),
            description=self.description_input.toPlainText(),
            created_at=self.fuel_type.created_at if self.fuel_type else datetime.now().isoformat(),
            created_by=self.fuel_type.created_by if self.fuel_type else ""
        )


class TankDialog(QDialog):
    """Dialog for adding/editing tank information."""

    def __init__(self, parent=None, tank=None, fuel_types=None):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            tank: Existing Tank to edit (None for new)
            fuel_types: List of available FuelType objects
        """
        super().__init__(parent)
        self.tank = tank
        self.fuel_types = fuel_types or []
        self.setWindowTitle("Tank" if tank is None else f"Edit {tank.tank_id}")
        self.setGeometry(200, 200, 450, 400)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QFormLayout()

        # Tank ID
        self.tank_id_input = QLineEdit()
        self.tank_id_input.setReadOnly(self.tank is not None)
        if self.tank:
            self.tank_id_input.setText(self.tank.tank_id)
        layout.addRow("Tank ID:", self.tank_id_input)

        # Fuel type
        self.fuel_type_combo = QComboBox()
        for fuel in self.fuel_types:
            self.fuel_type_combo.addItem(fuel.name, fuel.id)
        if self.tank:
            index = self.fuel_type_combo.findData(self.tank.fuel_type_id)
            self.fuel_type_combo.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Fuel Type:", self.fuel_type_combo)

        # Capacity
        self.capacity_input = QDoubleSpinBox()
        self.capacity_input.setRange(0, 1000000)
        self.capacity_input.setDecimals(2)
        self.capacity_input.setSuffix(" L")
        if self.tank:
            self.capacity_input.setValue(float(self.tank.capacity))
        layout.addRow("Capacity (Liters):", self.capacity_input)

        # Current stock
        self.stock_input = QDoubleSpinBox()
        self.stock_input.setRange(0, 1000000)
        self.stock_input.setDecimals(2)
        self.stock_input.setSuffix(" L")
        if self.tank:
            self.stock_input.setValue(float(self.tank.current_stock))
        layout.addRow("Current Stock:", self.stock_input)

        # Minimum level
        self.min_level_input = QDoubleSpinBox()
        self.min_level_input.setRange(0, 1000000)
        self.min_level_input.setDecimals(2)
        self.min_level_input.setSuffix(" L")
        if self.tank:
            self.min_level_input.setValue(float(self.tank.minimum_level))
        layout.addRow("Minimum Level:", self.min_level_input)

        # Location
        self.location_input = QLineEdit()
        if self.tank and self.tank.location:
            self.location_input.setText(self.tank.location)
        layout.addRow("Location:", self.location_input)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def get_tank(self) -> Tank:
        """
        Get the tank from the dialog.

        Returns:
            Tank object
        """
        return Tank(
            id=self.tank.id if self.tank else None,
            tank_id=self.tank_id_input.text(),
            fuel_type_id=self.fuel_type_combo.currentData(),
            capacity=str(self.capacity_input.value()),
            current_stock=str(self.stock_input.value()),
            minimum_level=str(self.min_level_input.value()),
            location=self.location_input.text() or None,
            created_at=self.tank.created_at if self.tank else datetime.now().isoformat(),
            created_by=self.tank.created_by if self.tank else ""
        )


class FuelManagementScreen(QWidget):
    """Fuel management screen for managing fuel types and tank inventory."""

    def __init__(self, user):
        """Initialize fuel management screen."""
        super().__init__()
        self.user = user
        self.fuel_service = FuelService()
        self.tank_service = TankService()
        self.db_service = DatabaseService()

        self.setWindowTitle("Fuel Management")
        self.setGeometry(100, 100, 1200, 700)

        self.fuel_types = []
        self.tanks = []

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout()

        # Header
        header = QLabel("Fuel Management")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(header)

        # Tab widget
        tabs = QTabWidget()

        # Fuel Types tab
        fuel_tab = QWidget()
        fuel_layout = QVBoxLayout()

        # Fuel types table
        self.fuel_table = QTableWidget()
        self.fuel_table.setColumnCount(5)
        self.fuel_table.setHorizontalHeaderLabels([
            "Fuel Name", "Current Rate (Rs/L)", "Tax (%)", "Description", "Actions"
        ])
        self.fuel_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        fuel_layout.addWidget(self.fuel_table)

        # Buttons for fuel types
        fuel_btn_layout = QHBoxLayout()
        add_fuel_btn = QPushButton("Add Fuel Type")
        add_fuel_btn.clicked.connect(self.add_fuel_type)
        fuel_btn_layout.addWidget(add_fuel_btn)
        fuel_btn_layout.addStretch()
        fuel_layout.addLayout(fuel_btn_layout)

        fuel_tab.setLayout(fuel_layout)
        tabs.addTab(fuel_tab, "Fuel Types")

        # Tanks tab
        tank_tab = QWidget()
        tank_layout = QVBoxLayout()

        # Tanks table
        self.tank_table = QTableWidget()
        self.tank_table.setColumnCount(7)
        self.tank_table.setHorizontalHeaderLabels([
            "Tank ID", "Fuel Type", "Capacity (L)", "Current Stock (L)",
            "Minimum Level (L)", "Status", "Actions"
        ])
        self.tank_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tank_layout.addWidget(self.tank_table)

        # Buttons for tanks
        tank_btn_layout = QHBoxLayout()
        add_tank_btn = QPushButton("Add Tank")
        add_tank_btn.clicked.connect(self.add_tank)
        tank_btn_layout.addWidget(add_tank_btn)
        tank_btn_layout.addStretch()
        tank_layout.addLayout(tank_btn_layout)

        tank_tab.setLayout(tank_layout)
        tabs.addTab(tank_tab, "Tank Inventory")

        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

    def load_data(self):
        """Load fuel types and tanks from database."""
        try:
            # Load fuel types
            self.fuel_types = self.fuel_service.get_all_fuel_types()
            self.populate_fuel_table()

            # Load tanks
            self.tanks = self.tank_service.get_all_tanks()
            self.populate_tank_table()

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def populate_fuel_table(self):
        """Populate fuel types table."""
        self.fuel_table.setRowCount(len(self.fuel_types))

        for row, fuel in enumerate(self.fuel_types):
            # Fuel name
            self.fuel_table.setItem(row, 0, QTableWidgetItem(fuel.name))

            # Current rate
            self.fuel_table.setItem(row, 1, QTableWidgetItem(f"Rs. {fuel.current_rate}"))

            # Tax
            self.fuel_table.setItem(row, 2, QTableWidgetItem(f"{fuel.tax_percentage}%"))

            # Description
            self.fuel_table.setItem(row, 3, QTableWidgetItem(
                fuel.description or "---"
            ))

            # Actions
            action_layout = QHBoxLayout()
            edit_btn = QPushButton("Edit")
            delete_btn = QPushButton("Delete")

            edit_btn.clicked.connect(
                lambda checked, f=fuel: self.edit_fuel_type(f)
            )
            delete_btn.clicked.connect(
                lambda checked, f=fuel: self.delete_fuel_type(f)
            )

            action_widget = QWidget()
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_widget.setLayout(action_layout)

            self.fuel_table.setCellWidget(row, 4, action_widget)

    def populate_tank_table(self):
        """Populate tanks table."""
        self.tank_table.setRowCount(len(self.tanks))

        for row, tank in enumerate(self.tanks):
            # Tank ID
            self.tank_table.setItem(row, 0, QTableWidgetItem(tank.tank_id))

            # Fuel type
            fuel_name = next(
                (f.name for f in self.fuel_types if f.id == tank.fuel_type_id),
                "Unknown"
            )
            self.tank_table.setItem(row, 1, QTableWidgetItem(fuel_name))

            # Capacity
            self.tank_table.setItem(row, 2, QTableWidgetItem(f"{tank.capacity} L"))

            # Current stock
            self.tank_table.setItem(row, 3, QTableWidgetItem(f"{tank.current_stock} L"))

            # Minimum level
            self.tank_table.setItem(row, 4, QTableWidgetItem(f"{tank.minimum_level} L"))

            # Status
            current = float(tank.current_stock)
            minimum = float(tank.minimum_level)
            if current < minimum:
                status_item = QTableWidgetItem("⚠ LOW STOCK")
                status_item.setForeground(QColor("red"))
            else:
                status_item = QTableWidgetItem("✓ OK")
                status_item.setForeground(QColor("green"))
            self.tank_table.setItem(row, 5, status_item)

            # Actions
            action_layout = QHBoxLayout()
            edit_btn = QPushButton("Edit")
            delete_btn = QPushButton("Delete")

            edit_btn.clicked.connect(
                lambda checked, t=tank: self.edit_tank(t)
            )
            delete_btn.clicked.connect(
                lambda checked, t=tank: self.delete_tank(t)
            )

            action_widget = QWidget()
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_widget.setLayout(action_layout)

            self.tank_table.setCellWidget(row, 6, action_widget)

    def add_fuel_type(self):
        """Add a new fuel type."""
        dialog = FuelTypeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                fuel = dialog.get_fuel_type()
                success, message = self.fuel_service.add_fuel_type(fuel)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error adding fuel type: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to add fuel type: {str(e)}")

    def edit_fuel_type(self, fuel):
        """Edit an existing fuel type."""
        dialog = FuelTypeDialog(self, fuel)
        if dialog.exec_() == QDialog.Accepted:
            try:
                updated_fuel = dialog.get_fuel_type()
                success, message = self.fuel_service.update_fuel_type(
                    fuel.id, updated_fuel
                )

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error updating fuel type: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to update fuel type: {str(e)}")

    def delete_fuel_type(self, fuel):
        """Delete a fuel type."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{fuel.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success, message = self.fuel_service.delete_fuel_type(fuel.id)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error deleting fuel type: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete fuel type: {str(e)}")

    def add_tank(self):
        """Add a new tank."""
        dialog = TankDialog(self, fuel_types=self.fuel_types)
        if dialog.exec_() == QDialog.Accepted:
            try:
                tank = dialog.get_tank()
                success, message = self.tank_service.add_tank(tank)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error adding tank: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to add tank: {str(e)}")

    def edit_tank(self, tank):
        """Edit an existing tank."""
        dialog = TankDialog(self, tank, self.fuel_types)
        if dialog.exec_() == QDialog.Accepted:
            try:
                updated_tank = dialog.get_tank()
                success, message = self.tank_service.update_tank(tank.id, updated_tank)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error updating tank: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to update tank: {str(e)}")

    def delete_tank(self, tank):
        """Delete a tank."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete tank '{tank.tank_id}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success, message = self.tank_service.delete_tank(tank.id)

                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Error", message)

            except Exception as e:
                logger.error(f"Error deleting tank: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete tank: {str(e)}")
