from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from expense.addexpense import AddExpenseWidget
from expense.expenselist import ExpenseListWidget
from expense.expensedetail import ExpenseDetailWidget
from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseExpenseWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()

        # Add expense Widget
        self.addexpense_widget = AddExpenseWidget()
        self.addexpense_widget.expenselist.clicked.connect(self.set_expenselist_widget)

        # List expense Widget
        self.expenselist_widget = ExpenseListWidget()
        self.expenselist_widget.addexpense.clicked.connect(self.set_addexpense_widget)
        self.expenselist_widget.detailpagesignal.connect(self.set_expensedetail_widget)

        # Detail expense Widget
        self.expensedetail_widget = ExpenseDetailWidget()
        self.expensedetail_widget.expenselist.clicked.connect(self.set_expenselist_widget)

        self.stacked_layout.addWidget(self.addexpense_widget)
        self.stacked_layout.addWidget(self.expenselist_widget)
        self.stacked_layout.addWidget(self.expensedetail_widget)
        
        self.setLayout(self.stacked_layout)
        
        
    @Permissions.require_permission('expense.create')
    def set_addexpense_widget(self):
        self.stacked_layout.setCurrentWidget(self.addexpense_widget)

    @Permissions.require_permission('expense.view')
    def set_expenselist_widget(self):
        self.stacked_layout.setCurrentWidget(self.expenselist_widget)

    @Permissions.require_permission('expense.view')
    def set_expensedetail_widget(self, id):
        self.expensedetail_widget.load_expense_data(id)
        self.stacked_layout.setCurrentWidget(self.expensedetail_widget)

   
    # 🔑 reset method
    def reset_to_default(self):
        if Permissions.has_permission('expense.view'):
            self.stacked_layout.setCurrentWidget(self.expenselist_widget)
        elif Permissions.has_permission('expense.create'):
            self.stacked_layout.setCurrentWidget(self.addexpense_widget)
