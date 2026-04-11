from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, 
    QDateEdit, QTableWidget, QTableWidgetItem, QFrame, QHeaderView, QSizePolicy, QTableWidgetItem
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtSql import QSqlQuery
from utilities.stylus import load_stylesheets
from utilities.table_helpers import centered_cell_widget, style_table_action_button



class MyTable(QTableWidget):
    def __init__(self, column_ratios=None, parent=None):
        super().__init__(parent)
        self.column_ratios = column_ratios or []
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        if total <= 0:
            return
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            self.setColumnWidth(i, int(width * (ratio / total)))


class POListWidget(QWidget):
    """Purchase Order List View"""
    
    add_po_signal = Signal()
    detail_po_signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Orders", objectName="SectionTitle")
        self.add_po_btn = QPushButton("Create New PO", objectName="TopRightButton")
        self.add_po_btn.setCursor(Qt.PointingHandCursor)
        self.add_po_btn.clicked.connect(self.on_add_po_clicked)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.add_po_btn)

        self.layout.addLayout(header_layout)

        # === Separator ===
        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
            QFrame#lineSeparator {
                border: none;
                border-top: 2px solid #333;
            }
        """)
        self.layout.addWidget(line)
        self.layout.addSpacing(10)

        # === Filter Row ===
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(10)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search PO number or supplier...")
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.load_po_list)
        self.search_edit.textChanged.connect(self.on_search_text_changed)

        from_label = QLabel("From")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-90))

        to_label = QLabel("To")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())

        get_data_btn = QPushButton("Get Data", objectName="TopRightButton")
        get_data_btn.setCursor(Qt.PointingHandCursor)
        get_data_btn.clicked.connect(self.load_po_list)

        filter_layout.addWidget(self.search_edit, 3)
        filter_layout.addWidget(from_label)
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(to_label)
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(get_data_btn)

        self.layout.addLayout(filter_layout)
        self.layout.addSpacing(10)

        # === Table ===
        self.row_height = 35
        self.table = MyTable(column_ratios=[0.06, 0.14, 0.21, 0.10, 0.11, 0.10, 0.14, 0.08, 0.06])
        headers = ["ID", "PO Number", "Supplier", "PO Date", "Expected Delivery", "Status", "Progress", "Total Value", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.table.setStyleSheet("QTableWidget::item { color: #333; }")
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        self.layout.addStretch()

        self.setStyleSheet(load_stylesheets())

    def showEvent(self, event):
        super().showEvent(event)
        self.load_po_list()

    def on_search_text_changed(self):
        self.search_timer.stop()
        self.search_timer.start(500)

    def on_add_po_clicked(self):
        self.add_po_signal.emit()

    def load_po_list(self):
        """Load PO list from database"""
        search_text = (self.search_edit.text() or "").strip()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        query = QSqlQuery()
        
        # Base query
        sql = """
            SELECT
                po.id,
                po.po_number,
                s.name,
                po.po_date,
                po.expected_delivery_date,
                po.status,
                COALESCE((SELECT SUM(qty_ordered) FROM purchase_order_line WHERE po_id = po.id), 0) AS ordered_qty,
                COALESCE((
                    SELECT SUM(grl.qty_received)
                    FROM goods_receipt_line grl
                    JOIN goods_receipt gr ON gr.id = grl.grn_id
                    JOIN purchase_order_line pol ON pol.id = grl.po_line_id
                    WHERE gr.po_id = po.id
                ), 0) AS received_qty,
                po.total_value
            FROM purchase_order po
            JOIN supplier s ON po.supplier = s.id
            WHERE po.po_date BETWEEN ? AND ?
        """

        params = [date_from, date_to]

        # Add search filter
        if search_text:
            sql += " AND (po.po_number LIKE ? OR s.name LIKE ?)"
            params.append(f"%{search_text}%")
            params.append(f"%{search_text}%")

        sql += " ORDER BY po.po_date DESC"

        query.prepare(sql)
        for param in params:
            query.addBindValue(param)

        if not query.exec():
            print("Error loading PO list:", query.lastError().text())
            self.table.setRowCount(0)
            return

        # Clear existing rows
        self.table.setRowCount(0)

        row = 0
        while query.next():
            self.table.insertRow(row)

            po_id = query.value(0)
            po_number = query.value(1)
            supplier = query.value(2)
            po_date = query.value(3)
            expected_delivery = query.value(4)
            status = query.value(5)
            ordered_qty = float(query.value(6) or 0)
            received_qty = float(query.value(7) or 0)
            total_value = query.value(8)

            # Add items to row
            self.table.setItem(row, 0, QTableWidgetItem(str(po_id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(po_number)))
            self.table.setItem(row, 2, QTableWidgetItem(str(supplier)))
            self.table.setItem(row, 3, QTableWidgetItem(str(po_date)))
            self.table.setItem(row, 4, QTableWidgetItem(str(expected_delivery)))
            
            # Status badge
            status_item = QTableWidgetItem(str(status))
            self.table.setItem(row, 5, status_item)

            remaining_qty = max(ordered_qty - received_qty, 0.0)
            progress_text = f"{received_qty:.2f}/{ordered_qty:.2f} ({remaining_qty:.2f} left)"
            self.table.setItem(row, 6, QTableWidgetItem(progress_text))
            
            # Total value
            self.table.setItem(row, 7, QTableWidgetItem(f"{float(total_value or 0):.2f}"))

            # Detail button
            detail_btn = style_table_action_button(QPushButton("View"))
            detail_btn.setCursor(Qt.PointingHandCursor)
            detail_btn.clicked.connect(lambda checked, id=po_id: self.detail_po_signal.emit(id))
            self.table.setCellWidget(row, 8, centered_cell_widget(detail_btn))

            row += 1
