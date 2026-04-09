"""
Quick Reference - Modern Date Picker Integration Examples
Copy-paste these snippets into your code.
"""

# ============================================================================
# EXAMPLE 1: Simple Button to Open Date Picker Dialog
# ============================================================================

from PySide6.QtWidgets import QPushButton, QLabel, QVBoxLayout, QWidget, QDialog
from PySide6.QtCore import Qt
from utilities.modern_date_picker import ModernDatePickerDialog


class SimplePickerExample(QWidget):
    """Example: Button that opens date picker, displays selected date."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Display label
        self.result_label = QLabel("Click button to select a date")
        
        # Button
        pick_btn = QPushButton("📅 Pick Date")
        pick_btn.clicked.connect(self.open_picker)
        pick_btn.setFixedHeight(40)
        
        layout.addWidget(pick_btn)
        layout.addWidget(self.result_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setWindowTitle("Simple Date Picker")
    
    def open_picker(self):
        """Open the modern date picker dialog."""
        dialog = ModernDatePickerDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            date = dialog.get_selected_date()
            self.result_label.setText(f"You selected: {date.toString('dddd, MMMM d, yyyy')}")


# ============================================================================
# EXAMPLE 2: Use in a Form (Purchase Order)
# ============================================================================

from PySide6.QtWidgets import QFormLayout, QLineEdit
from utilities.modern_date_picker import ModernDateEdit


class PurchaseOrderForm(QWidget):
    """Example: Purchase form using ModernDateEdit."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Purchase Date
        self.date_edit = ModernDateEdit()
        layout.addRow("Purchase Date:", self.date_edit)
        
        # Supplier
        self.supplier_edit = QLineEdit()
        layout.addRow("Supplier:", self.supplier_edit)
        
        # Amount
        self.amount_edit = QLineEdit()
        layout.addRow("Amount:", self.amount_edit)
        
        self.setLayout(layout)
        self.setWindowTitle("New Purchase Order")
    
    def get_form_data(self):
        """Get all form data."""
        return {
            'date': self.date_edit.date(),
            'supplier': self.supplier_edit.text(),
            'amount': self.amount_edit.text(),
        }


# ============================================================================
# EXAMPLE 3: Date Range Picker (From / To)
# ============================================================================

