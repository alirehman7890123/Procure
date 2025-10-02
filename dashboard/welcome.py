from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PySide6.QtCore import Qt
import sys

class WelcomeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # main vertical layout
        layout = QVBoxLayout(self)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.label = QLabel("Welcome Back", self)
        self.label.setStyleSheet("color: #333;")


        # add label and hbox to main layout
        layout.addWidget(self.label)
        layout.addStretch()

        self.setLayout(layout)
        

