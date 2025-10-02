from PySide6.QtWidgets import QPushButton, QSizePolicy
from PySide6.QtCore import QPropertyAnimation, Property, QEasingCurve, Qt
from PySide6.QtGui import QColor, QPainter, QBrush, QFont

class SideBarButton(QPushButton):
    def __init__(self, text="", normal_color="#47034E", hover_color="#ffffff",
                 text_normal="white", text_hover="#47034E", duration=250, parent=None):
        super().__init__(text, parent)

        # background colors
        self._bg_color = QColor(normal_color)
        self.normal_color = QColor(normal_color)
        self.hover_color = QColor(hover_color)

        # text colors
        self._text_color = QColor(text_normal)
        self.text_normal = QColor(text_normal)
        self.text_hover = QColor(text_hover)

        # hover state
        self._is_hovered = False

        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFlat(True)
        self.setStyleSheet("margin:0; border:none; padding:8px; outline:none;")
        self.setAttribute(Qt.WA_Hover, True)
        self.setCursor(Qt.PointingHandCursor)

        # animation for background
        self.animation_bg = QPropertyAnimation(self, b"bg_color", self)
        self.animation_bg.setDuration(duration)
        self.animation_bg.setEasingCurve(QEasingCurve.InOutQuad)

        # fake "smooth bold" = scaling animation
        self._scale = 1.0
        self.animation_scale = QPropertyAnimation(self, b"scale", self)
        self.animation_scale.setDuration(duration)
        self.animation_scale.setEasingCurve(QEasingCurve.InOutQuad)

    def enterEvent(self, event):
        self._is_hovered = True
        self.animate_bg(self.hover_color)
        self._text_color = self.text_hover
        self.animate_scale(1.03)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self.animate_bg(self.normal_color)
        self._text_color = self.text_normal
        self.animate_scale(1.0)
        super().leaveEvent(event)

    def animate_bg(self, target_color: QColor):
        self.animation_bg.stop()
        self.animation_bg.setStartValue(self._bg_color)
        self.animation_bg.setEndValue(target_color)
        self.animation_bg.start()

    def animate_scale(self, target_scale: float):
        self.animation_scale.stop()
        self.animation_scale.setStartValue(self._scale)
        self.animation_scale.setEndValue(target_scale)
        self.animation_scale.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # draw background
        painter.setBrush(QBrush(self._bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

        # prepare font
        font = self.font()
        font.setWeight(QFont.Weight.Bold if self._is_hovered else QFont.Weight.Normal)
        painter.setFont(font)

        # apply scaling transform (fake bold animation effect)
        painter.save()
        rect = self.rect().adjusted(30, 0, -8, 0)
        painter.translate(rect.center())
        painter.scale(self._scale, self._scale)
        painter.translate(-rect.center())

        # draw text
        painter.setPen(QColor(self._text_color))
        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, self.text())
        painter.restore()

    # Background property
    def get_bg_color(self): return self._bg_color
    def set_bg_color(self, color):
        if isinstance(color, QColor):
            self._bg_color = color
            self.update()
    bg_color = Property(QColor, get_bg_color, set_bg_color)

    # Scale property (fake bold smoothness)
    def get_scale(self): return self._scale
    def set_scale(self, s):
        self._scale = float(s)
        self.update()
    scale = Property(float, get_scale, set_scale)
