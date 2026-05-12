# Modern Date Picker Widget - Usage Guide

## Overview

The `modern_date_picker.py` module provides two modern, professionally styled date picker components:

1. **`ModernDatePickerDialog`** - A standalone popup dialog with calendar
2. **`ModernDateEdit`** - An enhanced QDateEdit with styled embedded calendar

Both components feature:
- ✨ Modern, visually appealing design
- 🎨 Explicit color scheme matching ProCure theme
- ⌨️ Full keyboard navigation support
- 🖱️ Smooth hover and selection effects
- 📱 Responsive layout
- 🎯 Clear visual hierarchy

## Color Scheme

The date picker uses ProCure's established color palette:

| Element | Color | Hex Code |
|---------|-------|----------|
| Primary Dark | Dark Blue | #163B5C |
| Primary Main | Main Blue | #2F5D7C |
| Primary Light | Light Blue | #5A8FB5 |
| Primary Lighter | Lighter Blue | #8FBFE4 |
| Text Primary | Dark Text | #222222 |
| Text Secondary | Gray Text | #666666 |
| Background Primary | White | #FFFFFF |
| Background Secondary | Very Light Blue | #F9FCFE |
| Background Tertiary | Soft Blue | #EEF5FA |
| Border | Light Border | #D0DFE9 |
| Hover State | Light Hover | #EEF5FA |

## Component 1: ModernDatePickerDialog

A popup dialog that displays a full calendar with modern styling.

### Basic Usage

```python
from PySide6.QtWidgets import QDialog
from PySide6.QtCore import QDate
from utilities.modern_date_picker import ModernDatePickerDialog

# Create and show the dialog
picker = ModernDatePickerDialog()

if picker.exec() == QDialog.Accepted:
    selected_date = picker.get_selected_date()
    print(f"Selected date: {selected_date.toString('yyyy-MM-dd')}")
```

### With Initial Date

```python
from datetime import datetime

# Using datetime object
picker = ModernDatePickerDialog(initial_date=datetime.now())

# Using QDate
from PySide6.QtCore import QDate
picker = ModernDatePickerDialog(initial_date=QDate(2025, 1, 15))
```

### Connecting to Signals

```python
picker = ModernDatePickerDialog()
picker.date_selected.connect(on_date_selected)

def on_date_selected(date):
    print(f"Date selected: {date.toString('dddd, MMMM d, yyyy')}")

picker.exec()
```

### In a Button Click Handler

```python
from PySide6.QtWidgets import QPushButton, QLabel, QVBoxLayout, QWidget
from utilities.modern_date_picker import ModernDatePickerDialog

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.date_label = QLabel("No date selected")
        btn = QPushButton("Select Date")
        btn.clicked.connect(self.open_date_picker)
        
        layout.addWidget(btn)
        layout.addWidget(self.date_label)
        self.setLayout(layout)
    
    def open_date_picker(self):
        picker = ModernDatePickerDialog(parent=self)
        if picker.exec():
            date = picker.get_selected_date()
            self.date_label.setText(f"Selected: {date.toString('yyyy-MM-dd')}")
```

## Component 2: ModernDateEdit

An enhanced QDateEdit widget with a styled popup calendar.

### Basic Usage

```python
from PySide6.QtWidgets import QVBoxLayout, QWidget
from utilities.modern_date_picker import ModernDateEdit

class MyForm(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        date_edit = ModernDateEdit()
        layout.addWidget(date_edit)
        
        self.setLayout(layout)
```

### Getting the Selected Date

```python
date_edit = ModernDateEdit()

# Get QDate
selected_date = date_edit.date()

# Convert to string
date_str = selected_date.toString('yyyy-MM-dd')

# Convert to datetime
from datetime import datetime
dt = datetime(selected_date.year(), selected_date.month(), selected_date.day())
```

## Advanced Usage Examples

### Transaction Form Integration

```python
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout
from PySide6.QtCore import QDate
from utilities.modern_date_picker import ModernDatePickerDialog, ModernDateEdit

class TransactionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Transaction")
        
        layout = QFormLayout()
        
        # Transaction date
        self.date_edit = ModernDateEdit()
        layout.addRow("Transaction Date:", self.date_edit)
        
        # Description
        self.desc_edit = QLineEdit()
        layout.addRow("Description:", self.desc_edit)
        
        # Amount
        self.amount_edit = QLineEdit()
        layout.addRow("Amount:", self.amount_edit)
        
        # Buttons
        btn_layout = QVBoxLayout()
        submit_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        submit_btn.clicked.connect(self.save_transaction)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(submit_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        self.setLayout(layout)
    
    def save_transaction(self):
        date = self.date_edit.date()
        description = self.desc_edit.text()
        amount = self.amount_edit.text()
        
        # Save logic here
        print(f"Saved: {date}, {description}, {amount}")
        self.accept()
```

### Date Range Selection

```python
from utilities.modern_date_picker import ModernDatePickerDialog
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class DateRangeSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        self.start_date_label = QLabel("Start: None")
        self.end_date_label = QLabel("End: None")
        
        start_btn = QPushButton("Select Start Date")
        end_btn = QPushButton("Select End Date")
        
        start_btn.clicked.connect(self.select_start_date)
        end_btn.clicked.connect(self.select_end_date)
        
        layout.addWidget(self.start_date_label)
        layout.addWidget(start_btn)
        layout.addWidget(self.end_date_label)
        layout.addWidget(end_btn)
        
        self.setLayout(layout)
    
    def select_start_date(self):
        picker = ModernDatePickerDialog(parent=self)
        if picker.exec() == QDialog.Accepted:
            date = picker.get_selected_date()
            self.start_date_label.setText(f"Start: {date.toString('yyyy-MM-dd')}")
    
    def select_end_date(self):
        picker = ModernDatePickerDialog(parent=self)
        if picker.exec() == QDialog.Accepted:
            date = picker.get_selected_date()
            self.end_date_label.setText(f"End: {date.toString('yyyy-MM-dd')}")
```

