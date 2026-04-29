import calendar

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QLineEdit, QSizePolicy, QApplication,
    QGroupBox
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.session_gate import require_open_session
from medic.utilities.session_service import get_active_session_id
from medic.utilities.payment_handler import PaymentMethodHandler
from medic.services.payroll_service import (
    get_all_active_employees, get_pending_advances,
    get_attendance_summary, payroll_exists,
    insert_payroll, apply_advance_recovery,
    update_employee_advance_balance
)
from medic.services.payroll_posting_service import (
    get_working_days, build_payroll_payload
)


_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


class AddPayrollWidget(QWidget):
    payrolllist = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("Generate Salary Slip", objectName="SectionTitle")
        self.listbtn = QPushButton("Payroll List", objectName="TopRightButton")
        self.listbtn.setCursor(Qt.PointingHandCursor)
        self.listbtn.clicked.connect(self.payrolllist)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.listbtn)
        root.addLayout(header)

        sep = QFrame(objectName="lineSeparator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        root.addWidget(sep)

        # --- Employee + Period ---
        form = QVBoxLayout()
        form.setSpacing(12)

        self.employee_combo = QComboBox()
        self.employee_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.employee_combo.currentIndexChanged.connect(self._on_employee_changed)
        form.addLayout(self._field_row("Employee", self.employee_combo))

        # Month + Year in one row
        period_row = QHBoxLayout()
        period_lbl = QLabel("Pay Period")
        period_lbl.setMinimumWidth(150)
        period_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.month_combo = QComboBox()
        for i, name in enumerate(_MONTH_NAMES, start=1):
            self.month_combo.addItem(name, userData=i)
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
        self.month_combo.currentIndexChanged.connect(self._refresh_computation)

        self.year_combo = QComboBox()
        current_year = QDate.currentDate().year()
        for y in range(current_year - 2, current_year + 2):
            self.year_combo.addItem(str(y), userData=y)
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentIndexChanged.connect(self._refresh_computation)

        period_row.addWidget(period_lbl)
        period_row.addSpacing(8)
        period_row.addWidget(self.month_combo, 3)
        period_row.addWidget(self.year_combo, 1)
        form.addLayout(period_row)

        # Basic salary (auto-filled, editable)
        self.basic_edit = QLineEdit()
        self.basic_edit.setPlaceholderText("0.00")
        self.basic_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.basic_edit.textChanged.connect(self._refresh_net)
        form.addLayout(self._field_row("Basic Salary", self.basic_edit))

        # Allowances
        self.allowances_edit = QLineEdit()
        self.allowances_edit.setPlaceholderText("0.00")
        self.allowances_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.allowances_edit.textChanged.connect(self._refresh_net)
        form.addLayout(self._field_row("Allowances", self.allowances_edit))

        root.addLayout(form)

        # --- Attendance Summary (read-only) ---
        att_group = QGroupBox("Attendance Summary (auto-computed)")
        att_layout = QHBoxLayout(att_group)
        self.present_lbl  = QLabel("Present: —")
        self.absent_lbl   = QLabel("Absent: —")
        self.halfday_lbl  = QLabel("Half Day: —")
        self.leave_lbl    = QLabel("Leave: —")
        self.workdays_lbl = QLabel("Working Days: —")
        self.deduct_lbl   = QLabel("Deduction: —")
        self.deduct_lbl.setStyleSheet("color: #cc2222; font-weight: bold;")
        for lbl in (self.present_lbl, self.absent_lbl, self.halfday_lbl,
                    self.leave_lbl, self.workdays_lbl, self.deduct_lbl):
            att_layout.addWidget(lbl)
        root.addWidget(att_group)

        # --- Advance Deduction ---
        adv_form = QVBoxLayout()
        adv_form.setSpacing(12)

        self.pending_advance_lbl = QLabel("Pending advance balance: Rs. 0.00")
        self.pending_advance_lbl.setStyleSheet("color: #e07b00;")
        adv_form.addLayout(self._field_row("", self.pending_advance_lbl))

        self.advance_deduct_edit = QLineEdit()
        self.advance_deduct_edit.setPlaceholderText("0.00  (amount to recover this month)")
        self.advance_deduct_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.advance_deduct_edit.textChanged.connect(self._refresh_net)
        adv_form.addLayout(self._field_row("Advance Deduct", self.advance_deduct_edit))
        root.addLayout(adv_form)

        # --- Net Salary Preview ---
        net_row = QHBoxLayout()
        net_row.addStretch()
        self.net_label = QLabel("Net Salary: Rs. 0.00")
        self.net_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a7a1a;")
        net_row.addWidget(self.net_label)
        root.addLayout(net_row)

        sep2 = QFrame(objectName="lineSeparator")
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        sep2.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 1px solid #555; }")
        root.addWidget(sep2)

        # --- Payment method ---
        pay_form = QVBoxLayout()
        pay_form.setSpacing(12)

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        pay_form.addLayout(self._field_row("Payment Method", self.payment_combo))

        self.bank_name_edit = QLineEdit()
        self.bank_name_edit.setPlaceholderText("Bank name")
        self.bank_name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._bank_name_row = self._field_row("Bank Name", self.bank_name_edit)
        pay_form.addLayout(self._bank_name_row)

        self.account_no_edit = QLineEdit()
        self.account_no_edit.setPlaceholderText("Account number")
        self.account_no_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._account_row = self._field_row("Account No.", self.account_no_edit)
        pay_form.addLayout(self._account_row)

        self.wallet_provider_edit = QLineEdit()
        self.wallet_provider_edit.setPlaceholderText("e.g. EasyPaisa")
        self.wallet_provider_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._wallet_provider_row = self._field_row("Wallet Provider", self.wallet_provider_edit)
        pay_form.addLayout(self._wallet_provider_row)

        self.wallet_no_edit = QLineEdit()
        self.wallet_no_edit.setPlaceholderText("Wallet number")
        self.wallet_no_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._wallet_no_row = self._field_row("Wallet No.", self.wallet_no_edit)
        pay_form.addLayout(self._wallet_no_row)

        self.payment_ref_edit = QLineEdit()
        self.payment_ref_edit.setPlaceholderText("Transaction reference (optional)")
        self.payment_ref_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        pay_form.addLayout(self._field_row("Reference", self.payment_ref_edit))

        self.payment_combo.currentTextChanged.connect(self._on_payment_changed)
        self._on_payment_changed(self.payment_combo.currentText())

        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional notes")
        self.notes_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        pay_form.addLayout(self._field_row("Notes", self.notes_edit))
        root.addLayout(pay_form)

        # --- Save button ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("Save & Pay", objectName="SaveButton")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedWidth(160)
        self.save_btn.clicked.connect(self.save_payroll)
        btn_row.addWidget(self.save_btn)
        root.addLayout(btn_row)

        root.addStretch()

        self._employees = []
        self._attendance = {}
        self._pending_advances = []

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
        self._on_employee_changed()

    def _on_employee_changed(self):
        emp = self.employee_combo.currentData()
        if emp:
            self.basic_edit.blockSignals(True)
            self.basic_edit.setText(str(emp.get("basic_salary", 0.0) or 0.0))
            self.basic_edit.blockSignals(False)

            bal = emp.get("advance_balance", 0.0) or 0.0
            self.pending_advance_lbl.setText(f"Pending advance balance: Rs. {bal:,.2f}")

            self._pending_advances = get_pending_advances(emp["id"])
        self._refresh_computation()

    def _refresh_computation(self):
        emp = self.employee_combo.currentData()
        if not emp:
            return
        year  = self.year_combo.currentData()
        month = self.month_combo.currentData()
        year_month = f"{year:04d}-{month:02d}"

        self._attendance = get_attendance_summary(emp["id"], year_month)
        working_days = get_working_days(year, month)

        self.present_lbl.setText(f"Present: {self._attendance['present']}")
        self.absent_lbl.setText(f"Absent: {self._attendance['absent']}")
        self.halfday_lbl.setText(f"Half Day: {self._attendance['half_day']}")
        self.leave_lbl.setText(f"Leave: {self._attendance['leave']}")
        self.workdays_lbl.setText(f"Working Days: {working_days}")

        self._working_days = working_days
        self._refresh_net()

    def _refresh_net(self):
        try:
            basic = float(self.basic_edit.text() or 0)
        except ValueError:
            basic = 0.0
        try:
            allowances = float(self.allowances_edit.text() or 0)
        except ValueError:
            allowances = 0.0
        try:
            adv_deduct = float(self.advance_deduct_edit.text() or 0)
        except ValueError:
            adv_deduct = 0.0

        att = getattr(self, "_attendance", {})
        working_days = getattr(self, "_working_days", 26)

        from medic.services.payroll_posting_service import compute_deduction, compute_net_salary
        deduction = compute_deduction(
            basic, att.get("absent", 0), att.get("half_day", 0), working_days
        )
        net = compute_net_salary(basic, allowances, deduction, adv_deduct)

        self.deduct_lbl.setText(f"Deduction: Rs. {deduction:,.2f}")
        self.net_label.setText(f"Net Salary: Rs. {net:,.2f}")

    def _on_payment_changed(self, method):
        is_bank   = method == "Bank Transfer"
        is_wallet = method in ("EasyPaisa", "JazzCash")

        for widget in (self.bank_name_edit, self.account_no_edit):
            widget.setVisible(is_bank)
        for widget in (self.wallet_provider_edit, self.wallet_no_edit):
            widget.setVisible(is_wallet)

        # Also hide the labels (parent QHBoxLayout items)
        for layout in (self._bank_name_row, self._account_row):
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    item.widget().setVisible(is_bank)
        for layout in (self._wallet_provider_row, self._wallet_no_row):
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    item.widget().setVisible(is_wallet)

    # ------------------------------------------------------------------
    @Permissions.require_permission("payroll.create")
    def save_payroll(self):
        if not require_open_session(self):
            return

        emp = self.employee_combo.currentData()
        if not emp:
            AppMessageBox.warning(self, "Validation", "Select an employee.")
            return

        year  = self.year_combo.currentData()
        month = self.month_combo.currentData()
        year_month = f"{year:04d}-{month:02d}"

        if payroll_exists(emp["id"], year_month):
            AppMessageBox.warning(
                self, "Duplicate",
                f"A payroll slip for {emp['name']} — {year_month} already exists."
            )
            return

        try:
            basic = float(self.basic_edit.text() or 0)
            allowances = float(self.allowances_edit.text() or 0)
            adv_deduct = float(self.advance_deduct_edit.text() or 0)
        except ValueError:
            AppMessageBox.warning(self, "Validation", "Enter valid numeric values.")
            return

        if adv_deduct < 0:
            AppMessageBox.warning(self, "Validation", "Advance deduction cannot be negative.")
            return

        advance_balance = emp.get("advance_balance", 0.0) or 0.0
        if adv_deduct > advance_balance:
            AppMessageBox.warning(
                self, "Validation",
                f"Advance deduction (Rs. {adv_deduct:,.2f}) exceeds pending balance "
                f"(Rs. {advance_balance:,.2f})."
            )
            return

        att  = getattr(self, "_attendance", {})
        wd   = getattr(self, "_working_days", get_working_days(year, month))
        payload = build_payroll_payload(emp["id"], year_month, basic, allowances, att, adv_deduct, wd)

        payment_data = {
            "payment_method":   self.payment_combo.currentText(),
            "bank_name":        self.bank_name_edit.text().strip(),
            "account_no":       self.account_no_edit.text().strip(),
            "transaction_mode": "",
            "wallet_provider":  self.wallet_provider_edit.text().strip(),
            "wallet_no":        self.wallet_no_edit.text().strip(),
            "payment_reference":self.payment_ref_edit.text().strip(),
        }

        session_id = get_active_session_id()
        paid_by    = self._get_user_id()
        paid_on    = QDate.currentDate().toString("yyyy-MM-dd")

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.critical(self, "Error", "Could not start transaction.")
            return
        try:
            ok, result = insert_payroll(
                employee_id=emp["id"],
                month=year_month,
                basic_salary=payload["basic_salary"],
                allowances=payload["allowances"],
                deductions=payload["deductions"],
                advance_deduct=payload["advance_deduct"],
                net_salary=payload["net_salary"],
                payment_data=payment_data,
                notes=self.notes_edit.text().strip() or None,
                paid_on=paid_on,
                session_id=session_id,
                paid_by=paid_by,
            )
            if not ok:
                raise Exception(result)

            # Recover advance against oldest pending advances
            remaining_recovery = adv_deduct
            for adv in self._pending_advances:
                if remaining_recovery <= 0:
                    break
                outstanding = adv["amount"] - adv["recovered"]
                this_recovery = min(remaining_recovery, outstanding)
                if this_recovery > 0:
                    if not apply_advance_recovery(adv["id"], this_recovery):
                        raise Exception("Failed to update advance recovery record.")
                    remaining_recovery -= this_recovery

            # Deduct from employee advance_balance
            if adv_deduct > 0:
                if not update_employee_advance_balance(None, emp["id"], -adv_deduct):
                    raise Exception("Failed to update employee advance balance.")

            if not db.commit():
                raise Exception("Commit failed.")

            AppMessageBox.information(
                self, "Success",
                f"Salary slip saved. Net: Rs. {payload['net_salary']:,.2f}"
            )
            self._clear_fields()
            self._load_employees()

        except Exception as exc:
            db.rollback()
            AppMessageBox.critical(self, "Error", str(exc))

    # ------------------------------------------------------------------
    def _clear_fields(self):
        self.allowances_edit.clear()
        self.advance_deduct_edit.clear()
        self.payment_ref_edit.clear()
        self.notes_edit.clear()
        self.bank_name_edit.clear()
        self.account_no_edit.clear()
        self.wallet_provider_edit.clear()
        self.wallet_no_edit.clear()

    def _get_user_id(self):
        username = QApplication.instance().property("username")
        q = QSqlQuery()
        q.prepare("SELECT id FROM auth WHERE username = ?")
        q.addBindValue(username)
        q.exec()
        return q.value(0) if q.next() else None
