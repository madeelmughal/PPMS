"""
UI Widgets - Reusable PyQt5 widgets
"""

from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QComboBox,
    QDateEdit, QSpinBox, QDoubleSpinBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QDialog, QVBoxLayout,
    QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont


class SearchableTable(QTableWidget):
    """Searchable table widget."""

    def __init__(self, columns: list):
        """Initialize table."""
        super().__init__()
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)

    def add_row(self, data: list):
        """Add row to table."""
        row_position = self.rowCount()
        self.insertRow(row_position)

        for column, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row_position, column, item)

    def clear_table(self):
        """Clear all rows."""
        self.setRowCount(0)

    def get_selected_row(self) -> dict:
        """Get selected row data."""
        selected_items = self.selectedItems()
        if not selected_items:
            return {}

        row = selected_items[0].row()
        data = {}
        for col in range(self.columnCount()):
            header = self.horizontalHeaderItem(col).text()
            value = self.item(row, col).text()
            data[header] = value

        return data


class InputDialog(QDialog):
    """Generic input dialog."""

    def __init__(self, title: str, fields: dict, parent=None):
        """
        Initialize dialog.

        Args:
            title: Dialog title
            fields: Dict of {field_name: field_type}
                   field_type can be 'text', 'number', 'decimal', 'date', 'combo'
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.fields = fields
        self.inputs = {}

        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        for field_name, field_type in self.fields.items():
            label = QLabel(field_name + ":")
            layout.addWidget(label)

            if field_type == 'text':
                widget = QLineEdit()
            elif field_type == 'number':
                widget = QSpinBox()
            elif field_type == 'decimal':
                widget = QDoubleSpinBox()
                widget.setDecimals(2)
            elif field_type == 'date':
                widget = QDateEdit()
                widget.setDate(QDate.currentDate())
            elif field_type == 'combo':
                widget = QComboBox()
            else:
                widget = QLineEdit()

            layout.addWidget(widget)
            self.inputs[field_name] = widget

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_data(self) -> dict:
        """Get input data."""
        data = {}
        for field_name, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                data[field_name] = widget.text()
            elif isinstance(widget, QSpinBox):
                data[field_name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                data[field_name] = widget.value()
            elif isinstance(widget, QDateEdit):
                data[field_name] = widget.date().toPython()
            elif isinstance(widget, QComboBox):
                data[field_name] = widget.currentText()

        return data

    def set_combo_options(self, field_name: str, options: list):
        """Set combo box options."""
        if field_name in self.inputs:
            widget = self.inputs[field_name]
            if isinstance(widget, QComboBox):
                widget.addItems([str(opt) for opt in options])


__all__ = ['SearchableTable', 'InputDialog']
