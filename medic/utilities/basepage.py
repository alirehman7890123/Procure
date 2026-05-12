from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import QSize

class BasePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Make all pages "neutral"
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(0, 0)

    def sizeHint(self):
        # Override to return a neutral size for all pages
        return QSize(200, 200)