class DateRangePickerExample(QWidget):
    """Example: Select date range for reports."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # From date section
        from_layout = QHBoxLayout()
        self.from_label = QLabel("Start Date: Not selected")
        from_btn = QPushButton("📅 Select Start")
        from_btn.clicked.connect(self.pick_start_date)
        from_layout.addWidget(from_btn)
        from_layout.addWidget(self.from_label)
        from_layout.addStretch()
        
        # To date section
        to_layout = QHBoxLayout()
        self.to_label = QLabel("End Date: Not selected")
        to_btn = QPushButton("📅 Select End")
        to_btn.clicked.connect(self.pick_end_date)
        to_layout.addWidget(to_btn)
        to_layout.addWidget(self.to_label)
        to_layout.addStretch()
        
        # Generate button
        gen_btn = QPushButton("Generate Report")
        gen_btn.setFixedHeight(40)
        gen_btn.clicked.connect(self.generate_report)
        
        layout.addLayout(from_layout)
        layout.addLayout(to_layout)
        layout.addWidget(gen_btn)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setWindowTitle("Date Range Selector")
    
    def pick_start_date(self):
        dialog = ModernDatePickerDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.start_date = dialog.get_selected_date()
            self.from_label.setText(f"Start: {self.start_date.toString('yyyy-MM-dd')}")
    
    def pick_end_date(self):
        dialog = ModernDatePickerDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.end_date = dialog.get_selected_date()
            self.to_label.setText(f"End: {self.end_date.toString('yyyy-MM-dd')}")
    
    def generate_report(self):
        if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
            print(f"Report from {self.start_date} to {self.end_date}")


# ============================================================================
# EXAMPLE 4: Date Picker in a Dialog Form
# ============================================================================

class TransactionDialog(QDialog):
    """Example: Transaction entry dialog with date picker."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Transaction")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Date picker
        self.date_edit = ModernDateEdit()
        layout.addRow("Transaction Date:", self.date_edit)
        
        # Description
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Enter description...")
        layout.addRow("Description:", self.desc_edit)
        
        # Category
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Enter category...")
        layout.addRow("Category:", self.category_edit)
        
        # Amount
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("Enter amount...")
        layout.addRow("Amount:", self.amount_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save)
        save_btn.setFixedHeight(40)
        
        cancel_btn = QPushButton("✕ Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setFixedHeight(40)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
        self.setFixedWidth(400)
    
    def save(self):
        data = {
            'date': self.date_edit.date(),
            'description': self.desc_edit.text(),
            'category': self.category_edit.text(),
            'amount': self.amount_edit.text(),
        }
        print(f"Saving transaction: {data}")
        self.accept()


# ============================================================================
# EXAMPLE 5: Multiple Date Pickers (Birth Dates, etc.)
# ============================================================================

class MultiDatePickerExample(QWidget):
    """Example: Multiple date pickers for birthdate, expiry, etc."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Birth date
        self.birth_date = ModernDateEdit()
        layout.addRow("Birth Date:", self.birth_date)
        
        # Expiry date
        self.expiry_date = ModernDateEdit()
        layout.addRow("Expiry Date:", self.expiry_date)
        
        # License renewal date
        self.renewal_date = ModernDateEdit()
        layout.addRow("License Renewal:", self.renewal_date)
        
        # Submit button
        submit_btn = QPushButton("✓ Submit")
        submit_btn.clicked.connect(self.submit)
        submit_btn.setFixedHeight(40)
        
        layout.addRow(submit_btn)
        
        self.setLayout(layout)
        self.setWindowTitle("Multiple Date Fields")
    
    def submit(self):
        print(f"Birth: {self.birth_date.date()}")
        print(f"Expiry: {self.expiry_date.date()}")
        print(f"Renewal: {self.renewal_date.date()}")


# ============================================================================
# EXAMPLE 6: Dialog for Existing Code Integration
# ============================================================================

def show_date_picker_in_existing_code():
    """
    Simple function to integrate into existing code.
    Just call this function whenever you need a date selection.
    """
    dialog = ModernDatePickerDialog()
    if dialog.exec() == QDialog.Accepted:
        selected_date = dialog.get_selected_date()
        # Use selected_date here
        print(f"Selected: {selected_date.toString('yyyy-MM-dd')}")
        return selected_date
    return None


# ============================================================================
# EXAMPLE 7: Initialize and Use in Event Handler
# ============================================================================

def on_edit_button_clicked():
    """Example: Use in an existing button click handler."""
    picker = ModernDatePickerDialog()
    
    if picker.exec() == QDialog.Accepted:
        date = picker.get_selected_date()
        
        # Convert to string for database
        date_str = date.toString('yyyy-MM-dd')
        
        # Convert to Python datetime for more operations
        from datetime import datetime
        py_date = datetime(date.year(), date.month(), date.day())
        
        # Use the date
        print(f"String: {date_str}")
        print(f"Python datetime: {py_date}")
        
        # Save to database, update UI, etc.
        # ... your code here ...


# ============================================================================
# DEMO: Run all examples
# ============================================================================

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
    
    app = QApplication([])
    
    # Create tab widget to show all examples
    main_window = QMainWindow()
    main_window.setWindowTitle("Modern Date Picker - Examples")
    main_window.setGeometry(100, 100, 800, 600)
    
    tabs = QTabWidget()
    
    # Add each example as a tab
    tabs.addTab(SimplePickerExample(), "Simple Picker")
    tabs.addTab(PurchaseOrderForm(), "Purchase Form")
    tabs.addTab(DateRangePickerExample(), "Date Range")
    tabs.addTab(MultiDatePickerExample(), "Multiple Dates")
    
    main_window.setCentralWidget(tabs)
    main_window.show()
    
    app.exec()
