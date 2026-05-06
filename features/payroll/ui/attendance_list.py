from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate, Signal

from medic.utilities.stylus import load_stylesheets
from medic.services.payroll_service import get_monthly_attendance_all_employees


_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


class AttendanceListWidget(QWidget):
    markattendance = Signal()   # go to mark-attendance page
    payrolllist    = Signal()   # back to payroll slips

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("Attendance Summary", objectName="SectionTitle")
        self.back_btn = QPushButton("← Payroll Slips", objectName="TopRightButton")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.payrolllist)
        self.mark_btn = QPushButton("Mark Attendance", objectName="TopRightButton")
        self.mark_btn.setCursor(Qt.PointingHandCursor)
        self.mark_btn.clicked.connect(self.markattendance)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.back_btn)
        header.addWidget(self.mark_btn)
        root.addLayout(header)

        line = QFrame(objectName="lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        root.addWidget(line)

        # --- Filters ---
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Year:"))
        self.year_combo = QComboBox()
        current_year = QDate.currentDate().year()
        for y in range(current_year - 2, current_year + 2):
            self.year_combo.addItem(str(y), userData=y)
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentIndexChanged.connect(self._load_data)
        filter_row.addWidget(self.year_combo)

        filter_row.addSpacing(16)
        filter_row.addWidget(QLabel("Month:"))
        self.month_combo = QComboBox()
        for i, name in enumerate(_MONTH_NAMES, start=1):
            self.month_combo.addItem(name, userData=i)
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
        self.month_combo.currentIndexChanged.connect(self._load_data)
        filter_row.addWidget(self.month_combo)

        filter_row.addStretch()
        root.addLayout(filter_row)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "No.", "Employee", "Present", "Absent", "Half Day", "Leave", "Total Marked"
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
        year  = self.year_combo.currentData()
        month = self.month_combo.currentData()
        year_month = f"{year:04d}-{month:02d}"

        rows = get_monthly_attendance_all_employees(year_month)
        self.table.setRowCount(len(rows))

        for r, rec in enumerate(rows):
            def _item(val, align=Qt.AlignCenter):
                it = QTableWidgetItem(str(val))
                it.setTextAlignment(align)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                return it

            self.table.setItem(r, 0, _item(r + 1))
            self.table.setItem(r, 1, _item(rec["name"], Qt.AlignLeft | Qt.AlignVCenter))
            self.table.setItem(r, 2, _item(rec["present"]))
            self.table.setItem(r, 3, _item(rec["absent"]))
            self.table.setItem(r, 4, _item(rec["half_day"]))
            self.table.setItem(r, 5, _item(rec["leave"]))
            self.table.setItem(r, 6, _item(rec["total_marked"]))
