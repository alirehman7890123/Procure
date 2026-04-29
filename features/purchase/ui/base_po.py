from PySide6.QtWidgets import QStackedLayout

from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BasePOWidget(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()
        self.current_po_id = None

        self.add_po_widget = None
        self.po_list_widget = None
        self.po_detail_widget = None
        self.grn_detail_widget = None

        self.setLayout(self.stacked_layout)

    def _ensure_add_po_widget(self):
        if self.add_po_widget is None:
            from medic.features.purchase.ui.add_po import AddPOWidget

            self.add_po_widget = AddPOWidget()
            self.add_po_widget.po_list_signal.connect(self.set_po_list_widget)
            self.stacked_layout.addWidget(self.add_po_widget)
        return self.add_po_widget

    def _ensure_po_list_widget(self):
        if self.po_list_widget is None:
            from medic.features.purchase.ui.po_list import POListWidget

            self.po_list_widget = POListWidget()
            self.po_list_widget.add_po_signal.connect(self.set_add_po_widget)
            self.po_list_widget.detail_po_signal.connect(self.set_po_detail_widget)
            self.stacked_layout.addWidget(self.po_list_widget)
        return self.po_list_widget

    def _ensure_po_detail_widget(self):
        if self.po_detail_widget is None:
            from medic.features.purchase.ui.po_detail import PODetailWidget

            self.po_detail_widget = PODetailWidget()
            self.po_detail_widget.po_list_signal.connect(self.set_po_list_widget)
            self.po_detail_widget.grn_detail_signal.connect(self.set_grn_detail_from_po_widget)
            self.stacked_layout.addWidget(self.po_detail_widget)
        return self.po_detail_widget

    def _ensure_grn_detail_widget(self):
        if self.grn_detail_widget is None:
            from medic.features.purchase.ui.grn_detail import GRNDetailWidget

            self.grn_detail_widget = GRNDetailWidget()
            self.grn_detail_widget.grn_list_signal.connect(self.set_po_detail_widget_from_grn)
            self.stacked_layout.addWidget(self.grn_detail_widget)
        return self.grn_detail_widget

    @Permissions.require_permission("po.view")
    def set_po_list_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_po_list_widget())

    @Permissions.require_permission("po.create")
    def set_add_po_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_add_po_widget())

    @Permissions.require_permission("po.view")
    def set_po_detail_widget(self, po_id):
        self.current_po_id = int(po_id)
        self._ensure_po_detail_widget()
        self.po_detail_widget.load_po_data(po_id)
        self.stacked_layout.setCurrentWidget(self.po_detail_widget)

    @Permissions.require_permission("grn.view")
    def set_grn_detail_from_po_widget(self, grn_id):
        self._ensure_grn_detail_widget()
        self.grn_detail_widget.load_grn_data(grn_id)
        self.stacked_layout.setCurrentWidget(self.grn_detail_widget)

    @Permissions.require_permission("po.view")
    def set_po_detail_widget_from_grn(self):
        if self.current_po_id is None:
            self.set_po_list_widget()
            return
        self.set_po_detail_widget(self.current_po_id)

    def reset_to_default(self):
        self.stacked_layout.setCurrentWidget(self._ensure_po_list_widget())