## Styling Details

### Dialog Dimensions
- **Width**: 450px
- **Height**: 520px
- **Border Radius**: 10px
- **Margins**: 20px

### Calendar Grid
- **Grid Visible**: Yes
- **First Day**: Monday
- **Border Radius**: 8px

### Day Selection
- **Normal Hover**: Light blue (#EEF5FA) background with light border
- **Selected**: Primary blue (#2F5D7C) background with white text
- **Disabled**: Gray text (#d0d0d0)

### Navigation Buttons
- **Normal**: Primary main blue (#2F5D7C) with white text
- **Hover**: Light blue (#5A8FB5)
- **Pressed**: Dark blue (#163B5C)

### Action Buttons
- **Cancel**: Light tertiary background (#EEF5FA) with border
- **Confirm**: Primary main blue (#2F5D7C) with white text, bold font

## Running the Demo

To see the date picker in action:

```bash
python -m utilities.modern_date_picker
```

This will open a demo window showing:
- Modern Date Picker Dialog button
- Date display label
- Embedded ModernDateEdit widget

## Integration with Existing Forms

### Purchase Form Example

```python
from utilities.modern_date_picker import ModernDateEdit

class AddPurchaseForm(QWidget):
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout()
        
        # Existing fields...
        
        # Add date picker
        date_label = QLabel("Purchase Date:")
        self.purchase_date = ModernDateEdit()
        layout.addWidget(date_label)
        layout.addWidget(self.purchase_date)
        
        # More fields...
        
        self.setLayout(layout)
    
    def get_purchase_date(self):
        """Get the selected purchase date."""
        return self.purchase_date.date()
```

### Reports Date Range Example

```python
from utilities.modern_date_picker import ModernDatePickerDialog

class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        
        self.start_date = None
        self.end_date = None
        
        layout = QVBoxLayout()
        
        # Date range section
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("From:"))
        self.start_btn = QPushButton("Select Start")
        self.start_btn.clicked.connect(self.select_start_date)
        range_layout.addWidget(self.start_btn)
        
        range_layout.addWidget(QLabel("To:"))
        self.end_btn = QPushButton("Select End")
        self.end_btn.clicked.connect(self.select_end_date)
        range_layout.addWidget(self.end_btn)
        
        layout.addLayout(range_layout)
        
        # Generate button
        gen_btn = QPushButton("Generate Report")
        gen_btn.clicked.connect(self.generate_report)
        layout.addWidget(gen_btn)
        
        self.setLayout(layout)
    
    def select_start_date(self):
        picker = ModernDatePickerDialog(parent=self)
        if picker.exec():
            self.start_date = picker.get_selected_date()
            self.start_btn.setText(f"From: {self.start_date.toString('yyyy-MM-dd')}")
    
    def select_end_date(self):
        picker = ModernDatePickerDialog(parent=self)
        if picker.exec():
            self.end_date = picker.get_selected_date()
            self.end_btn.setText(f"To: {self.end_date.toString('yyyy-MM-dd')}")
    
    def generate_report(self):
        if self.start_date and self.end_date:
            print(f"Report from {self.start_date} to {self.end_date}")
```

## Customization

### Changing Colors

To customize the color scheme, modify the `COLORS` dictionary in `ModernDatePickerDialog`:

```python
from utilities.modern_date_picker import ModernDatePickerDialog

class CustomDatePickerDialog(ModernDatePickerDialog):
    COLORS = {
        **ModernDatePickerDialog.COLORS,
        "primary_main": "#FF6B35",  # Your custom color
        "primary_dark": "#C73E1D",
    }
```

### Modifying Dimensions

```python
class LargerDatePicker(ModernDatePickerDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(600, 650)  # Custom size
```

## Notes

- All components use **PySide6** (Qt for Python)
- Font family used: **Montserrat** (ensure it's available on your system)
- The date picker is **fully keyboard accessible**
- All colors are explicitly defined for consistency
- The dialog is **modal** by default
- The dialog has **no window frame** (frameless) for a modern look

## API Reference

### ModernDatePickerDialog

**Methods:**
- `__init__(initial_date=None, parent=None)` - Initialize dialog
- `get_selected_date()` -> QDate - Get currently selected date
- `exec()` -> int - Show dialog and return result

**Signals:**
- `date_selected(QDate)` - Emitted when date is confirmed

### ModernDateEdit

**Methods:**
- `__init__(parent=None)` - Initialize widget
- `date()` -> QDate - Get currently selected date
- `setDate(QDate)` - Set date programmatically

**Inherits from QDateEdit**, so all standard QDateEdit methods are available.

## Support

For issues or customizations, refer to PySide6 documentation:
- QCalendarWidget: https://doc.qt.io/qtforpython/PySide6/QtWidgets/QCalendarWidget.html
- QDateEdit: https://doc.qt.io/qtforpython/PySide6/QtWidgets/QDateEdit.html
- Stylesheets: https://doc.qt.io/qtforpython/overviews/stylesheet.html
