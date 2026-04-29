from PySide6.QtWidgets import QStackedLayout

from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseGRNWidget(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()
        self.grn_list_widget = None
        self.create_grn_widget = None
        self.grn_detail_widget = None

        self.setLayout(self.stacked_layout)

    def _ensure_grn_list_widget(self):
        if self.grn_list_widget is None:
            from medic.features.purchase.ui.grn_list import GRNListWidget

            self.grn_list_widget = GRNListWidget()
            self.grn_list_widget.add_grn_signal.connect(self.set_create_grn_widget)
            self.grn_list_widget.detail_grn_signal.connect(self.set_grn_detail_widget)
            self.stacked_layout.addWidget(self.grn_list_widget)
        return self.grn_list_widget

    def _ensure_create_grn_widget(self):
        if self.create_grn_widget is None:
            from medic.features.purchase.ui.create_grn import CreateGRNWidget

            self.create_grn_widget = CreateGRNWidget()
            self.create_grn_widget.grn_list_signal.connect(self.set_grn_list_widget)
            self.stacked_layout.addWidget(self.create_grn_widget)
        return self.create_grn_widget

    def _ensure_grn_detail_widget(self):
        if self.grn_detail_widget is None:
            from medic.features.purchase.ui.grn_detail import GRNDetailWidget

            self.grn_detail_widget = GRNDetailWidget()
            self.grn_detail_widget.grn_list_signal.connect(self.set_grn_list_widget)
            self.stacked_layout.addWidget(self.grn_detail_widget)
        return self.grn_detail_widget

    @Permissions.require_permission("grn.view")
    def set_grn_list_widget(self):
        self._ensure_grn_list_widget()
        self.grn_list_widget.load_grn_list()
        self.stacked_layout.setCurrentWidget(self.grn_list_widget)

    @Permissions.require_permission("grn.create")
    def set_create_grn_widget(self):
        self._ensure_create_grn_widget()
        self.create_grn_widget.prepare_new_grn()
        self.stacked_layout.setCurrentWidget(self.create_grn_widget)

    @Permissions.require_permission("grn.view")
    def set_grn_detail_widget(self, grn_id):
        self._ensure_grn_detail_widget()
        self.grn_detail_widget.load_grn_data(grn_id)
        self.stacked_layout.setCurrentWidget(self.grn_detail_widget)

    def reset_to_default(self):
        self.set_grn_list_widget()
