"""
Shared reusable widgets for medic/.

ProductSearchBox
----------------
A QComboBox subclass with a pre-wired QCompleter that runs the standard
product name search (SELECT id, display_name FROM product WHERE display_name
LIKE ? LIMIT 50) on every keystroke and emits product_selected(int, str)
when the user picks an item.

Usage
-----
    box = ProductSearchBox(self)
    box.product_selected.connect(self.on_product_picked)

    def on_product_picked(self, product_id: int, display_name: str):
        # do your context-specific field filling here
        ...

Custom query
------------
If you need extra columns (e.g. discount_group, tax_group in sales):

    box = ProductSearchBox(self, query_fn=my_query_fn)

    def my_query_fn(search_text: str) -> list[tuple[str, any]]:
        # return list of (display_name, data) where data is stored in
        # the combobox item and passed back via product_selected_with_data
        ...

    box.product_selected_with_data.connect(self.on_product_with_data)
"""

from PySide6.QtWidgets import QComboBox, QCompleter
from PySide6.QtCore import Qt, Signal, QStringListModel
from PySide6.QtSql import QSqlQuery


_POPUP_STYLE = """
    QListView {
        padding: 5px;
        background-color: white;
        border: 1px solid gray;
        color: #333;
    }
    QListView::item {
        padding: 6px 10px;
    }
    QListView::item:selected {
        background-color: #5A9EC9;
        color: white;
    }
"""


