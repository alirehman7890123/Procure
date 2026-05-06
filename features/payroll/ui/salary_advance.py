from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtSql import QSqlDatabase

from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.session_gate import require_open_session
from medic.utilities.session_service import get_active_session_id
from medic.services.payroll_service import (
    get_all_active_employees, insert_salary_advance,
    resolve_payroll_auth_user_id, update_employee_advance_balance
)


class SalaryAdvanceWidget(QWidget):
    advancelist = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("Salary Advance", objectName="SectionTitle")
        self.listbtn = QPushButton("Advance List", objectName="TopRightButton")
        self.listbtn.setCursor(Qt.PointingHandCursor)
        self.listbtn.clicked.connect(self.advancelist)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.listbtn)
        root.addLayout(header)

        sep = QFrame(objectName="lineSeparator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        root.addWidget(sep)

        # --- Form ---
        form = QVBoxLayout()
        form.setSpacing(12)

        self.employee_combo = QComboBox()
        self.employee_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.employee_combo.currentIndexChanged.connect(self._update_balance_label)
        form.addLayout(self._field_row("Employee", self.employee_combo))

        self.balance_label = QLabel("Pending Advance: —")
        self.balance_label.setStyleSheet("color: #e07b00; font-weight: bold;")
        form.addLayout(self._field_row("", self.balance_label))

        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        self.amount_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        form.addLayout(self._field_row("Amount", self.amount_edit))

        self.reason_edit = QLineEdit()
        self.reason_edit.setPlaceholderText("Optional reason / note")
        self.reason_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        form.addLayout(self._field_row("Reason", self.reason_edit))

        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("YYYY-MM-DD")
        self.date_edit.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        self.date_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        form.addLayout(self._field_row("Date", self.date_edit))

        root.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("Disburse Advance", objectName="SaveButton")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedWidth(180)
        self.save_btn.clicked.connect(self.save_advance)
        btn_row.addWidget(self.save_btn)
        root.addLayout(btn_row)

        root.addStretch()

        self._employees = []
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
            self.employee_combo.addItem(emp["name"], userData=emp)
        self.employee_combo.blockSignals(False)
        self._update_balance_label()

    def _update_balance_label(self):
        emp = self.employee_combo.currentData()
        if emp:
            bal = emp.get("advance_balance", 0.0) or 0.0
            self.balance_label.setText(f"Pending Advance Balance: Rs. {bal:,.2f}")
        else:
            self.balance_label.setText("Pending Advance: —")

    # ------------------------------------------------------------------
    @Permissions.require_permission("payroll.advance")
    def save_advance(self):
        if not require_open_session(self):
            return

        emp = self.employee_combo.currentData()
        if not emp:
            AppMessageBox.warning(self, "Validation", "Please select an employee.")
            return

        amount_text = self.amount_edit.text().strip()
        if not amount_text:
            AppMessageBox.warning(self, "Validation", "Enter an advance amount.")
            return
        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            AppMessageBox.warning(self, "Validation", "Enter a valid positive amount.")
            return

        date = self.date_edit.text().strip()
        if len(date) != 10:
            AppMessageBox.warning(self, "Validation", "Enter a valid date (YYYY-MM-DD).")
            return

        session_id  = get_active_session_id()
        recorded_by = self._get_user_id()

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.critical(self, "Error", "Could not start transaction.")
            return
        try:
            ok, result = insert_salary_advance(
                employee_id=emp["id"],
                amount=amount,
                reason=self.reason_edit.text().strip() or None,
                date=date,
                session_id=session_id,
                recorded_by=recorded_by,
            )
            if not ok:
                raise Exception(result)

            if not update_employee_advance_balance(None, emp["id"], amount):
                raise Exception("Failed to update employee advance balance.")

            if not db.commit():
                raise Exception("Commit failed.")

            AppMessageBox.information(self, "Success", f"Advance of Rs. {amount:,.2f} disbursed.")
            self._clear_fields()
            self._load_employees()

        except Exception as exc:
            db.rollback()
            AppMessageBox.critical(self, "Error", str(exc))

    # ------------------------------------------------------------------
    def _clear_fields(self):
        self.amount_edit.clear()
        self.reason_edit.clear()
        self.date_edit.setText(QDate.currentDate().toString("yyyy-MM-dd"))

    def _get_user_id(self):
        username = self.window().property("username")
        return resolve_payroll_auth_user_id(username)
