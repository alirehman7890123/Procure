from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from employee.addemployee import AddEmployeeWidget
from employee.employeelist import EmployeeListWidget
from employee.employeedetails import EmployeeDetailWidget
from utilities.basepage import BasePage
from utilities.permissions import Permissions

class BaseEmployeeWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()

        # Add Employee Widget
        self.addemployee_widget = AddEmployeeWidget()
        self.addemployee_widget.employeelist.clicked.connect(self.set_employeelist_widget)

        # List Employee Widget
        self.employeelist_widget = EmployeeListWidget()
        self.employeelist_widget.addemployee.clicked.connect(self.set_addemployee_widget)
        self.employeelist_widget.detailpagesignal.connect(self.set_employeedetail_widget)

        # Detail Employee Widget
        self.employeedetail_widget = EmployeeDetailWidget()
        self.employeedetail_widget.employeelist.clicked.connect(self.set_employeelist_widget)

        self.stacked_layout.addWidget(self.addemployee_widget)
        self.stacked_layout.addWidget(self.employeelist_widget)
        self.stacked_layout.addWidget(self.employeedetail_widget)

        self.setLayout(self.stacked_layout)


    @Permissions.require_permission('employee.create')
    def set_addemployee_widget(self):
        self.stacked_layout.setCurrentWidget(self.addemployee_widget)

    @Permissions.require_permission('employee.view')
    def set_employeelist_widget(self):
        self.stacked_layout.setCurrentWidget(self.employeelist_widget)

    @Permissions.require_permission('employee.view')
    def set_employeedetail_widget(self, id):
        self.employeedetail_widget.load_employee_data(id)
        self.stacked_layout.setCurrentWidget(self.employeedetail_widget)

    # 🔑 reset method
    def reset_to_default(self):
        self.stacked_layout.setCurrentWidget(self.employeelist_widget)