from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame, QLabel, QDateEdit, QLineEdit, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt, QDate, Signal, QDateTime, QTimer
from PySide6.QtSql import QSqlQuery
from functools import partial

from utilities.stylus import load_stylesheets
from utilities.table_helpers import centered_cell_widget, style_table_action_button


class ReceiptListWidget(QWidget):

    salesdetailsignal = Signal(int)

    def __init__(self, parent=None):

        super().__init__(parent)

        self._sales_barcode_filter = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        heading = QLabel("Sales Invoices", objectName="SectionTitle")
        self.addinvoice = QPushButton("Add Invoice", objectName="TopRightButton")
        self.addinvoice.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.addinvoice)
        self.layout.addLayout(header_layout)

        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(
            """
            QFrame#lineSeparator {
                border: none;
                border-top: 2px solid #333;
            }
            """
        )
        self.layout.addWidget(line)
        self.layout.addSpacing(10)

        # Unified search + date filter
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search customer or scan barcode...")
        self._sales_search_timer = QTimer()
        self._sales_search_timer.setSingleShot(True)
        self._sales_search_timer.timeout.connect(self.load_sales_into_table)
        self.search_edit.textChanged.connect(self.on_sales_search_text_changed)
        self.search_edit.returnPressed.connect(self.handle_sales_search_enter)
        search_layout.addWidget(self.search_edit, 4)

        from_label = QLabel("Date From")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))

        to_label = QLabel("Date To")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())

        search_layout.addWidget(from_label)
        search_layout.addWidget(self.date_from)
        search_layout.addWidget(to_label)
        search_layout.addWidget(self.date_to)

        search_data = QPushButton("Get Data")
        search_data.setStyleSheet("color: #333; padding: 3px 5px;")
        search_data.clicked.connect(self.load_sales_into_table)
        search_layout.addWidget(search_data)

        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)

        self.row_height = 35

        self.table = MyTable(column_ratios=[0.05, 0.15, 0.40, 0.10, 0.10, 0.08])
        headers = ["Id", "Customer", "Products", "Received", "Date", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setTextElideMode(Qt.ElideRight)

        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        detail_col = headers.index("Detail")
        self.table.horizontalHeaderItem(detail_col).setTextAlignment(Qt.AlignCenter)

        self.table.setStyleSheet("QTableWidget::item { color: #333; }")
        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        self.table.setMinimumWidth(700)

        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        self.layout.addStretch()

        self.setStyleSheet(load_stylesheets())

    def on_sales_search_text_changed(self):
        text = (self.search_edit.text() or "").strip()
        self._sales_barcode_filter = None
        if text and text.isdigit():
            return
        self._sales_search_timer.start(400)

    def handle_sales_search_enter(self):
        text = (self.search_edit.text() or "").strip()
        if text and text.isdigit():
            self._sales_barcode_filter = text
            self.load_sales_into_table()
            return

        self._sales_barcode_filter = None
        self.load_sales_into_table()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_sales_into_table()

    def load_sales_into_table(self):
        search_text = self.search_edit.text().strip()
        from_date = self.date_from.date().toString("yyyy-MM-dd") + " 00:00:00"
        to_date = self.date_to.date().toString("yyyy-MM-dd") + " 23:59:59"
        pattern = f"%{search_text}%"
        barcode_code = self._sales_barcode_filter

        query = QSqlQuery()
        if barcode_code:
            query.prepare(
                """
                SELECT
                    s.id,
                    COALESCE(c.name, 'Walk-in Customer'),
                    (
                        SELECT GROUP_CONCAT(pr.display_name, ' | ')
                        FROM salesitem si
                        LEFT JOIN product pr ON pr.id = si.product_id
                        WHERE si.sales_id = s.id
                    ) AS products,
                    s.received,
                    s.creation_date
                FROM sales s
                LEFT JOIN customer c ON c.id = s.customer
                WHERE s.creation_date BETWEEN ? AND ?
                  AND EXISTS (
                      SELECT 1
                      FROM salesitem si2
                      JOIN product p2 ON p2.id = si2.product_id
                      WHERE si2.sales_id = s.id
                        AND TRIM(CAST(p2.code AS TEXT)) = ?
                  )
                ORDER BY s.id DESC
                """
            )
            query.addBindValue(from_date)
            query.addBindValue(to_date)
            query.addBindValue(barcode_code)
        else:
            query.prepare(
                """
                SELECT
                    s.id,
                    COALESCE(c.name, 'Walk-in Customer'),
                    (
                        SELECT GROUP_CONCAT(pr.display_name, ' | ')
                        FROM salesitem si
                        LEFT JOIN product pr ON pr.id = si.product_id
                        WHERE si.sales_id = s.id
                    ) AS products,
                    s.received,
                    s.creation_date
                FROM sales s
                LEFT JOIN customer c ON c.id = s.customer
                WHERE s.creation_date BETWEEN ? AND ?
                  AND (
                    ? = ''
                    OR c.name LIKE ?
                    OR (s.customer IS NULL AND 'Walk-in Customer' LIKE ?)
                  )
                ORDER BY s.id DESC
                """
            )
            query.addBindValue(from_date)
            query.addBindValue(to_date)
            query.addBindValue(search_text)
            query.addBindValue(pattern)
            query.addBindValue(pattern)

        if not query.exec():
            print("Sales query failed:", query.lastError().text())
            return

        self.table.setRowCount(0)
        row = 0

        while query.next():
            self.table.insertRow(row)

            sales_id = int(query.value(0))
            customer = str(query.value(1) or "Walk-in Customer")
            products = str(query.value(2) or "")
            received = str(query.value(3) or "")
            creation = str(query.value(4) or "")

            dt = QDateTime.fromString(creation, "yyyy-MM-dd HH:mm:ss")
            if dt.isValid():
                creation = dt.date().toString("dd-MM-yyyy")

            self.table.setItem(row, 0, QTableWidgetItem(str(sales_id)))
            self.table.setItem(row, 1, QTableWidgetItem(customer))
            self.table.setItem(row, 2, QTableWidgetItem(products))
            self.table.setItem(row, 3, QTableWidgetItem(received))
            self.table.setItem(row, 4, QTableWidgetItem(creation))

            detail = style_table_action_button(QPushButton("Details"))
            self.table.setCellWidget(row, 5, centered_cell_widget(detail))
            detail.clicked.connect(partial(self.salesdetailsignal.emit, sales_id))

            row += 1


class MyTable(QTableWidget):
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            col_width = int(width * (ratio / total))
            self.setColumnWidth(i, col_width)
