from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal

from medic.utilities.stylus import load_stylesheets
from medic.services.payroll_service import get_all_advances


class AdvanceListWidget(QWidget):
    addadvance  = Signal()
    payrolllist = Signal()   # back to payroll slips

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("Salary Advances", objectName="SectionTitle")
        self.back_btn = QPushButton("← Payroll Slips", objectName="TopRightButton")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.payrolllist)
        self.add_btn = QPushButton("New Advance", objectName="TopRightButton")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.addadvance)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.back_btn)
        header.addWidget(self.add_btn)
        root.addLayout(header)

        sep = QFrame(objectName="lineSeparator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        root.addWidget(sep)

        # --- Filter row ---
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter by Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "pending", "partial", "recovered"])
        self.status_filter.currentIndexChanged.connect(self._load_data)
        filter_row.addWidget(self.status_filter)
        filter_row.addStretch()
        root.addLayout(filter_row)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "No.", "Employee", "Amount", "Recovered", "Outstanding", "Date", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        self.setStyleSheet(load_stylesheets())

    # ------------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()

    def _load_data(self):
        status_filter = self.status_filter.currentText()
        rows = get_all_advances()

        if status_filter != "All":
            rows = [r for r in rows if r["status"] == status_filter]

        self.table.setRowCount(len(rows))
        for r, rec in enumerate(rows):
            outstanding = rec["amount"] - rec["recovered"]

            def _item(val, align=Qt.AlignCenter):
                it = QTableWidgetItem(str(val))
                it.setTextAlignment(align)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                return it

            self.table.setItem(r, 0, _item(r + 1))
            self.table.setItem(r, 1, _item(rec["emp_name"], Qt.AlignLeft | Qt.AlignVCenter))
            self.table.setItem(r, 2, _item(f"{rec['amount']:,.2f}"))
            self.table.setItem(r, 3, _item(f"{rec['recovered']:,.2f}"))
            self.table.setItem(r, 4, _item(f"{outstanding:,.2f}"))
            self.table.setItem(r, 5, _item(rec["date"]))
            self.table.setItem(r, 6, _item(rec["status"]))
