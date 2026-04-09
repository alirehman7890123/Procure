from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from utilities.stylus import load_stylesheets


_installed = False
_original_exec = None
_original_information = None
_original_warning = None
_original_critical = None
_original_question = None


_KIND_ACCENTS = {
    "info": {
        "border": "#2F5D7C",
        "button": "#2F5D7C",
        "hover": "#244A62",
        "pressed": "#163B5C",
    },
    "success": {
        "border": "#2E7D5A",
        "button": "#2E7D5A",
        "hover": "#25684B",
        "pressed": "#1D533B",
    },
    "warning": {
        "border": "#B7791F",
        "button": "#9A670F",
        "hover": "#84570B",
        "pressed": "#6C4708",
    },
    "error": {
        "border": "#B74A4A",
        "button": "#A33A3A",
        "hover": "#8A3131",
        "pressed": "#702727",
    },
    "question": {
        "border": "#4C6B86",
        "button": "#4C6B86",
        "hover": "#3F5A71",
        "pressed": "#344B5E",
    },
}


def _resolve_parent(parent=None):
    if parent is not None:
        return parent

    app = QApplication.instance()
    if app is None:
        return None

    active = app.activeWindow()
    if active is not None:
        return active

    top_levels = app.topLevelWidgets()
    for widget in top_levels:
        if widget.isVisible():
            return widget
    return None


def _center_box(box, parent=None):
    target_parent = _resolve_parent(parent) or box.parentWidget()
    box.adjustSize()
    geo = box.frameGeometry()

    if target_parent is not None and target_parent.isVisible():
        center_point = target_parent.frameGeometry().center()
    else:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        center_point = screen.availableGeometry().center()

    geo.moveCenter(center_point)
    box.move(geo.topLeft())


def _kind_stylesheet(kind):
    palette = _KIND_ACCENTS.get(kind, _KIND_ACCENTS["info"])
    return f"""
    QMessageBox {{
        border-top: 4px solid {palette['border']};
    }}
    QMessageBox QPushButton {{
        background-color: {palette['button']};
        border-color: {palette['button']};
    }}
    QMessageBox QPushButton:hover {{
        background-color: {palette['hover']};
        border-color: {palette['hover']};
    }}
    QMessageBox QPushButton:pressed {{
        background-color: {palette['pressed']};
        border-color: {palette['pressed']};
    }}
    """


def _prepare_box(box, parent=None, kind="info"):
    resolved_parent = _resolve_parent(parent)
    if resolved_parent is not None and box.parentWidget() is None:
        box.setParent(resolved_parent)

    box.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
    box.setMinimumWidth(420)
    box.setTextInteractionFlags(Qt.TextSelectableByMouse)
    box.setStyleSheet(load_stylesheets() + "\n" + _kind_stylesheet(kind))
    box.setProperty("messageKind", kind)

    for button in box.findChildren(QPushButton):
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumWidth(96)

    QTimer.singleShot(0, lambda: _center_box(box, resolved_parent))
    return box


def _show_message(icon, parent, title, text, buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton, kind="info"):
    box = QMessageBox(icon, title, text, QMessageBox.StandardButton(buttons), _resolve_parent(parent))
    box.setStandardButtons(QMessageBox.StandardButton(buttons))

    if default_button != QMessageBox.NoButton:
        box.setDefaultButton(QMessageBox.StandardButton(default_button))

    _prepare_box(box, parent, kind=kind)
    return box.exec()


class AppMessageBox:
    @staticmethod
    def information(parent, title, text, buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton):
        return AppMessageBox.info(parent, title, text, buttons, default_button)

    @staticmethod
    def info(parent, title, text, buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton):
        return _show_message(QMessageBox.Information, parent, title, text, buttons, default_button, kind="info")

    @staticmethod
    def critical(parent, title, text, buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton):
        return AppMessageBox.error(parent, title, text, buttons, default_button)

    @staticmethod
    def success(parent, title, text, buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton):
        return _show_message(QMessageBox.Information, parent, title, text, buttons, default_button, kind="success")

    @staticmethod
    def warning(parent, title, text, buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton):
        return _show_message(QMessageBox.Warning, parent, title, text, buttons, default_button, kind="warning")

    @staticmethod
    def error(parent, title, text, buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton):
        return _show_message(QMessageBox.Critical, parent, title, text, buttons, default_button, kind="error")

    @staticmethod
    def question(parent, title, text, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, default_button=QMessageBox.NoButton):
        return _show_message(QMessageBox.Question, parent, title, text, buttons, default_button, kind="question")

    @staticmethod
    def confirm(
        parent,
        title,
        text,
        confirm_label="Confirm",
        cancel_label="Cancel",
        confirm_role=QMessageBox.ButtonRole.AcceptRole,
        cancel_role=QMessageBox.ButtonRole.RejectRole,
        kind="question",
    ):
        box = QMessageBox(QMessageBox.Question, title, text, QMessageBox.NoButton, _resolve_parent(parent))
        confirm_btn = box.addButton(confirm_label, confirm_role)
        cancel_btn = box.addButton(cancel_label, cancel_role)
        box.setDefaultButton(confirm_btn)
        box.setEscapeButton(cancel_btn)
        _prepare_box(box, parent, kind=kind)
        result = box.exec()
        return result, box.clickedButton() is confirm_btn


def install_messagebox_theme():
    global _installed
    global _original_exec, _original_information, _original_warning, _original_critical, _original_question

    if _installed:
        return

    _original_exec = QMessageBox.exec
    _original_information = QMessageBox.information
    _original_warning = QMessageBox.warning
    _original_critical = QMessageBox.critical
    _original_question = QMessageBox.question

    def themed_exec(self):
        kind = self.property("messageKind") or "info"
        _prepare_box(self, self.parentWidget(), kind=kind)
        return _original_exec(self)

    def themed_information(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        return AppMessageBox.info(parent, title, text, buttons, defaultButton)

    def themed_warning(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        return AppMessageBox.warning(parent, title, text, buttons, defaultButton)

    def themed_critical(parent, title, text, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        return AppMessageBox.error(parent, title, text, buttons, defaultButton)

    def themed_question(parent, title, text, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, defaultButton=QMessageBox.NoButton):
        return _show_message(QMessageBox.Question, parent, title, text, buttons, defaultButton, kind="question")

    QMessageBox.exec = themed_exec
    QMessageBox.information = staticmethod(themed_information)
    QMessageBox.warning = staticmethod(themed_warning)
    QMessageBox.critical = staticmethod(themed_critical)
    QMessageBox.question = staticmethod(themed_question)

    _installed = True
