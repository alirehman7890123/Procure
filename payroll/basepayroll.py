from PySide6.QtWidgets import QStackedLayout

from payroll.attendance import AttendanceWidget
from payroll.attendancelist import AttendanceListWidget
from payroll.salaryadvance import SalaryAdvanceWidget
from payroll.advancelist import AdvanceListWidget
from payroll.addpayroll import AddPayrollWidget
from payroll.payrolllist import PayrollListWidget
from payroll.payrolldetail import PayrollDetailWidget
from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BasePayrollWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked = QStackedLayout()

        # --- Attendance ---
        self.attendance_widget = AttendanceWidget()
        self.attendance_widget.attendancelist.connect(self.set_attendance_list)

        self.attendance_list_widget = AttendanceListWidget()
        self.attendance_list_widget.markattendance.connect(self.set_attendance)
        self.attendance_list_widget.payrolllist.connect(self.set_payroll_list)

        # --- Salary Advance ---
        self.advance_widget = SalaryAdvanceWidget()
        self.advance_widget.advancelist.connect(self.set_advance_list)

        self.advance_list_widget = AdvanceListWidget()
        self.advance_list_widget.addadvance.connect(self.set_advance)
        self.advance_list_widget.payrolllist.connect(self.set_payroll_list)

        # --- Payroll ---
        self.addpayroll_widget = AddPayrollWidget()
        self.addpayroll_widget.payrolllist.connect(self.set_payroll_list)

        self.payrolllist_widget = PayrollListWidget()
        self.payrolllist_widget.addpayroll.connect(self.set_addpayroll)
        self.payrolllist_widget.detailsignal.connect(self.set_payroll_detail)
        self.payrolllist_widget.attendance_nav.connect(self.set_attendance_list)
        self.payrolllist_widget.advance_nav.connect(self.set_advance_list)

        self.payrolldetail_widget = PayrollDetailWidget()
        self.payrolldetail_widget.payrolllist.connect(self.set_payroll_list)

        for w in (
            self.attendance_widget,
            self.attendance_list_widget,
            self.advance_widget,
            self.advance_list_widget,
            self.addpayroll_widget,
            self.payrolllist_widget,
            self.payrolldetail_widget,
        ):
            self.stacked.addWidget(w)

        self.setLayout(self.stacked)

    # ------------------------------------------------------------------
    @Permissions.require_permission("payroll.attendance")
    def set_attendance(self):
        self.stacked.setCurrentWidget(self.attendance_widget)

    @Permissions.require_permission("payroll.view")
    def set_attendance_list(self):
        self.stacked.setCurrentWidget(self.attendance_list_widget)

    @Permissions.require_permission("payroll.advance")
    def set_advance(self):
        self.stacked.setCurrentWidget(self.advance_widget)

    @Permissions.require_permission("payroll.view")
    def set_advance_list(self):
        self.stacked.setCurrentWidget(self.advance_list_widget)

    @Permissions.require_permission("payroll.create")
    def set_addpayroll(self):
        self.stacked.setCurrentWidget(self.addpayroll_widget)

    @Permissions.require_permission("payroll.view")
    def set_payroll_list(self):
        self.stacked.setCurrentWidget(self.payrolllist_widget)

    @Permissions.require_permission("payroll.view")
    def set_payroll_detail(self, payroll_id):
        self.payrolldetail_widget.load_payroll(payroll_id)
        self.stacked.setCurrentWidget(self.payrolldetail_widget)

    def reset_to_default(self):
        if Permissions.has_permission("payroll.view"):
            self.stacked.setCurrentWidget(self.payrolllist_widget)
        elif Permissions.has_permission("payroll.create"):
            self.stacked.setCurrentWidget(self.addpayroll_widget)
        elif Permissions.has_permission("payroll.attendance"):
            self.stacked.setCurrentWidget(self.attendance_widget)
