from PySide6.QtWidgets import QStackedLayout

from purchase.grn_list import GRNListWidget
from purchase.create_grn import CreateGRNWidget
from purchase.grn_detail import GRNDetailWidget
from utilities.basepage import BasePage
from utilities.permissions import Permissions


class BaseGRNWidget(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()

        self.grn_list_widget = GRNListWidget()
        self.create_grn_widget = CreateGRNWidget()
        self.grn_detail_widget = GRNDetailWidget()

        self.grn_list_widget.add_grn_signal.connect(self.set_create_grn_widget)
        self.grn_list_widget.detail_grn_signal.connect(self.set_grn_detail_widget)

        self.create_grn_widget.grn_list_signal.connect(self.set_grn_list_widget)
        self.grn_detail_widget.grn_list_signal.connect(self.set_grn_list_widget)

        self.stacked_layout.addWidget(self.grn_list_widget)
        self.stacked_layout.addWidget(self.create_grn_widget)
        self.stacked_layout.addWidget(self.grn_detail_widget)

        self.setLayout(self.stacked_layout)

    @Permissions.require_permission('grn.view')
    def set_grn_list_widget(self):
        self.grn_list_widget.load_grn_list()
        self.stacked_layout.setCurrentWidget(self.grn_list_widget)

    @Permissions.require_permission('grn.create')
    def set_create_grn_widget(self):
        self.create_grn_widget.prepare_new_grn()
        self.stacked_layout.setCurrentWidget(self.create_grn_widget)

    @Permissions.require_permission('grn.view')
    def set_grn_detail_widget(self, grn_id):
        self.grn_detail_widget.load_grn_data(grn_id)
        self.stacked_layout.setCurrentWidget(self.grn_detail_widget)

    def reset_to_default(self):
        self.set_grn_list_widget()
