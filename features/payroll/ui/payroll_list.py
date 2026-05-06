from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate, Signal

from medic.utilities.stylus import load_stylesheets
from medic.services.payroll_service import get_payroll_list, get_all_active_employees


_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


class PayrollListWidget(QWidget):
    addpayroll   = Signal()
    detailsignal = Signal(int)   # payroll_id
    attendance_nav = Signal()
    advance_nav    = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("Payroll", objectName="SectionTitle")
        self.attendance_btn = QPushButton("Attendance", objectName="TopRightButton")
        self.attendance_btn.setCursor(Qt.PointingHandCursor)
        self.attendance_btn.clicked.connect(self.attendance_nav)
        self.advance_btn = QPushButton("Salary Advance", objectName="TopRightButton")
        self.advance_btn.setCursor(Qt.PointingHandCursor)
        self.advance_btn.clicked.connect(self.advance_nav)
        self.add_btn = QPushButton("New Salary Slip", objectName="TopRightButton")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.addpayroll)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.attendance_btn)
        header.addWidget(self.advance_btn)
        header.addWidget(self.add_btn)
        root.addLayout(header)

        sep = QFrame(objectName="lineSeparator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        root.addWidget(sep)

        # --- Filters ---
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Employee:"))
        self.emp_filter = QComboBox()
        self.emp_filter.addItem("All", userData=None)
        self.emp_filter.currentIndexChanged.connect(self._load_data)
        filter_row.addWidget(self.emp_filter)

        filter_row.addSpacing(16)
        filter_row.addWidget(QLabel("Year:"))
        self.year_combo = QComboBox()
        current_year = QDate.currentDate().year()
        self.year_combo.addItem("All", userData=None)
        for y in range(current_year - 2, current_year + 2):
            self.year_combo.addItem(str(y), userData=y)
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentIndexChanged.connect(self._load_data)
        filter_row.addWidget(self.year_combo)

        filter_row.addSpacing(8)
        filter_row.addWidget(QLabel("Month:"))
        self.month_combo = QComboBox()
        self.month_combo.addItem("All", userData=None)
        for i, name in enumerate(_MONTH_NAMES, start=1):
            self.month_combo.addItem(name, userData=i)
        self.month_combo.currentIndexChanged.connect(self._load_data)
        filter_row.addWidget(self.month_combo)

        filter_row.addStretch()
        root.addLayout(filter_row)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "No.", "Employee", "Month", "Basic", "Deductions", "Net Salary",
            "Payment", "Detail"
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
        self._load_employees()
        self._load_data()

    def _load_employees(self):
        self.emp_filter.blockSignals(True)
        current = self.emp_filter.currentData()
        self.emp_filter.clear()
        self.emp_filter.addItem("All", userData=None)
        for emp in get_all_active_employees():
            self.emp_filter.addItem(emp["name"], userData=emp["id"])
        # restore selection
        idx = self.emp_filter.findData(current)
        if idx >= 0:
            self.emp_filter.setCurrentIndex(idx)
        self.emp_filter.blockSignals(False)

    def _load_data(self):
        emp_id = self.emp_filter.currentData()
        year   = self.year_combo.currentData()
        month  = self.month_combo.currentData()

        year_month = None
        if year and month:
            year_month = f"{year:04d}-{month:02d}"
        elif year:
            year_month = None  # will filter client-side by year

        rows = get_payroll_list(employee_id=emp_id, year_month=year_month)

        # Client-side year filter if month=All but year selected
        if year and not month:
            rows = [r for r in rows if r["month"].startswith(str(year))]

        self.table.setRowCount(len(rows))
        for r, rec in enumerate(rows):
            def _item(val, align=Qt.AlignCenter):
                it = QTableWidgetItem(str(val))
                it.setTextAlignment(align)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                return it

            total_ded = rec["deductions"] + rec["advance_deduct"]

            self.table.setItem(r, 0, _item(r + 1))
            self.table.setItem(r, 1, _item(rec["emp_name"], Qt.AlignLeft | Qt.AlignVCenter))
            self.table.setItem(r, 2, _item(rec["month"]))
            self.table.setItem(r, 3, _item(f"{rec['basic_salary']:,.2f}"))
            self.table.setItem(r, 4, _item(f"{total_ded:,.2f}"))
            self.table.setItem(r, 5, _item(f"{rec['net_salary']:,.2f}"))
            self.table.setItem(r, 6, _item(rec["payment_method"] or ""))

            detail_btn = QPushButton("Detail", objectName="ActionButton")
            detail_btn.setCursor(Qt.PointingHandCursor)
            payroll_id = rec["id"]
            detail_btn.clicked.connect(lambda _, pid=payroll_id: self.detailsignal.emit(pid))
            self.table.setCellWidget(r, 7, detail_btn)
