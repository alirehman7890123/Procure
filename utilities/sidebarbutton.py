from PySide6.QtWidgets import QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QSize
from utilities.app_theme import get_theme_palette

class SideBarButton(QPushButton):
    def __init__(self, text="", normal_color="#2F5D7C", hover_color="#3D6A89",
                 text_normal="#F3F8FC", text_hover="#FFFFFF", duration=250, parent=None):
        super().__init__(text, parent)

        self._full_text = text
        self._display_text = f"  {text}" if text else text
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_normal = text_normal
        self.text_hover = text_hover
        self.active_color = "#F8F6F1"
        self.active_text = "#17152A"
        self.active_indicator = "#F8F6F1"

        self._is_hovered = False
        self._is_active = False
        self._is_collapsed = False

        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(42)
        self.setFlat(True)
        self.setIconSize(QSize(18, 18))
        self.setAttribute(Qt.WA_Hover, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(self._display_text)
        self.refresh_theme()
        self._apply_style()

    def refresh_theme(self):
        palette = get_theme_palette()
        self.normal_color = palette["sidebar_bg"]
        self.hover_color = palette["sidebar_hover"]
        self.text_normal = palette["sidebar_text"]
        self.text_hover = "#FFFFFF"
        self.active_color = palette["sidebar_active"]
        self.active_text = palette["sidebar_active_text"]
        self.active_indicator = palette["sidebar_active"]
        self._apply_style()

    def enterEvent(self, event):
        self._is_hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def set_active(self, active: bool):
        self._is_active = bool(active)
        self._apply_style()

    def set_collapsed(self, collapsed: bool):
        self._is_collapsed = bool(collapsed)
        self.setFixedHeight(38 if self._is_collapsed else 42)
        if self._is_collapsed:
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.setFixedWidth(40)
            self.setText("")
            self.setToolTip(self._full_text)
        else:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
            self.setText(self._display_text)
            self.setToolTip("")
        self._apply_style()

    def _apply_style(self):
        if self._is_active:
            bg = self.active_color
            fg = self.active_text
            border = self.active_color
        elif self._is_hovered:
            bg = self.hover_color
            fg = "#FFFFFF"
            border = self.hover_color
        else:
            bg = "transparent"
            fg = self.text_normal
            border = "transparent"

        radius = "5px"

        text_align = "center" if self._is_collapsed else "left"
        left_pad = "0px" if self._is_collapsed else "18px"
        right_pad = "0px" if self._is_collapsed else "14px"
        min_width = "40px" if self._is_collapsed else "0px"
        margin = "4px" if self._is_collapsed else "3px 0px"
        padding = "0px" if self._is_collapsed else "0px"
        radius = "10px" if self._is_collapsed else "5px"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: {radius};
                padding: {padding};
                padding-left: {left_pad};
                padding-right: {right_pad};
                margin: {margin};
                text-align: {text_align};
                font-family: montserrat;
                font-size: 12px;
                font-weight: {'700' if self._is_active else '600'};
                min-width: {min_width};
            }}
        """)
