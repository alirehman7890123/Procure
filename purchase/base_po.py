from PySide6.QtWidgets import QWidget, QStackedLayout
from PySide6.QtCore import Qt

from purchase.po_list import POListWidget
from purchase.add_po import AddPOWidget
from purchase.po_detail import PODetailWidget
from purchase.grn_detail import GRNDetailWidget
from utilities.basepage import BasePage
from utilities.permissions import Permissions


class PurchaseOrder:
    """Data class for Purchase Order"""
    def __init__(self, id, po_number, supplier, po_date, expected_delivery_date, status, total_value, notes=None):
        self.id = id
        self.po_number = po_number
        self.supplier = supplier
        self.po_date = po_date
        self.expected_delivery_date = expected_delivery_date
        self.status = status
        self.total_value = total_value
        self.notes = notes


class BasePOWidget(BasePage):
    """Main container widget for PO management with stacked layout"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()
        self.current_po_id = None

        # Create sub-widgets
        self.add_po_widget = AddPOWidget()
        self.po_list_widget = POListWidget()
        self.po_detail_widget = PODetailWidget()
        self.grn_detail_widget = GRNDetailWidget()

        # Connect signals
        self.add_po_widget.po_list_signal.connect(self.set_po_list_widget)
        self.po_list_widget.add_po_signal.connect(self.set_add_po_widget)
        self.po_list_widget.detail_po_signal.connect(self.set_po_detail_widget)
        self.po_detail_widget.po_list_signal.connect(self.set_po_list_widget)
        self.po_detail_widget.grn_detail_signal.connect(self.set_grn_detail_from_po_widget)
        self.grn_detail_widget.grn_list_signal.connect(self.set_po_detail_widget_from_grn)

        # Add to stacked layout
        self.stacked_layout.addWidget(self.po_list_widget)
        self.stacked_layout.addWidget(self.add_po_widget)
        self.stacked_layout.addWidget(self.po_detail_widget)
        self.stacked_layout.addWidget(self.grn_detail_widget)

        self.setLayout(self.stacked_layout)

    @Permissions.require_permission('po.view')
    def set_po_list_widget(self):
        """Switch to PO list view"""
        self.stacked_layout.setCurrentWidget(self.po_list_widget)

    @Permissions.require_permission('po.create')
    def set_add_po_widget(self):
        """Switch to Add PO view"""
        self.stacked_layout.setCurrentWidget(self.add_po_widget)

    @Permissions.require_permission('po.view')
    def set_po_detail_widget(self, po_id):
        """Switch to PO detail view and load data"""
        self.current_po_id = int(po_id)
        self.po_detail_widget.load_po_data(po_id)
        self.stacked_layout.setCurrentWidget(self.po_detail_widget)

    @Permissions.require_permission('grn.view')
    def set_grn_detail_from_po_widget(self, grn_id):
        """Open GRN detail while staying inside PO flow"""
        self.grn_detail_widget.load_grn_data(grn_id)
        self.stacked_layout.setCurrentWidget(self.grn_detail_widget)

    @Permissions.require_permission('po.view')
    def set_po_detail_widget_from_grn(self):
        """Return from linked GRN detail to current PO detail"""
        if self.current_po_id is None:
            self.set_po_list_widget()
            return
        self.set_po_detail_widget(self.current_po_id)

    def reset_to_default(self):
        """Reset to list view"""
        self.stacked_layout.setCurrentWidget(self.po_list_widget)
