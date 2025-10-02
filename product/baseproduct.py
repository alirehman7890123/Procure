from PySide6.QtWidgets import QWidget, QStackedLayout

from product.addproduct import AddProductWidget
from product.productlist import ProductListWidget
from product.productdetail import ProductDetailWidget
from utilities.basepage import BasePage


class BaseProductWidget(BasePage):


    def __init__(self, parent=None):

        super().__init__(parent)



        self.stacked_layout = QStackedLayout()


        # Add product Widget
        self.addproduct_widget = AddProductWidget()
        self.addproduct_widget.productlist.clicked.connect(self.set_productlist_widget)


        # List product Widget
        self.productlist_widget = ProductListWidget()
        self.productlist_widget.addproduct.clicked.connect(self.set_addproduct_widget)
        self.productlist_widget.detailpagesignal.connect(self.set_productdetail_widget)



        # Detail product Widget
        self.productdetail_widget = ProductDetailWidget()
        self.productdetail_widget.productlist.clicked.connect(self.set_productlist_widget)
        self.productdetail_widget.modal_signal.connect(self.set_modal)
        

        self.stacked_layout.addWidget(self.addproduct_widget)
        self.stacked_layout.addWidget(self.productlist_widget)
        self.stacked_layout.addWidget(self.productdetail_widget)



        self.setLayout(self.stacked_layout)


    def set_modal(self, batch_id):
        self.productdetail_widget.open_modal_window(batch_id)
        

    def set_addproduct_widget(self):
        self.stacked_layout.setCurrentWidget(self.addproduct_widget)

    
    def set_productlist_widget(self):
        self.stacked_layout.setCurrentWidget(self.productlist_widget)


    def set_productdetail_widget(self, id):
        self.productdetail_widget.load_product_data(id)
        self.stacked_layout.setCurrentWidget(self.productdetail_widget)
        
    

    # 🔑 reset method
    def reset_to_default(self):
        self.stacked_layout.setCurrentWidget(self.productlist_widget)
