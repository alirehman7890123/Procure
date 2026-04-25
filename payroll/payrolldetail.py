from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from utilities.stylus import load_stylesheets
from services.payroll_service import get_payroll_detail


class PayrollDetailWidget(QWidget):
    payrolllist = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("Payslip Detail", objectName="SectionTitle")
        self.back_btn = QPushButton("Payroll List", objectName="TopRightButton")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.payrolllist)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.back_btn)
        root.addLayout(header)

        sep = QFrame(objectName="lineSeparator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        root.addWidget(sep)

        # --- Detail grid ---
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        def _lbl(text, bold=False):
            l = QLabel(text)
            if bold:
                l.setStyleSheet("font-weight: bold;")
            return l

        # Row 0
        grid.addWidget(_lbl("Employee:", True), 0, 0)
        self.emp_name_lbl = _lbl("—")
        grid.addWidget(self.emp_name_lbl, 0, 1)
        grid.addWidget(_lbl("Role:", True), 0, 2)
        self.role_lbl = _lbl("—")
        grid.addWidget(self.role_lbl, 0, 3)

        # Row 1
        grid.addWidget(_lbl("Contact:", True), 1, 0)
        self.contact_lbl = _lbl("—")
        grid.addWidget(self.contact_lbl, 1, 1)
        grid.addWidget(_lbl("Pay Period:", True), 1, 2)
        self.month_lbl = _lbl("—")
        grid.addWidget(self.month_lbl, 1, 3)

        sep_grid = QFrame()
        sep_grid.setFrameShape(QFrame.HLine)
        sep_grid.setFrameShadow(QFrame.Sunken)
        grid.addWidget(sep_grid, 2, 0, 1, 4)

        # Row 3 — salary breakdown
        grid.addWidget(_lbl("Basic Salary:", True), 3, 0)
        self.basic_lbl = _lbl("—")
        grid.addWidget(self.basic_lbl, 3, 1)
        grid.addWidget(_lbl("Allowances:", True), 3, 2)
        self.allowances_lbl = _lbl("—")
        grid.addWidget(self.allowances_lbl, 3, 3)

        grid.addWidget(_lbl("Absent Deduction:", True), 4, 0)
        self.deductions_lbl = _lbl("—")
        self.deductions_lbl.setStyleSheet("color: #cc2222;")
        grid.addWidget(self.deductions_lbl, 4, 1)
        grid.addWidget(_lbl("Advance Deduction:", True), 4, 2)
        self.advance_lbl = _lbl("—")
        self.advance_lbl.setStyleSheet("color: #cc2222;")
        grid.addWidget(self.advance_lbl, 4, 3)

        sep_grid2 = QFrame()
        sep_grid2.setFrameShape(QFrame.HLine)
        sep_grid2.setFrameShadow(QFrame.Sunken)
        grid.addWidget(sep_grid2, 5, 0, 1, 4)

        grid.addWidget(_lbl("Net Salary:", True), 6, 0)
        self.net_lbl = _lbl("—")
        self.net_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a7a1a;")
        grid.addWidget(self.net_lbl, 6, 1)
        grid.addWidget(_lbl("Status:", True), 6, 2)
        self.status_lbl = _lbl("—")
        grid.addWidget(self.status_lbl, 6, 3)

        sep_grid3 = QFrame()
        sep_grid3.setFrameShape(QFrame.HLine)
        sep_grid3.setFrameShadow(QFrame.Sunken)
        grid.addWidget(sep_grid3, 7, 0, 1, 4)

        grid.addWidget(_lbl("Payment Method:", True), 8, 0)
        self.payment_lbl = _lbl("—")
        grid.addWidget(self.payment_lbl, 8, 1)
        grid.addWidget(_lbl("Reference:", True), 8, 2)
        self.ref_lbl = _lbl("—")
        grid.addWidget(self.ref_lbl, 8, 3)

        grid.addWidget(_lbl("Paid On:", True), 9, 0)
        self.paid_on_lbl = _lbl("—")
        grid.addWidget(self.paid_on_lbl, 9, 1)
        grid.addWidget(_lbl("Paid By:", True), 9, 2)
        self.paid_by_lbl = _lbl("—")
        grid.addWidget(self.paid_by_lbl, 9, 3)

        grid.addWidget(_lbl("Notes:", True), 10, 0)
        self.notes_lbl = _lbl("—")
        self.notes_lbl.setWordWrap(True)
        grid.addWidget(self.notes_lbl, 10, 1, 1, 3)

        root.addLayout(grid)
        root.addStretch()

        self.setStyleSheet(load_stylesheets())

    # ------------------------------------------------------------------
    def load_payroll(self, payroll_id):
        rec = get_payroll_detail(payroll_id)
        if not rec:
            return

        self.emp_name_lbl.setText(rec["emp_name"] or "—")
        self.role_lbl.setText(rec["emp_role"] or "—")
        self.contact_lbl.setText(rec["emp_contact"] or "—")
        self.month_lbl.setText(rec["month"] or "—")

        self.basic_lbl.setText(f"Rs. {rec['basic_salary']:,.2f}")
        self.allowances_lbl.setText(f"Rs. {rec['allowances']:,.2f}")
        self.deductions_lbl.setText(f"Rs. {rec['deductions']:,.2f}")
        self.advance_lbl.setText(f"Rs. {rec['advance_deduct']:,.2f}")
        self.net_lbl.setText(f"Rs. {rec['net_salary']:,.2f}")
        self.status_lbl.setText((rec["status"] or "").capitalize())

        self.payment_lbl.setText(rec["payment_method"] or "—")
        self.ref_lbl.setText(rec["payment_reference"] or "—")
        self.paid_on_lbl.setText(rec["paid_on"] or "—")
        self.paid_by_lbl.setText(rec["paid_by"] or "—")
        self.notes_lbl.setText(rec["notes"] or "—")
