from PySide6.QtWidgets import QDialog, QMessageBox, QScrollArea, QWidget, QVBoxLayout, QFrame


_installed = False
_original_exec = None
_original_open = None
_original_show = None


def _move_item_to_layout(item, target_layout):
    child_widget = item.widget()
    child_layout = item.layout()
    spacer = item.spacerItem()

    if child_widget is not None:
        target_layout.addWidget(child_widget)
    elif child_layout is not None:
        target_layout.addLayout(child_layout)
    elif spacer is not None:
        target_layout.addSpacerItem(spacer)


def _build_section_widget(items, spacing):
    section = QWidget()
    section_layout = QVBoxLayout(section)
    section_layout.setContentsMargins(0, 0, 0, 0)
    section_layout.setSpacing(spacing if spacing >= 0 else 0)
    for item in items:
        _move_item_to_layout(item, section_layout)
    return section


def _make_dialog_scrollable(dialog):
    if dialog is None:
        return

    if dialog.property("disableAutoDialogScroll"):
        return

    if dialog.property("autoDialogScrollWrapped"):
        return

    if isinstance(dialog, QMessageBox):
        return

    layout = QWidget.layout(dialog)
    if layout is None or layout.count() == 0:
        return

    explicit_content = dialog.findChild(QWidget, "dialogContent")
    explicit_header = dialog.findChild(QWidget, "dialogHeader")
    explicit_footer = dialog.findChild(QWidget, "dialogFooter")

    if explicit_content is not None and explicit_content.findChild(QScrollArea) is None:
        content_layout = explicit_content.layout()
        if content_layout is not None and content_layout.count() > 0:
            margins = content_layout.contentsMargins()
            spacing = content_layout.spacing()
            content_widget = QWidget()
            inner_layout = QVBoxLayout(content_widget)
            inner_layout.setContentsMargins(0, 0, 0, 0)
            inner_layout.setSpacing(spacing if spacing >= 0 else 0)

            while content_layout.count():
                _move_item_to_layout(content_layout.takeAt(0), inner_layout)

            scroll_area = QScrollArea(explicit_content)
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.NoFrame)
            scroll_area.setWidget(content_widget)

            content_layout.setContentsMargins(margins.left(), margins.top(), margins.right(), margins.bottom())
            content_layout.setSpacing(0)
            content_layout.addWidget(scroll_area)

        dialog.setProperty("autoDialogScrollWrapped", True)
        return

    if dialog.findChild(QScrollArea) is not None:
        dialog.setProperty("autoDialogScrollWrapped", True)
        return

    margins = layout.contentsMargins()
    spacing = layout.spacing()
    items = []

    while layout.count():
        items.append(layout.takeAt(0))

    content_items = items
    header_items = []
    footer_items = []

    if len(items) == 2:
        content_items = items[:1]
        footer_items = items[1:]
    elif len(items) >= 3:
        header_items = items[:1]
        content_items = items[1:-1]
        footer_items = items[-1:]

    if not content_items:
        content_items = items
        header_items = []
        footer_items = []

    if header_items:
        layout.addWidget(_build_section_widget(header_items, spacing))

    content_widget = _build_section_widget(content_items, spacing)

    scroll_area = QScrollArea(dialog)
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    scroll_area.setWidget(content_widget)

    layout.setContentsMargins(margins.left(), margins.top(), margins.right(), margins.bottom())
    layout.setSpacing(0)
    layout.addWidget(scroll_area)

    if footer_items:
        layout.addWidget(_build_section_widget(footer_items, spacing))

    dialog.setProperty("autoDialogScrollWrapped", True)


def install_dialog_scrolling():
    global _installed
    global _original_exec, _original_open, _original_show

    if _installed:
        return

    _original_exec = QDialog.exec
    _original_open = QDialog.open
    _original_show = QDialog.show

    def wrapped_exec(self, *args, **kwargs):
        _make_dialog_scrollable(self)
        return _original_exec(self, *args, **kwargs)

    def wrapped_open(self, *args, **kwargs):
        _make_dialog_scrollable(self)
        return _original_open(self, *args, **kwargs)

    def wrapped_show(self, *args, **kwargs):
        _make_dialog_scrollable(self)
        return _original_show(self, *args, **kwargs)

    QDialog.exec = wrapped_exec
    QDialog.open = wrapped_open
    QDialog.show = wrapped_show

    _installed = True
