from PySide6.QtWidgets import QWidget, QComboBox, QHBoxLayout, QFrame, QLabel, QLineEdit, QDateEdit, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem, QDialog
from PySide6.QtCore import QFile, Qt, Signal, QDate, QDateTime, QTimer
from PySide6.QtSql import QSqlQuery
from functools import partial
from medic.utilities.stylus import load_stylesheets
from medic.utilities.modern_date_picker import ModernDatePickerDialog





class PurchaseListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Invoice List", objectName="SectionTitle")
        self.addpurchase = QPushButton("Add Purchase", objectName="TopRightButton")
        self.addpurchase.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.addpurchase)

        self.layout.addLayout(header_layout)
        

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

        self.purchase_search = QLineEdit()
        self.purchase_search.setPlaceholderText("Search supplier/invoice or scan barcode...")
        self._purchase_search_timer = QTimer()
        self._purchase_search_timer.setSingleShot(True)
        self._purchase_search_timer.timeout.connect(self.load_purchases_into_table)
        self.purchase_search.textChanged.connect(self.on_purchase_search_text_changed)
        self.purchase_search.returnPressed.connect(self.handle_purchase_search_enter)

        # Date Range Picker
        from_label = QLabel("From")
        self.purchase_date_from = QDate.currentDate().addDays(-30)
        self.from_date_btn = QPushButton("📅 Select Date")
        self.from_date_btn.setFixedWidth(140)
        self.from_date_btn.setCursor(Qt.PointingHandCursor)
        self.from_date_btn.clicked.connect(self._open_from_date_picker)
        self.from_date_btn.setStyleSheet("""
            QPushButton {
                background-color: #2F5D7C;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5A8FB5;
            }
            QPushButton:pressed {
                background-color: #163B5C;
            }
        """)
        self.from_date_display = QLabel(self.purchase_date_from.toString("dd-MM-yyyy"))
        self.from_date_display.setStyleSheet("color: #2F5D7C; font-weight: bold; padding: 5px 10px; background-color: #EEF5FA; border-radius: 4px; border: 1px solid #D0DFE9;")
        
        to_label = QLabel("To")
        self.purchase_date_to = QDate.currentDate()
        self.to_date_btn = QPushButton("📅 Select Date")
        self.to_date_btn.setFixedWidth(140)
        self.to_date_btn.setCursor(Qt.PointingHandCursor)
        self.to_date_btn.clicked.connect(self._open_to_date_picker)
        self.to_date_btn.setStyleSheet("""
            QPushButton {
                background-color: #2F5D7C;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5A8FB5;
            }
            QPushButton:pressed {
                background-color: #163B5C;
            }
        """)
        self.to_date_display = QLabel(self.purchase_date_to.toString("dd-MM-yyyy"))
        self.to_date_display.setStyleSheet("color: #2F5D7C; font-weight: bold; padding: 5px 10px; background-color: #EEF5FA; border-radius: 4px; border: 1px solid #D0DFE9;")

        get_data_btn = QPushButton("Get Data", objectName="TopRightButton")
        get_data_btn.setCursor(Qt.PointingHandCursor)
        get_data_btn.clicked.connect(self.load_purchases_into_table)

        filter_layout.addWidget(self.purchase_search, 3)
        filter_layout.addWidget(from_label)
        filter_layout.addWidget(self.from_date_btn)
        filter_layout.addWidget(self.from_date_display)
        filter_layout.addWidget(to_label)
        filter_layout.addWidget(self.to_date_btn)
        filter_layout.addWidget(self.to_date_display)
        filter_layout.addWidget(get_data_btn)

        self.layout.addLayout(filter_layout)
        self.layout.addSpacing(10)

        self.row_height = 35

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10])
        headers = ["Id", "Supplier", "Invoice", "Rep", "Date", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
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
        self.table.setFixedHeight(400)
        
        # Hide vertical header (row numbers)
        self.table.verticalHeader().setVisible(False)
        
        # Alternating row colors
        self.table.setAlternatingRowColors(True)

        # Selection behaviour
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        
        self.layout.addStretch()


        
        self.setStyleSheet(load_stylesheets())

        self._purchase_barcode_filter = None
        
        

        



    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_purchases_into_table()


    def on_purchase_search_text_changed(self):
        text = (self.purchase_search.text() or "").strip()
        self._purchase_barcode_filter = None
        if text and text.isdigit():
            return
        self._purchase_search_timer.start(400)


    def handle_purchase_search_enter(self):
        text = (self.purchase_search.text() or "").strip()
        if text and text.isdigit():
            self._purchase_barcode_filter = text
            self.load_purchases_into_table()
            return

        self._purchase_barcode_filter = None
        self.load_purchases_into_table()
        

    def _open_from_date_picker(self):
        """Open modern date picker for FROM date."""
        picker = ModernDatePickerDialog(initial_date=self.purchase_date_from, parent=self)
        if picker.exec() == QDialog.Accepted:
            self.purchase_date_from = picker.get_selected_date()
            self.from_date_display.setText(self.purchase_date_from.toString("dd-MM-yyyy"))
            # Auto-load data after date selection
            self.load_purchases_into_table()
    
    def _open_to_date_picker(self):
        """Open modern date picker for TO date."""
        picker = ModernDatePickerDialog(initial_date=self.purchase_date_to, parent=self)
        if picker.exec() == QDialog.Accepted:
            self.purchase_date_to = picker.get_selected_date()
            self.to_date_display.setText(self.purchase_date_to.toString("dd-MM-yyyy"))
            # Auto-load data after date selection
            self.load_purchases_into_table()


    def load_purchases_into_table(self):

        search_text = self.purchase_search.text().strip()
        from_date = self.purchase_date_from.toString("yyyy-MM-dd") + " 00:00:00"
        to_date = self.purchase_date_to.toString("yyyy-MM-dd") + " 23:59:59"
        pattern = f"%{search_text}%"
        barcode_code = self._purchase_barcode_filter

        query = QSqlQuery()
        if barcode_code:
            query.prepare("""
                SELECT DISTINCT pu.id, COALESCE(s.name, ''), pu.sellerinvoice,
                       COALESCE(r.name, ''), pu.creation_date
                FROM purchase pu
                LEFT JOIN supplier s ON s.id = pu.supplier
                LEFT JOIN rep r ON r.id = pu.rep
                JOIN purchaseitem pi ON pi.purchase = pu.id
                JOIN product p ON p.id = pi.product
                WHERE pu.creation_date BETWEEN ? AND ?
                  AND TRIM(CAST(p.code AS TEXT)) = ?
                ORDER BY pu.id DESC
            """)
            query.addBindValue(from_date)
            query.addBindValue(to_date)
            query.addBindValue(barcode_code)
        elif search_text:
            query.prepare("""
                SELECT pu.id, COALESCE(s.name, ''), pu.sellerinvoice,
                       COALESCE(r.name, ''), pu.creation_date
                FROM purchase pu
                LEFT JOIN supplier s ON s.id = pu.supplier
                LEFT JOIN rep r ON r.id = pu.rep
                WHERE pu.creation_date BETWEEN ? AND ?
                  AND (s.name LIKE ? OR pu.sellerinvoice LIKE ?)
                ORDER BY pu.id DESC
            """)
            query.addBindValue(from_date)
            query.addBindValue(to_date)
            query.addBindValue(pattern)
            query.addBindValue(pattern)
        else:
            query.prepare("""
                SELECT pu.id, COALESCE(s.name, ''), pu.sellerinvoice,
                       COALESCE(r.name, ''), pu.creation_date
                FROM purchase pu
                LEFT JOIN supplier s ON s.id = pu.supplier
                LEFT JOIN rep r ON r.id = pu.rep
                WHERE pu.creation_date BETWEEN ? AND ?
                ORDER BY pu.id DESC
            """)
            query.addBindValue(from_date)
            query.addBindValue(to_date)

        if not query.exec():
            print("Purchase query failed:", query.lastError().text())
            return

        self.table.setRowCount(0)
        row = 0

        while query.next():
            self.table.insertRow(row)

            purchase_id = int(query.value(0))
            supplier = str(query.value(1) or "")
            invoice = str(query.value(2) or "")
            rep = str(query.value(3) or "")
            creation = str(query.value(4) or "")

            dt = QDateTime.fromString(creation, "yyyy-MM-dd HH:mm:ss")
            if dt.isValid():
                creation = dt.date().toString("dd-MM-yyyy")

            self.table.setItem(row, 0, QTableWidgetItem(str(purchase_id)))
            self.table.setItem(row, 1, QTableWidgetItem(supplier))
            self.table.setItem(row, 2, QTableWidgetItem(invoice))
            self.table.setItem(row, 3, QTableWidgetItem(rep))
            self.table.setItem(row, 4, QTableWidgetItem(creation))

            detail = QPushButton('Details')
            detail.setCursor(Qt.PointingHandCursor)
            detail.setFixedSize(80, 28)
            detail.setStyleSheet("""
                QPushButton {
                    background-color: #f5f0f6;
                    color: #244A62;
                    border: 1px solid #d8c7da;
                    border-radius: 14px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #244A62;
                    color: white;
                    border: 1px solid #244A62;
                }
            """)

            self.table.setCellWidget(row, 5, detail)
            detail.clicked.connect(partial(self.detailpagesignal.emit, purchase_id))

            row += 1
        





class MyTable(QTableWidget):
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # user can drag

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            col_width = int(width * (ratio / total))
            self.setColumnWidth(i, col_width)


            
        

