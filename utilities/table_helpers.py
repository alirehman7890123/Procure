from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton


def centered_cell_widget(widget: QWidget) -> QWidget:
    wrapper = QWidget()
    layout = QHBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addStretch()
    layout.addWidget(widget, 0, Qt.AlignCenter)
    layout.addStretch()
    return wrapper


def style_table_action_button(button: QPushButton) -> QPushButton:
    button.setObjectName("TableActionButton")
    button.setMinimumWidth(60)
    button.setMaximumWidth(68)
    button.setMinimumHeight(24)
    button.setMaximumHeight(24)
    return button
