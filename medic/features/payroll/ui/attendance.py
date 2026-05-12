from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QLineEdit, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate, Signal

from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.session_gate import require_open_session
from medic.utilities.session_service import get_active_session_id
from medic.services.payroll_service import (
    get_all_active_employees, get_attendance_record,
    resolve_payroll_auth_user_id, upsert_attendance
)


class AttendanceWidget(QWidget):
    attendancelist = Signal()   # emitted to navigate to list

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("Mark Attendance", objectName="SectionTitle")
        self.listbtn = QPushButton("Attendance List", objectName="TopRightButton")
        self.listbtn.setCursor(Qt.PointingHandCursor)
        self.listbtn.clicked.connect(self.attendancelist)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.listbtn)
        root.addLayout(header)

        line = QFrame(objectName="lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        root.addWidget(line)

        # --- Form ---
        form = QVBoxLayout()
        form.setSpacing(12)

        self.employee_combo = QComboBox()
        self.employee_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.employee_combo.currentIndexChanged.connect(self._on_employee_changed)
        form.addLayout(self._field_row("Employee", self.employee_combo))

        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("YYYY-MM-DD  (e.g. 2026-04-23)")
        self.date_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.date_edit.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        self.date_edit.textChanged.connect(self._try_load_existing)
        form.addLayout(self._field_row("Date", self.date_edit))

        self.status_combo = QComboBox()
        self.status_combo.addItems(["present", "absent", "half_day", "leave"])
        self.status_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        form.addLayout(self._field_row("Status", self.status_combo))

        self.checkin_edit = QLineEdit()
        self.checkin_edit.setPlaceholderText("HH:MM  (optional)")
        self.checkin_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        form.addLayout(self._field_row("Check In", self.checkin_edit))

        self.checkout_edit = QLineEdit()
        self.checkout_edit.setPlaceholderText("HH:MM  (optional)")
        self.checkout_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        form.addLayout(self._field_row("Check Out", self.checkout_edit))

        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional notes")
        self.notes_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        form.addLayout(self._field_row("Notes", self.notes_edit))

        root.addLayout(form)

        # --- Bulk mark section ---
        bulk_line = QFrame(objectName="lineSeparator")
        bulk_line.setFrameShape(QFrame.HLine)
        bulk_line.setFrameShadow(QFrame.Sunken)
        bulk_line.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 1px solid #555; }")
        root.addWidget(bulk_line)

        bulk_header = QHBoxLayout()
        bulk_label = QLabel("Bulk Mark — All Employees", objectName="SubSectionTitle")
        self.bulk_status_combo = QComboBox()
        self.bulk_status_combo.addItems(["present", "absent", "half_day", "leave"])
        self.bulk_status_combo.setFixedWidth(130)
        self.bulk_btn = QPushButton("Mark All", objectName="SaveButton")
        self.bulk_btn.setCursor(Qt.PointingHandCursor)
        self.bulk_btn.clicked.connect(self.mark_bulk)
        bulk_header.addWidget(bulk_label)
        bulk_header.addStretch()
        bulk_header.addWidget(QLabel("Status:"))
        bulk_header.addWidget(self.bulk_status_combo)
        bulk_header.addSpacing(8)
        bulk_header.addWidget(self.bulk_btn)
        root.addLayout(bulk_header)

        # --- Save button ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("Save Attendance", objectName="SaveButton")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedWidth(160)
        self.save_btn.clicked.connect(self.save_attendance)
        btn_row.addWidget(self.save_btn)
        root.addLayout(btn_row)

        root.addStretch()

        self._employees = []   # list of dicts from get_all_active_employees
        self.setStyleSheet(load_stylesheets())

    # ------------------------------------------------------------------
    def _field_row(self, label_text, widget):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setMinimumWidth(150)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(lbl)
        row.addSpacing(8)
        row.addWidget(widget)
        return row

    # ------------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self._load_employees()

    def _load_employees(self):
        self._employees = get_all_active_employees()
        self.employee_combo.blockSignals(True)
        self.employee_combo.clear()
        for emp in self._employees:
            self.employee_combo.addItem(emp["name"], userData=emp["id"])
        self.employee_combo.blockSignals(False)
        self._try_load_existing()

    def _on_employee_changed(self):
        self._try_load_existing()

    def _try_load_existing(self):
        """If a record already exists for this employee+date, pre-fill the form."""
        emp_id = self.employee_combo.currentData()
        date = self.date_edit.text().strip()
        if not emp_id or len(date) != 10:
            return
        rec = get_attendance_record(emp_id, date)
        if rec:
            idx = self.status_combo.findText(rec["status"])
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
            self.checkin_edit.setText(rec["check_in"] or "")
            self.checkout_edit.setText(rec["check_out"] or "")
            self.notes_edit.setText(rec["notes"] or "")

    # ------------------------------------------------------------------
    @Permissions.require_permission("payroll.attendance")
    def save_attendance(self):
        if not require_open_session(self):
            return

        emp_id = self.employee_combo.currentData()
        date   = self.date_edit.text().strip()
        status = self.status_combo.currentText()

        if not emp_id:
            AppMessageBox.warning(self, "Validation", "Please select an employee.")
            return
        if len(date) != 10:
            AppMessageBox.warning(self, "Validation", "Enter a valid date (YYYY-MM-DD).")
            return

        session_id  = get_active_session_id()
        recorded_by = self._get_user_id()

        ok = upsert_attendance(
            employee_id=emp_id,
            date=date,
            status=status,
            check_in=self.checkin_edit.text().strip() or None,
            check_out=self.checkout_edit.text().strip() or None,
            notes=self.notes_edit.text().strip() or None,
            session_id=session_id,
            recorded_by=recorded_by,
        )
        if ok:
            AppMessageBox.information(self, "Success", "Attendance saved.")
        else:
            AppMessageBox.critical(self, "Error", "Failed to save attendance.")

    @Permissions.require_permission("payroll.attendance")
    def mark_bulk(self):
        if not require_open_session(self):
            return

        date   = self.date_edit.text().strip()
        status = self.bulk_status_combo.currentText()

        if len(date) != 10:
            AppMessageBox.warning(self, "Validation", "Enter a valid date (YYYY-MM-DD) above first.")
            return

        confirm = AppMessageBox.question(
            self, "Bulk Mark",
            f"Mark ALL active employees as '{status}' on {date}?"
        )
        if confirm != AppMessageBox.Yes:
            return

        session_id  = get_active_session_id()
        recorded_by = self._get_user_id()
        failed = 0
        for emp in self._employees:
            ok = upsert_attendance(
                employee_id=emp["id"],
                date=date,
                status=status,
                check_in=None,
                check_out=None,
                notes=None,
                session_id=session_id,
                recorded_by=recorded_by,
            )
            if not ok:
                failed += 1

        if failed == 0:
            AppMessageBox.information(self, "Success", f"Marked {len(self._employees)} employees.")
        else:
            AppMessageBox.warning(self, "Partial", f"{failed} records failed to save.")

    # ------------------------------------------------------------------
    def _get_user_id(self):
        username = self.window().property("username")
        return resolve_payroll_auth_user_id(username)
