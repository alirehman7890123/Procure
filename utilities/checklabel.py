
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QMouseEvent


class CheckableLabel(QLabel):

    def __init__(self, text, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.setTextColor("black")  # Initial color for unchecked state
        self.setStyleSheet("border: 1px solid black; padding: 5px;")  # Optional styling

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.toggle()
            event.accept()

    def toggle(self):
        
        self.is_checked = not getattr(self, 'is_checked', False)
        if self.is_checked:
            self.setTextColor("green")  # Change color for checked state
            self.setText("Checked")     # Update text or other visual cues
        else:
            self.setTextColor("black")  # Change color for unchecked state
            self.setText("Unchecked")   # Update text or other visual cues

    def setTextColor(self, color):
        # Set text color
        self.setStyleSheet(f"color: {color}; border: 1px solid black; padding: 5px;")
