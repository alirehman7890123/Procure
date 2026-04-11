
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget,QTableWidget, QMainWindow,QMessageBox, QPushButton, QHBoxLayout, QVBoxLayout, QStackedLayout, QLabel, QSizePolicy, QGraphicsOpacityEffect
from PySide6.QtCore import QSize, Qt, QEvent, Signal, QObject, QTimer, QStringListModel, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import QScrollArea
from utilities.sidebarbutton import SideBarButton
from utilities.activity_logger import log_activity

from utilities.database import SQLiteConnectionManager
# from database import PostgresConnectionManager
from PySide6.QtGui import QPalette, QColor, QPixmap, QIcon
from dashboard.base_dashboard_page import BaseDashboardWidget
from dashboard.welcome import WelcomeWidget
from business.basebusiness import BaseBusinessWidget
from supplier.basesupplier import BaseSupplierWidget
from salesrep.basesalesrep import BaseSalesRepWidget
from customer.basecustomer import BaseCustomerWidget
from product.baseproduct import BaseProductWidget
from userprofile.baseprofile import BaseProfileWidget
from purchase.basepurchase import BasePurchaseWidget
from purchase.base_po import BasePOWidget
from purchase.base_grn import BaseGRNWidget
from sales.basesales import BaseSalesWidget
from employee.baseemployee import BaseEmployeeWidget
from transaction.basetransaction import BaseTransactionWidget
from purchasereturn.base_purchase_return import BasePurchaseReturnWidget
from salesreturn.base_sales_return import BaseSalesReturnWidget
from expense.baseexpense import BaseExpenseWidget
from reports.basereports import BaseReportsWidget
from salehold.basehold import BaseHoldSalesWidget

from utilities.sizehintfinder import print_size_hints
from functools import wraps
from PySide6.QtWidgets import QMessageBox, QApplication
from utilities.permissions import Permissions
from utilities.license_core import get_current_license_payload, get_license_days_remaining, is_demo_license



permission = Permissions()


import sys
import os
from utilities.app_messagebox import AppMessageBox


