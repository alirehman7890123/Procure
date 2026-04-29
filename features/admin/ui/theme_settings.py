from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.app_theme import DEFAULT_THEME, apply_app_theme, normalize_hex
from medic.utilities.permissions import Permissions
from medic.utilities.stylus import load_stylesheets
from services.accounting_settings_service import (
    load_theme_settings as load_theme_settings_from_service,
    save_theme_settings as save_theme_settings_to_service,
)


class ThemeSettingsWidget(QWidget):
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.primary_color = DEFAULT_THEME["theme_primary_color"]
        self.sidebar_color = DEFAULT_THEME["theme_sidebar_color"]

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Theme Settings", objectName="SectionTitle")
        self.back_btn = QPushButton("Back", objectName="TopRightButton")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.back_btn)
        self.layout.addLayout(header_layout)

        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        self.layout.addWidget(line)

        description = QLabel(
            "Choose a primary accent color for buttons/actions and a sidebar color for navigation. Changes apply immediately across the app."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #555; padding-left: 0;")
        self.layout.addWidget(description)

        form_card = QFrame()
        form_card.setObjectName("sectionCard")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        self.primary_preview = QLabel()
        self.primary_preview.setFixedHeight(34)
        self.sidebar_preview = QLabel()
        self.sidebar_preview.setFixedHeight(34)

        self.primary_pick_btn = QPushButton("Choose Primary", objectName="TopRightButton")
        self.primary_pick_btn.setCursor(Qt.PointingHandCursor)
        self.primary_pick_btn.clicked.connect(lambda: self.pick_color("primary"))

        self.sidebar_pick_btn = QPushButton("Choose Sidebar", objectName="TopRightButton")
        self.sidebar_pick_btn.setCursor(Qt.PointingHandCursor)
        self.sidebar_pick_btn.clicked.connect(lambda: self.pick_color("sidebar"))

        grid.addWidget(QLabel("Primary Accent"), 0, 0)
        grid.addWidget(self.primary_preview, 0, 1)
        grid.addWidget(self.primary_pick_btn, 0, 2)
        grid.addWidget(QLabel("Sidebar Color"), 1, 0)
        grid.addWidget(self.sidebar_preview, 1, 1)
        grid.addWidget(self.sidebar_pick_btn, 1, 2)
        grid.setColumnStretch(1, 1)

        form_layout.addLayout(grid)

        self.status_label = QLabel("Accent buttons and sidebar navigation will use these colors.")
        self.status_label.setStyleSheet("font-size: 11px; color: #666; padding-left: 0;")
        form_layout.addWidget(self.status_label)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.reset_btn = QPushButton("Reset Defaults", objectName="CancelButton")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset_defaults)

        self.save_btn = QPushButton("Save Theme", objectName="SaveButton")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_theme)

        button_row.addWidget(self.reset_btn)
        button_row.addWidget(self.save_btn)
        form_layout.addLayout(button_row)

        self.layout.addWidget(form_card)
        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())
        self.load_theme_settings()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_theme_settings()

    def _apply_preview(self, label, color_value):
        text_color = "#FFFFFF" if QColor(color_value).lightness() < 140 else "#1F2A33"
        label.setText(color_value)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            f"background-color: {color_value}; color: {text_color}; border: 1px solid #C7D4DE; border-radius: 6px; font-weight: 700;"
        )

    def load_theme_settings(self):
        settings = load_theme_settings_from_service()
        self.primary_color = normalize_hex(settings["theme_primary_color"], DEFAULT_THEME["theme_primary_color"])
        self.sidebar_color = normalize_hex(settings["theme_sidebar_color"], DEFAULT_THEME["theme_sidebar_color"])
        self._apply_preview(self.primary_preview, self.primary_color)
        self._apply_preview(self.sidebar_preview, self.sidebar_color)

    def pick_color(self, target):
        current = self.primary_color if target == "primary" else self.sidebar_color
        color = QColorDialog.getColor(QColor(current), self, "Choose Color")
        if not color.isValid():
            return
        if target == "primary":
            self.primary_color = color.name().upper()
            self._apply_preview(self.primary_preview, self.primary_color)
        else:
            self.sidebar_color = color.name().upper()
            self._apply_preview(self.sidebar_preview, self.sidebar_color)

    def reset_defaults(self):
        self.primary_color = DEFAULT_THEME["theme_primary_color"]
        self.sidebar_color = DEFAULT_THEME["theme_sidebar_color"]
        self._apply_preview(self.primary_preview, self.primary_color)
        self._apply_preview(self.sidebar_preview, self.sidebar_color)

    @Permissions.require_permission("business.update")
    def save_theme(self):
        try:
            save_theme_settings_to_service(
                primary_color=self.primary_color,
                sidebar_color=self.sidebar_color,
            )
        except Exception as exc:
            AppMessageBox.error(self, "Save Failed", str(exc))
            return

        apply_app_theme()
        AppMessageBox.success(self, "Saved", "Theme updated successfully.")