class ProductSearchBox(QComboBox):
    """
    Editable QComboBox with autocomplete for product search.

    Signals
    -------
    product_selected(product_id: int, display_name: str)
        Emitted when the user selects a product from the completer.
        `product_id` is the integer primary key; `display_name` is the
        selected text.

    product_selected_with_data(product_id: int, display_name: str, data: object)
        Same, but also carries whatever extra data was stored on the item
        (e.g. a dict with discount_group, tax_group for the sales screen).
        Only emitted when a `query_fn` is provided.
    """

    product_selected = Signal(int, str)
    product_selected_with_data = Signal(int, str, object)

    def __init__(self, parent=None, *, query_fn=None, placeholder="Search product...", defer_numeric_to_enter=False):
        super().__init__(parent)

        # query_fn signature: (search_text: str) -> list[tuple[str, any]]
        # returns [(display_name, data), ...]
        self._query_fn = query_fn
        self._defer_numeric_to_enter = defer_numeric_to_enter

        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setMaxVisibleItems(15)
        self.setPlaceholderText(placeholder)
        self.wheelEvent = lambda event: event.ignore()

        self._completer = QCompleter(self)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchStartsWith)

        popup = self._completer.popup()
        if popup is not None:
            popup.setStyleSheet(_POPUP_STYLE)

        self._completer.activated[str].connect(self._on_activated)
        self._wired_line_edit = None
        current_line_edit = self.lineEdit()
        if current_line_edit is not None:
            current_line_edit.setCompleter(self._completer)
        self._wire_line_edit(current_line_edit)

    def setLineEdit(self, line_edit):
        super().setLineEdit(line_edit)
        if line_edit is not None:
            line_edit.setCompleter(self._completer)
        self._wire_line_edit(line_edit)

    def _wire_line_edit(self, line_edit):
        if line_edit is None or line_edit is self._wired_line_edit:
            return
        if self._wired_line_edit is not None:
            try:
                self._wired_line_edit.textEdited.disconnect(self._on_text_edited)
            except Exception:
                pass
        line_edit.textEdited.connect(self._on_text_edited)
        self._wired_line_edit = line_edit

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def clear_selection(self):
        """Reset the box to empty without triggering search."""
        self.blockSignals(True)
        self.clear()
        self.setCurrentIndex(-1)
        self.blockSignals(False)
        if self._completer.popup():
            self._completer.popup().hide()

    def set_text(self, text: str):
        """Set the line-edit text without triggering search."""
        le = self.lineEdit()
        if le:
            le.blockSignals(True)
            le.setText(text)
            le.blockSignals(False)

    def select_result(self, text: str, data, *, emit_signals=True):
        """Programmatically commit a selected product into the combo."""
        text = str(text or "").strip()
        if not text:
            return

        self.blockSignals(True)
        self.clear()
        self.addItem(text, data)
        self.setCurrentIndex(0)
        self.blockSignals(False)

        if self.lineEdit() is not None:
            self.lineEdit().blockSignals(True)
            self.lineEdit().setText(text)
            self.lineEdit().blockSignals(False)

        self._completer.setModel(QStringListModel([], self))
        popup = self._completer.popup()
        if popup is not None:
            popup.hide()

        if not emit_signals:
            return

        if self._query_fn:
            product_id = data.get("product_id") if isinstance(data, dict) else int(data)
            self.product_selected.emit(product_id, text)
            self.product_selected_with_data.emit(product_id, text, data)
        else:
            self.product_selected.emit(int(data), text)

    @staticmethod
    def format_product_label(display_name, pack_size):
        name = str(display_name or "").strip()
        try:
            pack_size_num = int(float(pack_size))
        except (TypeError, ValueError):
            pack_size_num = 0

        if pack_size_num > 0:
            return f"{name} [{pack_size_num}s]"
        return name

    @staticmethod
    def lookup_product_by_code(code_text: str):
        code_text = str(code_text or "").strip()
        if not code_text:
            return None

        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                p.id,
                p.display_name,
                COALESCE((
                    SELECT pp.pack_size
                    FROM price_pack pp
                    WHERE pp.product_id = p.id
                    ORDER BY pp.is_default DESC, pp.id DESC
                    LIMIT 1
                ), 0) AS pack_size
            FROM product
            WHERE TRIM(CAST(p.code AS TEXT)) = ?
              AND COALESCE(status, 'active') IN ('active', 'used')
            LIMIT 1
            """
        )
        query.addBindValue(code_text)

        if not query.exec() or not query.next():
            return None

        return int(query.value(0)), ProductSearchBox.format_product_label(query.value(1), query.value(2))

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _on_text_edited(self, _text):
        self._load_suggestions()

    def _load_suggestions(self):
        current_text = self.lineEdit().text().strip()

        if self._defer_numeric_to_enter and current_text.isdigit():
            self.blockSignals(True)
            self.clear()
            self.setCurrentIndex(-1)
            if self.lineEdit() is not None:
                self.lineEdit().setText(current_text)
            self.blockSignals(False)
            self._completer.setModel(QStringListModel([], self))
            popup = self._completer.popup()
            if popup is not None:
                popup.hide()
            return

        if not current_text:
            self.blockSignals(True)
            self.clear()
            self.setCurrentIndex(-1)
            self.blockSignals(False)
            self._completer.setModel(QStringListModel([], self))
            if self._completer.popup():
                self._completer.popup().hide()
            return

        if self._query_fn:
            results = self._query_fn(current_text)  # [(name, data), ...]
        else:
            results = self._default_query(current_text)  # [(name, product_id), ...]

        self.blockSignals(True)
        self.clear()
        for name, data in results:
            self.addItem(name, data)
        self.setCurrentIndex(-1)
        self.lineEdit().setText(current_text)
        self.blockSignals(False)

        names = [name for name, _data in results]
        self._completer.setModel(QStringListModel(names, self))
        self._completer.setCompletionPrefix(current_text)
        if results:
            self._completer.complete()

    def _on_activated(self, text: str):
        text = text.strip()
        index = self.findText(text, Qt.MatchFixedString)
        if index < 0:
            return

        data = self.itemData(index)
        self.select_result(text, data, emit_signals=True)

    def popup_is_visible(self):
        popup = self._completer.popup()
        return bool(popup and popup.isVisible())

    @staticmethod
    def _default_query(search_text: str) -> list:
        """Run the standard id/display_name search."""
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                p.id,
                p.display_name,
                COALESCE((
                    SELECT pp.pack_size
                    FROM price_pack pp
                    WHERE pp.product_id = p.id
                    ORDER BY pp.is_default DESC, pp.id DESC
                    LIMIT 1
                ), 0) AS pack_size
            FROM product p
            WHERE p.display_name LIKE ?
            ORDER BY p.display_name ASC
            LIMIT 50
            """
        )
        query.addBindValue(f"{search_text}%")
        results = []
        if not query.exec():
            return results
        while query.next():
            pid = int(query.value(0))
            label = ProductSearchBox.format_product_label(query.value(1), query.value(2))
            results.append((label, pid))
        return results