def resource_path(relative_path):
    """Return the absolute path to a resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS  # PyInstaller extracts files here
    except AttributeError:
        base_path = os.path.abspath(".")  # running from source
    return os.path.join(base_path, relative_path)


css_files = [
    "styles/global_style.css",
    "styles/table_style.css",
]



class MainWindow(QMainWindow):
    
    
    

    def __init__(self):

        super().__init__()
        self.license_payload = get_current_license_payload()
        self.demo_mode = is_demo_license(self.license_payload)
        self.demo_days_remaining = get_license_days_remaining(self.license_payload)

        self.setWindowTitle(self._build_window_title())
        
        connection = SQLiteConnectionManager('ProcureApp')
        # connection = PostgresConnectionManager()
        connection.open()
        
        screen_geometry = QApplication.primaryScreen().geometry()
        
        width = screen_geometry.width()
        height = screen_geometry.height()
        
        self.setGeometry(0,0, width, height)
        
        
        self.history = []
        self.current_index = -1
        self._is_history_navigation = False
        self._nested_history_connections = []

        
        
        
        # Self Widget and Layout
        
        self.widget = QWidget()
        self.layout = QHBoxLayout()
        self.reset_widget_size(self.layout, self.widget)

        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
       
        
        
        # SIDE-BAR SCROLL
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setFixedWidth(210)
        self.sidebar_scroll.setMinimumWidth(210)
        self.sidebar_scroll.setMaximumWidth(210)
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.sidebar_scroll.setStyleSheet(""" 
                                    background-color: #2F5D7C;
                                    
                                    QScrollArea {
                                        background-color: #2F5D7C;
                                        border: none;
                                    }
                                    QScrollBar:vertical,
                                    QScrollBar:horizontal {
                                        width: 0px;
                                        height: 0px;
                                        background: transparent;
                                        border: none;
                                    }
                                """)


        self.sidebar_scroll.setAttribute(Qt.WA_Hover, True)
        self.sidebar_scroll.installEventFilter(self)

        # COMPACT SIDEBAR RAIL (icon-like navigation, VS Code style)
        self.sidebar_rail_width = 64
        self.sidebar_rail_scroll = QScrollArea()
        self.sidebar_rail_scroll.setFixedWidth(self.sidebar_rail_width)
        self.sidebar_rail_scroll.setMinimumWidth(self.sidebar_rail_width)
        self.sidebar_rail_scroll.setMaximumWidth(self.sidebar_rail_width)
        self.sidebar_rail_scroll.setWidgetResizable(True)
        self.sidebar_rail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar_rail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar_rail_scroll.setStyleSheet("""
                                    background-color: #2F5D7C;

                                    QScrollArea {
                                        background-color: #2F5D7C;
                                        border: none;
                                    }
                                    QScrollBar:vertical,
                                    QScrollBar:horizontal {
                                        width: 0px;
                                        height: 0px;
                                        background: transparent;
                                        border: none;
                                    }
                                """)
        self.sidebar_rail_scroll.hide()
    
        # SIDE-BAR WIDGET
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        
        self.reset_widget_size(sidebar_layout, sidebar_widget)
        

        sidebar_widget.setLayout(sidebar_layout)
        self.sidebar_scroll.setWidget(sidebar_widget)

        # COMPACT SIDEBAR RAIL WIDGET
        rail_widget = QWidget()
        rail_layout = QVBoxLayout(rail_widget)
        self.reset_widget_size(rail_layout, rail_widget)
        rail_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        rail_layout.setSpacing(6)
        rail_widget.setLayout(rail_layout)
        self.sidebar_rail_scroll.setWidget(rail_widget)
        
        
        
        # CONTENT AREA WIDGET
        content_area_widget = QWidget()
        content_area_widget.setStyleSheet("background-color: #fff;") 
        
        content_area_layout = QVBoxLayout()
        self.reset_widget_size(content_area_layout, content_area_widget)
        
        
        
        
        
        
        # HEADER WIDGET
        self.header_widget = QWidget()
        header_layout = QHBoxLayout()

        self.reset_widget_size(header_layout, self.header_widget)
        
        self.header_widget.setFixedHeight(60)
        header_layout.setContentsMargins(20,10,20,10)
        header_layout.setSpacing(8)

        self.header_widget.setLayout(header_layout)
        self.header_widget.setStyleSheet("""
            background-color: #2F5D7C;
            color: #F4F8FB;
            border-bottom: 1px solid #244A62;
        """)
        
        
        self.ham_button = QPushButton()
        self.ham_button.setCursor(Qt.PointingHandCursor)
        self.ham_button.setObjectName("HeaderControlButton")
        self.ham_button.setFixedSize(36, 36)
        self.ham_button.setIconSize(QSize(20, 20))

        self.ham_menu_icon = self._load_icon("res/rail_icons/ham.svg", "res/ham.png")
        self.ham_close_icon = self._load_icon("res/rail_icons/ham_close.svg")
        self.ham_button.setIcon(self.ham_close_icon if not self.ham_close_icon.isNull() else self.ham_menu_icon)
        self.ham_button.clicked.connect(self.collapse_sidebar_from_header)

        header_layout.addWidget(self.ham_button)
        
        business_title = QLabel("Muzammil Traders")
        business_name = self.set_business_name()
        business_title.setText(business_name)
        
        font = business_title.font()
        font.setUnderline(False)
        business_title.setFont(font)
        business_title.setStyleSheet("""
            border: none;
            color: #F4F8FB;
            font-family: 'arial';
            font-size: 20px;
            margin-left: 0px;
            font-weight: 700;
        """)
        
        header_layout.addWidget(business_title)

        self.back_nav_btn = QPushButton()
        self.back_nav_btn.setToolTip("Previous page")
        self.back_nav_btn.setCursor(Qt.PointingHandCursor)
        self.back_nav_btn.setObjectName("HeaderControlButton")
        self.back_nav_btn.setFixedSize(36, 36)
        self.back_nav_btn.setIconSize(QSize(16, 16))
        self.back_nav_icon = self._load_icon("res/rail_icons/nav_back.svg")
        if self.back_nav_icon.isNull():
            self.back_nav_btn.setText("<")
        else:
            self.back_nav_btn.setIcon(self.back_nav_icon)
        self.back_nav_btn.clicked.connect(self.go_back)

        self.forward_nav_btn = QPushButton()
        self.forward_nav_btn.setToolTip("Next page")
        self.forward_nav_btn.setCursor(Qt.PointingHandCursor)
        self.forward_nav_btn.setObjectName("HeaderControlButton")
        self.forward_nav_btn.setFixedSize(36, 36)
        self.forward_nav_btn.setIconSize(QSize(16, 16))
        self.forward_nav_icon = self._load_icon("res/rail_icons/nav_forward.svg")
        if self.forward_nav_icon.isNull():
            self.forward_nav_btn.setText(">")
        else:
            self.forward_nav_btn.setIcon(self.forward_nav_icon)
        self.forward_nav_btn.clicked.connect(self.go_forward)

        header_layout.addSpacing(10)
        header_layout.addWidget(self.back_nav_btn)
        header_layout.addSpacing(6)
        header_layout.addWidget(self.forward_nav_btn)
        
        
        
        
        
       
        header_layout.addStretch()
        
        logout_button = QPushButton("Logout")
        logout_button.setObjectName("HeaderPrimaryButton")
        logout_button.setFixedHeight(32)
        logout_button.setMinimumWidth(78)
        logout_button.setContentsMargins(0, 0, 20, 0)
        logout_button.clicked.connect(self.logout)
        
        header_layout.addWidget(logout_button)
        
        
        
        
        content_area_layout.addWidget(self.header_widget)
        
        content_area_widget.setLayout(content_area_layout)
        
        
        # MAIN CONTENT SCROLL
        main_content_scroll = QScrollArea()
        main_content_scroll.setWidgetResizable(True)
        
        
        # MAIN CONTENT
        self.main_content_widget = QWidget()
        self.main_content_layout = QStackedLayout()
        self.reset_widget_size(self.main_content_layout, self.main_content_widget)
        
        self.main_content_widget.setStyleSheet("background-color: #f3f3f5;")
        
        
        
        # set layout
        self.main_content_widget.setLayout(self.main_content_layout)
        
        # setting scroll
        main_content_scroll.setWidget(self.main_content_widget)
        
        
        
        
        
        # content_area_layout.addWidget(header_widget)
        content_area_layout.addWidget(main_content_scroll)
        
        
        
        
        

        # Logo
        logo = QWidget()
        
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(20,20,20,100)
        logo.setLayout(logo_layout)

        logolabel = QLabel()
        pixmap = QPixmap(resource_path("res/logo.png"))

        logolabel.setPixmap(pixmap)

        logo_layout.addWidget(logolabel)

        sidebar_layout.addWidget(logo)
        
        

        self.dashboard_button = SideBarButton('Dashboard')
        self.business_button = SideBarButton('Business')
        self.profile_button = SideBarButton('Profile')
        self.supplier_button = SideBarButton('Suppliers')
        self.salesrep_button = SideBarButton('Sales Rep')
        self.purchase_button = SideBarButton('Purchase Invoice')
        self.po_button = SideBarButton('Purchase Orders')
        self.grn_button = SideBarButton('Goods Receipt')
        self.sales_button = SideBarButton('Sales')
        self.customer_button = SideBarButton('Customers')
        self.product_button = SideBarButton('Product')
        self.employee_button = SideBarButton('Employees')
        self.transaction_button = SideBarButton('Transactions')
        self.purchase_return = SideBarButton('Purchase Return')
        self.sales_return = SideBarButton('Sales Return')
        self.expense_button = SideBarButton('Expenses')
        self.reports_button = SideBarButton('Reports')
        # self.holdsales_button = SideBarButton('On-Hold Sales')
        
        footer_button = QPushButton()
        footer_button.setStyleSheet("""
                                    margin-top: 100px;
                                    background-color: #2F5D7C;
                                    padding-right: 0px;
                                    height: 0px;
                                    """)

        button_styles = """
        
            QPushButton {
                padding: 10px 0;
                padding-left: 30px; 
                font-family: montserrat;
                border:none;
                color: #fffff0; 
                letter-spacing: 1px; 
                text-align: left;
            }
            QPushButton:hover {
                color: #000000;
                font-weight: 600;
                
            }
            QPushButton:pressed {
                background-color: #163B5C;
                color: #fff;
            }
            
        """

        self.dashboard_button.setStyleSheet(button_styles)
        self.business_button.setStyleSheet(button_styles)
        self.profile_button.setStyleSheet(button_styles)
        self.supplier_button.setStyleSheet(button_styles)
        self.salesrep_button.setStyleSheet(button_styles)
        self.purchase_button.setStyleSheet(button_styles)
        self.po_button.setStyleSheet(button_styles)
        self.grn_button.setStyleSheet(button_styles)
        self.customer_button.setStyleSheet(button_styles)
        self.product_button.setStyleSheet(button_styles)
        self.sales_button.setStyleSheet(button_styles)
        self.employee_button.setStyleSheet(button_styles)
        self.transaction_button.setStyleSheet(button_styles)
        self.purchase_return.setStyleSheet(button_styles)
        self.sales_return.setStyleSheet(button_styles)
        self.expense_button.setStyleSheet(button_styles)
        self.reports_button.setStyleSheet(button_styles)
        # self.holdsales_button.setStyleSheet(button_styles)
        
        

        self.dashboard_button.setCursor(Qt.PointingHandCursor)
        self.business_button.setCursor(Qt.PointingHandCursor)
        self.profile_button.setCursor(Qt.PointingHandCursor)
        self.supplier_button.setCursor(Qt.PointingHandCursor)
        self.salesrep_button.setCursor(Qt.PointingHandCursor)
        self.purchase_button.setCursor(Qt.PointingHandCursor)
        self.po_button.setCursor(Qt.PointingHandCursor)
        self.grn_button.setCursor(Qt.PointingHandCursor)
        self.customer_button.setCursor(Qt.PointingHandCursor)
        self.product_button.setCursor(Qt.PointingHandCursor)
        self.sales_button.setCursor(Qt.PointingHandCursor)
        self.employee_button.setCursor(Qt.PointingHandCursor)
        self.transaction_button.setCursor(Qt.PointingHandCursor)
        self.purchase_return.setCursor(Qt.PointingHandCursor)
        self.sales_return.setCursor(Qt.PointingHandCursor)
        self.expense_button.setCursor(Qt.PointingHandCursor)
        self.reports_button.setCursor(Qt.PointingHandCursor)
        # self.holdsales_button.setCursor(Qt.PointingHandCursor)


        sidebar_layout.addWidget(self.dashboard_button)
        sidebar_layout.addWidget(self.business_button)
        sidebar_layout.addWidget(self.profile_button)
        sidebar_layout.addWidget(self.supplier_button)
        sidebar_layout.addWidget(self.salesrep_button)
        sidebar_layout.addWidget(self.purchase_button)
        sidebar_layout.addWidget(self.po_button)
        sidebar_layout.addWidget(self.grn_button)
        sidebar_layout.addWidget(self.sales_button)
        sidebar_layout.addWidget(self.customer_button)
        sidebar_layout.addWidget(self.product_button)
        sidebar_layout.addWidget(self.employee_button)
        sidebar_layout.addWidget(self.transaction_button)
        sidebar_layout.addWidget(self.purchase_return)
        sidebar_layout.addWidget(self.sales_return)
        sidebar_layout.addWidget(self.expense_button)
        sidebar_layout.addWidget(self.reports_button)
        # sidebar_layout.addWidget(self.holdsales_button)
        
        sidebar_layout.addWidget(footer_button)

        sidebar_layout.addStretch()  # Push buttons to the top

        # Compact sidebar rail buttons with custom SVG icons
        self.rail_dashboard_button = self.create_rail_button("res/rail_icons/dashboard.svg", "Dashboard", "DB")
        self.rail_business_button = self.create_rail_button("res/rail_icons/business.svg", "Business", "BS")
        self.rail_profile_button = self.create_rail_button("res/rail_icons/profile.svg", "Profile", "PF")
        self.rail_supplier_button = self.create_rail_button("res/rail_icons/supplier.svg", "Suppliers", "SP")
        self.rail_salesrep_button = self.create_rail_button("res/rail_icons/salesrep.svg", "Sales Rep", "SR")
        self.rail_purchase_button = self.create_rail_button("res/rail_icons/purchase.svg", "Purchase Invoice", "PI")
        self.rail_po_button = self.create_rail_button("res/rail_icons/po.svg", "Purchase Orders", "PO")
        self.rail_grn_button = self.create_rail_button("res/rail_icons/grn.svg", "Goods Receipt", "GR")
        self.rail_sales_button = self.create_rail_button("res/rail_icons/sales.svg", "Sales", "SL")
        self.rail_customer_button = self.create_rail_button("res/rail_icons/customer.svg", "Customers", "CU")
        self.rail_product_button = self.create_rail_button("res/rail_icons/product.svg", "Product", "PR")
        self.rail_employee_button = self.create_rail_button("res/rail_icons/employee.svg", "Employees", "EM")
        self.rail_transaction_button = self.create_rail_button("res/rail_icons/transaction.svg", "Transactions", "TR")
        self.rail_purchase_return = self.create_rail_button("res/rail_icons/purchase_return.svg", "Purchase Return", "PN")
        self.rail_sales_return = self.create_rail_button("res/rail_icons/sales_return.svg", "Sales Return", "SN")
        self.rail_expense_button = self.create_rail_button("res/rail_icons/expense.svg", "Expenses", "EX")
        self.rail_reports_button = self.create_rail_button("res/rail_icons/reports.svg", "Reports", "RP")

        self.rail_toggle_button = self.create_rail_button("res/rail_icons/ham.svg", "Expand Sidebar", "", variant="toggle")
        self.rail_toggle_button.clicked.connect(self.reopen_sidebar_from_rail)
        rail_toggle_wrap = QWidget()
        rail_toggle_layout = QVBoxLayout(rail_toggle_wrap)
        rail_toggle_layout.setContentsMargins(8, 18, 8, 20)
        rail_toggle_layout.setSpacing(0)
        rail_toggle_layout.addWidget(self.rail_toggle_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(rail_toggle_wrap, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_dashboard_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_business_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_profile_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_supplier_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_salesrep_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_purchase_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_po_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_grn_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_sales_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_customer_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_product_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_employee_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_transaction_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_purchase_return, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_sales_return, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_expense_button, 0, Qt.AlignHCenter)
        rail_layout.addWidget(self.rail_reports_button, 0, Qt.AlignHCenter)
        rail_layout.addStretch()

    
        self.apply_role_permissions()
        self.apply_demo_restrictions()



        
        

        
        
        
        
        


        self.dashboard = BaseDashboardWidget()
        self.welcome = WelcomeWidget()
        
        self.profile = BaseProfileWidget()
        self.business = BaseBusinessWidget()
        self.supplier = BaseSupplierWidget()
        
        self.salesrep = BaseSalesRepWidget()
        self.purchase = BasePurchaseWidget()
        self.po = BasePOWidget()
        self.grn = BaseGRNWidget()
        
        self.base_sales = BaseSalesWidget(controller=self)
        
        self.base_customer = BaseCustomerWidget(controller=self)
        self.product = BaseProductWidget()
        
        
        self.employee = BaseEmployeeWidget()
        self.transaction = BaseTransactionWidget()
        self.purchasereturn = BasePurchaseReturnWidget()
        self.salesreturn = BaseSalesReturnWidget()
        self.expense = BaseExpenseWidget()
        self.reports = BaseReportsWidget()
        
        # self.holdsales = BaseHoldSalesWidget(controller=self)
        
        
        # self.dashboard.sales_page_signal.connect(lambda: self.set_sales(self.base_sales, self.main_content_layout))
        # self.dashboard.product_page_signal.connect(lambda: self.set_product(self.product, self.main_content_layout))
        
        

        self.dashboard_button.clicked.connect(lambda: self.set_dashboard(self.dashboard, self.main_content_layout))
        self.business_button.clicked.connect(lambda: self.set_business(self.business, self.main_content_layout))
        self.profile_button.clicked.connect(lambda: self.set_profile(self.profile, self.main_content_layout))
        self.supplier_button.clicked.connect(lambda: self.set_supplier(self.supplier, self.main_content_layout))
        self.salesrep_button.clicked.connect(lambda: self.set_salesrep(self.salesrep, self.main_content_layout))
        self.purchase_button.clicked.connect(lambda: self.set_purchase(self.purchase, self.main_content_layout))
        self.po_button.clicked.connect(lambda: self.set_po(self.po, self.main_content_layout))
        self.grn_button.clicked.connect(lambda: self.set_grn(self.grn, self.main_content_layout))
        self.sales_button.clicked.connect(lambda:self.set_sales(self.base_sales, self.main_content_layout))
        self.customer_button.clicked.connect(lambda: self.set_customer(self.base_customer, self.main_content_layout))
        self.product_button.clicked.connect(lambda: self.set_product(self.product, self.main_content_layout))
        self.employee_button.clicked.connect(lambda: self.set_employee(self.employee, self.main_content_layout))
        self.transaction_button.clicked.connect(lambda: self.set_transaction(self.transaction, self.main_content_layout))
        self.purchase_return.clicked.connect(lambda: self.set_purchasereturn(self.purchasereturn, self.main_content_layout))
        self.sales_return.clicked.connect(lambda: self.set_salesreturn(self.salesreturn, self.main_content_layout))
        self.expense_button.clicked.connect(lambda: self.set_expense(self.expense, self.main_content_layout))
        self.reports_button.clicked.connect(lambda: self.set_reports(self.reports, self.main_content_layout))
        # self.holdsales_button.clicked.connect(lambda: self.set_holdsales(self.holdsales, self.main_content_layout))

        self.rail_dashboard_button.clicked.connect(lambda: self.set_dashboard(self.dashboard, self.main_content_layout))
        self.rail_business_button.clicked.connect(lambda: self.set_business(self.business, self.main_content_layout))
        self.rail_profile_button.clicked.connect(lambda: self.set_profile(self.profile, self.main_content_layout))
        self.rail_supplier_button.clicked.connect(lambda: self.set_supplier(self.supplier, self.main_content_layout))
        self.rail_salesrep_button.clicked.connect(lambda: self.set_salesrep(self.salesrep, self.main_content_layout))
        self.rail_purchase_button.clicked.connect(lambda: self.set_purchase(self.purchase, self.main_content_layout))
        self.rail_po_button.clicked.connect(lambda: self.set_po(self.po, self.main_content_layout))
        self.rail_grn_button.clicked.connect(lambda: self.set_grn(self.grn, self.main_content_layout))
        self.rail_sales_button.clicked.connect(lambda: self.set_sales(self.base_sales, self.main_content_layout))
        self.rail_customer_button.clicked.connect(lambda: self.set_customer(self.base_customer, self.main_content_layout))
        self.rail_product_button.clicked.connect(lambda: self.set_product(self.product, self.main_content_layout))
        self.rail_employee_button.clicked.connect(lambda: self.set_employee(self.employee, self.main_content_layout))
        self.rail_transaction_button.clicked.connect(lambda: self.set_transaction(self.transaction, self.main_content_layout))
        self.rail_purchase_return.clicked.connect(lambda: self.set_purchasereturn(self.purchasereturn, self.main_content_layout))
        self.rail_sales_return.clicked.connect(lambda: self.set_salesreturn(self.salesreturn, self.main_content_layout))
        self.rail_expense_button.clicked.connect(lambda: self.set_expense(self.expense, self.main_content_layout))
        self.rail_reports_button.clicked.connect(lambda: self.set_reports(self.reports, self.main_content_layout))
        
        
        
        from PySide6.QtGui import QKeySequence, QShortcut

        
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self.set_dashboard(self.dashboard, self.main_content_layout))  # Dashboard
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self.set_profile(self.profile, self.main_content_layout))  # Profile
        QShortcut(QKeySequence("Ctrl+3"), self, activated=lambda: self.set_supplier(self.supplier, self.main_content_layout))  # Supplier
        QShortcut(QKeySequence("Ctrl+4"), self, activated=lambda: self.set_salesrep(self.salesrep, self.main_content_layout))  # Sales Rep
        QShortcut(QKeySequence("Ctrl+5"), self, activated=lambda: self.set_purchase(self.purchase, self.main_content_layout))  # Purchase
        QShortcut(QKeySequence("Ctrl+6"), self, activated=lambda: self.set_sales(self.base_sales, self.main_content_layout))  # Sales
        QShortcut(QKeySequence("Ctrl+7"), self, activated=lambda: self.set_customer(self.base_customer, self.main_content_layout))  # Customer
        QShortcut(QKeySequence("Ctrl+8"), self, activated=lambda: self.set_product(self.product, self.main_content_layout))  # Product
        QShortcut(QKeySequence("Ctrl+9"), self, activated=lambda: self.set_employee(self.employee, self.main_content_layout))  # Employee
        QShortcut(QKeySequence("Ctrl+0"), self, activated=lambda: self.set_transaction(self.transaction, self.main_content_layout))  # Transaction
        QShortcut(QKeySequence("Alt+Left"), self, activated=self.go_back)
        QShortcut(QKeySequence("Alt+Right"), self, activated=self.go_forward)
        # QShortcut(QKeySequence("Ctrl+P"), self, activated=lambda: self.set_purchasereturn(self.purchasereturn, self.main_content_layout))  # Purchase Return
        # QShortcut(QKeySequence("Ctrl+S"), self, activated=lambda: self.set_salesreturn(self.salesreturn, self.main_content_layout))  # Sales Return
        # QShortcut(QKeySequence("Ctrl+E"), self, activated=lambda: self.set_expense(self.expense, self.main_content_layout))  # Expense
        # QShortcut(QKeySequence("Ctrl+R"), self, activated=lambda: self.set_reports(self.reports, self.main_content_layout))  # Reports
        # QShortcut(QKeySequence("Ctrl+H"), self, activated=lambda: self.set_holdsales(self.holdsales, self.main_content_layout))  # On-Hold Sales
        
        
        if Permissions.has_permission("dashboard"):
            self.main_content_layout.addWidget(self.dashboard)
        else:
            self.main_content_layout.addWidget(self.welcome)
        
        
        self.main_content_layout.addWidget(self.business)
        self.main_content_layout.addWidget(self.profile)
        self.main_content_layout.addWidget(self.supplier)
        self.main_content_layout.addWidget(self.salesrep)
        self.main_content_layout.addWidget(self.purchase)
        self.main_content_layout.addWidget(self.po)
        self.main_content_layout.addWidget(self.grn)
        self.main_content_layout.addWidget(self.base_sales)
        self.main_content_layout.addWidget(self.base_customer)
        self.main_content_layout.addWidget(self.product)
        self.main_content_layout.addWidget(self.employee)
        self.main_content_layout.addWidget(self.transaction)
        self.main_content_layout.addWidget(self.purchasereturn)
        self.main_content_layout.addWidget(self.salesreturn)
        self.main_content_layout.addWidget(self.expense)
        self.main_content_layout.addWidget(self.reports)
        # self.main_content_layout.addWidget(self.holdsales)
        

        
        
        
        # making all widgets focusable
        self.make_all_focusable(self)

        
        self.layout.addWidget(self.sidebar_scroll)
        self.layout.addWidget(self.sidebar_rail_scroll)
        self.layout.addWidget(content_area_widget)

        self.register_nested_history_tracking()
        self.main_content_layout.currentChanged.connect(self.on_main_page_changed)
        QTimer.singleShot(0, self.initialize_navigation_history)
        
        
        
    def _build_window_title(self):
        if not self.demo_mode:
            return 'ProCure Medical - Login'

        if self.demo_days_remaining is None:
            return 'ProCure Medical - Demo'

        day_label = "day" if self.demo_days_remaining == 1 else "days"
        return f'ProCure Medical - Demo ({self.demo_days_remaining} {day_label} left)'

    def apply_demo_restrictions(self):
        if not self.demo_mode:
            return

        demo_tooltip = "Reports are unavailable in the 15-day demo."
        self.reports_button.setEnabled(False)
        self.rail_reports_button.setEnabled(False)
        self.reports_button.setToolTip(demo_tooltip)
        self.rail_reports_button.setToolTip(demo_tooltip)

        
        
    
    
    
    
    
    def set_business_name(self):
        
        query = QSqlQuery()
        query.prepare("SELECT businessname FROM business WHERE id = ?")
        query.addBindValue(1)

        if not query.exec():
            print("Error While Fetching Business", query.lastError().text())
            return False

        if query.next():
            
            businessname = query.value(0)
            return businessname
        
        
        

    
    def logout(self):
        # Ask confirmation (optional)
        _, accepted = AppMessageBox.confirm(
            self,
            "Logout Confirmation",
            "Are you sure you want to logout?",
            confirm_label="Logout",
            cancel_label="Stay Logged In",
            kind="warning",
        )

        if accepted:
            app = QApplication.instance()
            log_activity(
                category="login",
                action="logout",
                entity_type="user",
                entity_id=app.property("user_id"),
                note=f"{app.property('username') or ''} signed out of the system."
            )
            app.setProperty("user_id", None)
            app.setProperty("username", None)
            app.setProperty("login_session_id", None)

            from starting import AuthWindow

            login_window = AuthWindow()
            app.setProperty("login_window", login_window)
            login_window.show()
            self.close()
            
            
    
    
    
    def make_all_focusable(self, widget):
        """Make all widgets tabbable + labels selectable globally."""
        for child in widget.findChildren(QWidget):
            child.setFocusPolicy(Qt.StrongFocus)

            # Special case: QLabel → make text selectable
            if isinstance(child, QLabel):
                child.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
                child.setStyleSheet("QLabel:focus { background: #e6f2ff; }")

            # Special case: QTableWidget → fix Tab key trapping
            if isinstance(child, QTableWidget):
                child.setTabKeyNavigation(False)  # allow leaving with Tab
                child.installEventFilter(self)   # optional: catch Tab manually

    
    
    
    
    #### Hide Sideber on Hover Remove
    
    # def eventFilter(self, obj, event):

    #     if obj is self.sidebar_scroll and event.type() == QEvent.HoverLeave:
    #         print("Hover left sidebar — hiding")
    #         self.hide_sidebar(obj)
     
        
    #     return super().eventFilter(obj, event)

    
    
    
    
    
    
    @permission.require_permission('dashboard')
    def set_dashboard(self, widget, layout):
        self.navigate_to_page(widget, layout)

    def _require_any_permission(self, permission_names, label):
        if any(Permissions.has_permission(name) for name in permission_names):
            return True

        AppMessageBox.critical(
            self,
            "Not Authorized",
            f"You do not have permission to access {label}.",
        )
        return False
        
    def set_business(self, widget, layout):
        if not self._require_any_permission(("business.view", "business.update"), "Business"):
            return
        self.business.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_profile(self, widget, layout):
        if not self._require_any_permission(
            ("profile.view", "profile.update", "users.view", "users.create"),
            "Profile",
        ):
            return
        self.profile.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_supplier(self, widget, layout):
        if not self._require_any_permission(("supplier.view", "supplier.create"), "Suppliers"):
            return
        self.supplier.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_salesrep(self, widget, layout):
        if not self._require_any_permission(("rep.view", "rep.create"), "Sales Reps"):
            return
        self.salesrep.reset_to_default()
        self.navigate_to_page(widget, layout)
    
    def set_purchase(self, widget, layout):
        if not self._require_any_permission(("purchase.view", "purchase.create"), "Purchases"):
            return
        self.purchase.reset_to_default()
        self.navigate_to_page(widget, layout)
    
    def set_po(self, widget, layout):
        if not self._require_any_permission(("po.view", "po.create"), "Purchase Orders"):
            return
        self.po.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_grn(self, widget, layout):
        if not self._require_any_permission(("grn.view", "grn.create"), "GRN"):
            return
        self.grn.reset_to_default()
        self.navigate_to_page(widget, layout)
    
    def set_sales(self, widget, layout):
        if not self._require_any_permission(("sales.view", "sales.create"), "Sales"):
            return
        self.base_sales.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_customer(self, widget, layout):
        if not self._require_any_permission(("customer.view", "customer.create"), "Customers"):
            return
        self.base_customer.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_product(self, widget, layout):
        if not self._require_any_permission(("product.view", "product.create"), "Products"):
            return
        self.product.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_employee(self, widget, layout):
        if not self._require_any_permission(("employee.view", "employee.create"), "Employees"):
            return
        self.employee.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_transaction(self, widget, layout):
        if not self._require_any_permission(("transactions.view", "transactions.create"), "Transactions"):
            return
        self.transaction.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_purchasereturn(self, widget, layout):
        if not self._require_any_permission(
            ("purchasereturn.view", "purchasereturn.create"),
            "Purchase Returns",
        ):
            return
        self.purchasereturn.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_salesreturn(self, widget, layout):
        if not self._require_any_permission(
            ("salesreturn.view", "salesreturn.create"),
            "Sales Returns",
        ):
            return
        self.salesreturn.reset_to_default()
        self.navigate_to_page(widget, layout)


    def set_expense(self, widget, layout):
        if not self._require_any_permission(("expense.view", "expense.create"), "Expenses"):
            return
        self.expense.reset_to_default()
        self.navigate_to_page(widget, layout)
    
        
    def set_reports(self, widget, layout):
        if self.demo_mode:
            AppMessageBox.warning(
                self,
                "Demo Restriction",
                "Reports are disabled in the 15-day demo. Install a full license to unlock them.",
            )
            return
        if not self._require_any_permission(("reports.view",), "Reports"):
            return
        self.navigate_to_page(widget, layout)

    def navigate_to_page(self, widget, layout):
        if layout is not self.main_content_layout:
            layout.setCurrentWidget(widget)
            return

        if self.main_content_layout.currentWidget() is widget:
            return

        self.main_content_layout.setCurrentWidget(widget)

    def initialize_navigation_history(self):
        current_state = self.capture_navigation_state()
        if current_state is None:
            self.history = []
            self.current_index = -1
            self.update_nav_buttons()
            return

        self.history = [current_state]
        self.current_index = 0
        self.update_nav_buttons()

    def on_main_page_changed(self, index):
        if self._is_history_navigation:
            return

        widget = self.main_content_layout.widget(index)
        if widget is None:
            return

        self.record_history_state(self.capture_navigation_state(widget))

    def register_nested_history_tracking(self):
        history_widgets = [
            self.dashboard,
            self.business,
            self.profile,
            self.supplier,
            self.salesrep,
            self.purchase,
            self.po,
            self.grn,
            self.base_sales,
            self.base_customer,
            self.product,
            self.employee,
            self.transaction,
            self.purchasereturn,
            self.salesreturn,
            self.expense,
            self.reports,
        ]

        for owner in history_widgets:
            nested_layout = getattr(owner, "stacked_layout", None)
            if nested_layout is None:
                continue
            nested_layout.currentChanged.connect(
                lambda _index, owner=owner: self.on_nested_page_changed(owner)
            )

    def on_nested_page_changed(self, owner):
        if self._is_history_navigation:
            return

        if self.main_content_layout.currentWidget() is not owner:
            return

        self.record_history_state(self.capture_navigation_state(owner))

    def capture_navigation_state(self, main_widget=None):
        if main_widget is None:
            main_widget = self.main_content_layout.currentWidget()

        if main_widget is None:
            return None

        nested_widget = None
        nested_layout = getattr(main_widget, "stacked_layout", None)
        if nested_layout is not None:
            nested_widget = nested_layout.currentWidget()

        return (main_widget, nested_widget)

    def record_history_state(self, state):
        if state is None:
            return

        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]

        if self.history:
            last_main, last_nested = self.history[-1]
            current_main, current_nested = state
            if last_main is current_main and last_nested is current_nested:
                self.update_nav_buttons()
                return

        self.history.append(state)
        self.current_index = len(self.history) - 1
        self.update_nav_buttons()

    def restore_navigation_state(self, state):
        if state is None:
            return

        main_widget, nested_widget = state

        self._is_history_navigation = True
        try:
            self.main_content_layout.setCurrentWidget(main_widget)

            nested_layout = getattr(main_widget, "stacked_layout", None)
            if nested_layout is not None and nested_widget is not None:
                nested_layout.setCurrentWidget(nested_widget)
        finally:
            self._is_history_navigation = False

        self.update_nav_buttons()

    def update_nav_buttons(self):
        can_go_back = self.current_index > 0
        can_go_forward = self.current_index >= 0 and self.current_index < len(self.history) - 1

        self.back_nav_btn.setEnabled(can_go_back)
        self.forward_nav_btn.setEnabled(can_go_forward)

    def go_back(self):
        if self.current_index <= 0:
            return

        self.current_index -= 1
        target = self.history[self.current_index]
        self.restore_navigation_state(target)

    def go_forward(self):
        if self.current_index < 0 or self.current_index >= len(self.history) - 1:
            return

        self.current_index += 1
        target = self.history[self.current_index]
        self.restore_navigation_state(target)
    
    
    # def set_holdsales(self, widget, layout):
    #     layout.setCurrentWidget(widget)
    
 
    # Function to toggle sidebar visibility
    # This function is called when the hamburger button is toggled
    # It shows the sidebar when the button is checked and hides it when unchecked   
    
    
    
    def apply_role_permissions(self):
        permission_to_buttons = {
            "dashboard": (self.dashboard_button, self.rail_dashboard_button),
            "business.view": (self.business_button, self.rail_business_button),
            "profile.view": (self.profile_button, self.rail_profile_button),
            "supplier.view": (self.supplier_button, self.rail_supplier_button),
            "rep.view": (self.salesrep_button, self.rail_salesrep_button),
            "purchase.view": (self.purchase_button, self.rail_purchase_button),
            "po.view": (self.po_button, self.rail_po_button),
            "grn.view": (self.grn_button, self.rail_grn_button),
            "sales.view": (self.sales_button, self.rail_sales_button),
            "customer.view": (self.customer_button, self.rail_customer_button),
            "product.view": (self.product_button, self.rail_product_button),
            "employee.view": (self.employee_button, self.rail_employee_button),
            "transactions.view": (self.transaction_button, self.rail_transaction_button),
            "purchasereturn.view": (self.purchase_return, self.rail_purchase_return),
            "salesreturn.view": (self.sales_return, self.rail_sales_return),
            "expense.view": (self.expense_button, self.rail_expense_button),
            "reports.view": (self.reports_button, self.rail_reports_button),
        }

        for permission_name, buttons in permission_to_buttons.items():
            if Permissions.has_permission(permission_name):
                continue

            for btn in buttons:
                btn.hide()
            
            



    def expand_sidebar(self):
        self.sidebar_rail_scroll.hide()
        self.sidebar_rail_scroll.setMinimumWidth(0)
        self.sidebar_rail_scroll.setMaximumWidth(0)
        self.ham_button.show()

        self.sidebar_scroll.setMinimumWidth(210)
        self.sidebar_scroll.setMaximumWidth(210)
        self.sidebar_scroll.show()
        self.sidebar_scroll.raise_()

        self.layout.invalidate()
        self.layout.activate()
        self.widget.updateGeometry()
        self.widget.update()

    def collapse_sidebar(self):
        self.sidebar_scroll.hide()
        self.sidebar_scroll.setMinimumWidth(0)
        self.sidebar_scroll.setMaximumWidth(0)

        self.sidebar_rail_scroll.setMinimumWidth(self.sidebar_rail_width)
        self.sidebar_rail_scroll.setMaximumWidth(self.sidebar_rail_width)
        self.sidebar_rail_scroll.show()
        self.sidebar_rail_scroll.raise_()
        self.ham_button.hide()

        self.layout.invalidate()
        self.layout.activate()
        self.widget.updateGeometry()
        self.widget.update()



    def hide_sidebar(self, sidebar):
        
        sidebar.hide()

    def _load_icon(self, primary_relative_path, fallback_relative_path=None):
        icon = QIcon(resource_path(primary_relative_path))
        if icon.isNull() and fallback_relative_path:
            icon = QIcon(QPixmap(resource_path(fallback_relative_path)))
        return icon

    def collapse_sidebar_from_header(self):
        self.collapse_sidebar()

    def reopen_sidebar_from_rail(self):
        self.expand_sidebar()

    def create_rail_button(self, icon_relative_path, tooltip, fallback_text="", variant="nav"):
        btn = QPushButton("")
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(36, 36)
        icon = QIcon(resource_path(icon_relative_path))
        if not icon.isNull():
            btn.setIcon(icon)
            btn.setIconSize(QSize(20, 20))
        else:
            btn.setText(fallback_text)
        if variant == "toggle":
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3E6B89;
                    color: #fffff0;
                    border: 1px solid #5f86a2;
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #4a7b9b;
                    border: 1px solid #c6d9e7;
                    color: #ffffff;
                }
                QPushButton:pressed {
                    background-color: #2a5672;
                    border: 1px solid #7fa5bf;
                    color: #ffffff;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2F5D7C;
                    color: #fffff0;
                    border: 1px solid #2b5876;
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #46779b;
                    border: 1px solid #a8c8de;
                    color: #ffffff;
                }
                QPushButton:pressed {
                    background-color: #224b69;
                    border: 1px solid #6f98b6;
                    color: #ffffff;
                }
            """)
        return btn
        
        
    
    
    def reset_widget_size(self, layout, widget):
        
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        widget.setMinimumSize(0, 0)
        widget.setMaximumSize(16777215, 16777215)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)



class SelectAllLineEditFilter(QObject):
    def eventFilter(self, obj, event):
        if isinstance(obj, QLineEdit) and event.type() == QEvent.FocusIn:
            QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)
    




    
if __name__ == '__main__':

    app = QApplication(sys.argv)

    select_all_filter = SelectAllLineEditFilter()
    app.installEventFilter(select_all_filter)


    style = ""
    for css_file in css_files:
        path = resource_path(css_file)
        with open(path, "r") as f:
            style += f.read() + "\n"

    app.setStyleSheet(style)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
