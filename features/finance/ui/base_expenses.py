from PySide6.QtWidgets import QStackedLayout

from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseExpenseWidget(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()
        self.addexpense_widget = None
        self.expenselist_widget = None
        self.expensedetail_widget = None

        self.setLayout(self.stacked_layout)

    def _ensure_addexpense_widget(self):
        if self.addexpense_widget is None:
            from medic.features.finance.ui.add_expense import AddExpenseWidget

            self.addexpense_widget = AddExpenseWidget()
            self.addexpense_widget.expenselist.clicked.connect(self.set_expenselist_widget)
            self.stacked_layout.addWidget(self.addexpense_widget)
        return self.addexpense_widget

    def _ensure_expenselist_widget(self):
        if self.expenselist_widget is None:
            from medic.features.finance.ui.expense_list import ExpenseListWidget

            self.expenselist_widget = ExpenseListWidget()
            self.expenselist_widget.addexpense.clicked.connect(self.set_addexpense_widget)
            self.expenselist_widget.detailpagesignal.connect(self.set_expensedetail_widget)
            self.stacked_layout.addWidget(self.expenselist_widget)
        return self.expenselist_widget

    def _ensure_expensedetail_widget(self):
        if self.expensedetail_widget is None:
            from medic.features.finance.ui.expense_detail import ExpenseDetailWidget

            self.expensedetail_widget = ExpenseDetailWidget()
            self.expensedetail_widget.expenselist.clicked.connect(self.set_expenselist_widget)
            self.stacked_layout.addWidget(self.expensedetail_widget)
        return self.expensedetail_widget

    @Permissions.require_permission("expense.create")
    def set_addexpense_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_addexpense_widget())

    @Permissions.require_permission("expense.view")
    def set_expenselist_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_expenselist_widget())

    @Permissions.require_permission("expense.view")
    def set_expensedetail_widget(self, expense_id):
        self._ensure_expensedetail_widget()
        self.expensedetail_widget.load_expense_data(expense_id)
        self.stacked_layout.setCurrentWidget(self.expensedetail_widget)

    def reset_to_default(self):
        if Permissions.has_permission("expense.view"):
            self.stacked_layout.setCurrentWidget(self._ensure_expenselist_widget())
        elif Permissions.has_permission("expense.create"):
            self.stacked_layout.setCurrentWidget(self._ensure_addexpense_widget())
