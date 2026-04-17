
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget,QTableWidget, QMainWindow,QMessageBox, QPushButton, QHBoxLayout, QVBoxLayout, QStackedLayout, QLabel, QSizePolicy, QGraphicsOpacityEffect
from PySide6.QtCore import QSize, Qt, QEvent, Signal, QObject, QTimer, QStringListModel, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import QScrollArea
from utilities.sidebarbutton import SideBarButton
from utilities.activity_logger import log_activity

from utilities.database import SQLiteConnectionManager
# from database import PostgresConnectionManager
from PySide6.QtGui import QPalette, QColor, QPixmap, QIcon, QPainter
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
from utilities.stylus import load_stylesheets
from utilities.app_theme import get_theme_palette



permission = Permissions()


import sys
import os
from pathlib import Path
from utilities.app_messagebox import AppMessageBox


def resource_path(relative_path):
    """Return the absolute path to a resource, works for dev and PyInstaller."""
    relative = Path(relative_path)
    candidates = []

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / relative)

    module_root = Path(__file__).resolve().parent.parent
    candidates.append(module_root / relative)
    candidates.append(Path.cwd() / relative)

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return str(candidates[0])



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
        self.sidebar_expanded_width = 248
        self.sidebar_collapsed_width = 60
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setFixedWidth(self.sidebar_expanded_width)
        self.sidebar_scroll.setMinimumWidth(self.sidebar_expanded_width)
        self.sidebar_scroll.setMaximumWidth(self.sidebar_expanded_width)
        self.sidebar_scroll.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.sidebar_scroll.setStyleSheet(""" 
                                    background-color: #163B5C;

                                    QScrollArea {
                                        background-color: #163B5C;
                                        border: none;
                                    }
                                    QScrollArea > QWidget > QWidget {
                                        background-color: #163B5C;
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
        self.sidebar_collapsed = False

        # COMPACT SIDEBAR RAIL (icon-like navigation, VS Code style)
        self.sidebar_rail_width = self.sidebar_collapsed_width
        self.sidebar_rail_scroll = QScrollArea()
        self.sidebar_rail_scroll.setFixedWidth(self.sidebar_rail_width)
        self.sidebar_rail_scroll.setMinimumWidth(self.sidebar_rail_width)
        self.sidebar_rail_scroll.setMaximumWidth(self.sidebar_rail_width)
        self.sidebar_rail_scroll.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.sidebar_rail_scroll.setWidgetResizable(True)
        self.sidebar_rail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar_rail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar_rail_scroll.setStyleSheet("""
                                    background-color: #163B5C;

                                    QScrollArea {
                                        background-color: #163B5C;
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
        self.sidebar_rail_scroll.setMinimumWidth(0)
        self.sidebar_rail_scroll.setMaximumWidth(0)
        self.sidebar_rail_scroll.setFixedWidth(0)
    
        # SIDE-BAR WIDGET
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)

        self.reset_widget_size(sidebar_layout, sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)


        sidebar_widget.setLayout(sidebar_layout)
        self.sidebar_scroll.setWidget(sidebar_widget)

        self.sidebar_panel = QWidget()
        self.sidebar_panel.setObjectName("SidebarPanel")
        self.sidebar_panel.setStyleSheet("""
            QWidget#SidebarPanel {
                background-color: #163B5C;
                border: 1px solid #244A62;
                border-radius: 0px;
            }
        """)
        self.sidebar_panel_layout = QVBoxLayout(self.sidebar_panel)
        self.sidebar_panel_layout.setContentsMargins(14, 14, 14, 14)
        self.sidebar_panel_layout.setSpacing(10)
        sidebar_layout.addWidget(self.sidebar_panel)

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
        self.content_area_widget = content_area_widget
        content_area_widget.setStyleSheet("background-color: #fff;")
        content_area_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        content_area_layout = QVBoxLayout()
        self.reset_widget_size(content_area_layout, content_area_widget)
        
        
        
        
        
        
        # HEADER WIDGET
        self.header_widget = QWidget()
        header_layout = QHBoxLayout()

        self.reset_widget_size(header_layout, self.header_widget)
        
        self.header_widget.setFixedHeight(58)
        header_layout.setContentsMargins(16,4,16,4)
        header_layout.setSpacing(6)
        header_layout.setAlignment(Qt.AlignVCenter)

        self.header_widget.setLayout(header_layout)
        self.header_widget.setStyleSheet("""
            background-color: #163B5C;
            color: #F4F8FB;
            border-bottom: 1px solid #244A62;
        """)
        
        
        self.ham_button = QPushButton()
        self.ham_button.setCursor(Qt.PointingHandCursor)
        self.ham_button.setObjectName("HeaderControlButton")
        self.ham_button.setFixedSize(32, 32)
        self.ham_button.setIconSize(QSize(18, 18))

        self.ham_menu_icon = self._load_icon("res/rail_icons/ham.svg", "res/ham.png")
        self.ham_close_icon = self._load_icon("res/rail_icons/ham_close.svg")
        self.ham_button.setIcon(self.ham_close_icon if not self.ham_close_icon.isNull() else self.ham_menu_icon)
        
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
            font-size: 17px;
            margin-left: 0px;
            font-weight: 700;
        """)
        
        header_layout.addWidget(business_title, 0, Qt.AlignVCenter)

        self.back_nav_btn = QPushButton()
        self.back_nav_btn.setToolTip("Previous page")
        self.back_nav_btn.setCursor(Qt.PointingHandCursor)
        self.back_nav_btn.setObjectName("HeaderControlButton")
        self.back_nav_btn.setFixedSize(32, 32)
        self.back_nav_btn.setIconSize(QSize(14, 14))
        self.back_nav_icon = self._load_icon("res/rail_icons/nav_back.svg")
        if not self._icon_can_render(self.back_nav_icon, QSize(14, 14)):
            self.back_nav_btn.setText("<")
        else:
            self.back_nav_btn.setIcon(self.back_nav_icon)
        self.back_nav_btn.clicked.connect(self.go_back)

        self.forward_nav_btn = QPushButton()
        self.forward_nav_btn.setToolTip("Next page")
        self.forward_nav_btn.setCursor(Qt.PointingHandCursor)
        self.forward_nav_btn.setObjectName("HeaderControlButton")
        self.forward_nav_btn.setFixedSize(32, 32)
        self.forward_nav_btn.setIconSize(QSize(14, 14))
        self.forward_nav_icon = self._load_icon("res/rail_icons/nav_forward.svg")
        if not self._icon_can_render(self.forward_nav_icon, QSize(14, 14)):
            self.forward_nav_btn.setText(">")
        else:
            self.forward_nav_btn.setIcon(self.forward_nav_icon)
        self.forward_nav_btn.clicked.connect(self.go_forward)

        header_layout.addSpacing(10)
        header_layout.addWidget(self.back_nav_btn, 0, Qt.AlignVCenter)
        header_layout.addSpacing(6)
        header_layout.addWidget(self.forward_nav_btn, 0, Qt.AlignVCenter)
        
        
        
        
        
       
        header_layout.addStretch()
        
        logout_button = QPushButton("Logout")
        logout_button.setObjectName("HeaderPrimaryButton")
        logout_button.setFixedHeight(26)
        logout_button.setMinimumWidth(66)
        logout_button.setContentsMargins(0, 0, 20, 0)
        logout_button.clicked.connect(self.logout)
        
        header_layout.addWidget(logout_button)
        
        
        
        
        content_area_layout.addWidget(self.header_widget)
        
        content_area_widget.setLayout(content_area_layout)
        
        
        # MAIN CONTENT SCROLL
        main_content_scroll = QScrollArea()
        main_content_scroll.setWidgetResizable(True)
        main_content_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        
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
        
        
        
        
        

        self.sidebar_header = QWidget()
        self.sidebar_header_layout = QHBoxLayout(self.sidebar_header)
        self.sidebar_header_layout.setContentsMargins(4, 2, 4, 2)
        self.sidebar_header_layout.setSpacing(8)

        self.sidebar_brand_mark = QLabel("")
        self.sidebar_brand_mark.setAlignment(Qt.AlignCenter)
        self.sidebar_brand_mark.setFixedSize(136, 32)
        self._apply_sidebar_brand_logo()

        self.sidebar_toggle_button = QPushButton()
        self.sidebar_toggle_button.setObjectName("HeaderControlButton")
        self.sidebar_toggle_button.setCursor(Qt.PointingHandCursor)
        self.sidebar_toggle_button.setFixedSize(30, 30)
        self.sidebar_toggle_button.setIconSize(QSize(16, 16))
        self.sidebar_toggle_button.clicked.connect(self.collapse_sidebar_from_header)

        self.sidebar_header_layout.addWidget(self.sidebar_brand_mark)
        self.sidebar_header_spacer = QWidget()
        self.sidebar_header_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.sidebar_header_layout.addWidget(self.sidebar_header_spacer, 1)
        self.sidebar_header_layout.addWidget(self.sidebar_toggle_button, 0, Qt.AlignRight)
        self.sidebar_panel_layout.addWidget(self.sidebar_header)

        self.sidebar_search_edit = None
        self.sidebar_search_wrap = QWidget()
        self.sidebar_search_wrap.setObjectName("SidebarSearchWrap")
        self.sidebar_search_wrap.setFixedHeight(44)
        self.sidebar_search_wrap.setStyleSheet("""
            QWidget#SidebarSearchWrap {
                background-color: transparent;
                border: none;
            }
        """)
        self.sidebar_panel_layout.addWidget(self.sidebar_search_wrap)

        self.sidebar_nav_wrap = QWidget()
        self.sidebar_nav_layout = QVBoxLayout(self.sidebar_nav_wrap)
        self.sidebar_nav_layout.setContentsMargins(0, 6, 0, 0)
        self.sidebar_nav_layout.setSpacing(2)
        self.sidebar_panel_layout.addWidget(self.sidebar_nav_wrap, 1)

        self.dashboard_button = SideBarButton('Dashboard')
        self.business_button = SideBarButton('Business')
        self.profile_button = SideBarButton('Profile')
        self.supplier_button = SideBarButton('Suppliers')
        self.salesrep_button = SideBarButton('Sales Rep')
        self.purchase_button = SideBarButton('Purchase Invoice')
        self.po_button = SideBarButton('Purchase Orders')
        self.grn_button = SideBarButton('Goods Receipt')
        self.sales_button = SideBarButton('Sales Invoice')
        self.customer_button = SideBarButton('Customers')
        self.product_button = SideBarButton('Product')
        self.employee_button = SideBarButton('Employees')
        self.transaction_button = SideBarButton('Transactions')
        self.purchase_return = SideBarButton('Purchase Return')
        self.sales_return = SideBarButton('Sales Return')
        self.expense_button = SideBarButton('Expenses')
        self.reports_button = SideBarButton('Reports')
        # self.holdsales_button = SideBarButton('On-Hold Sales')

        # SideBarButton now owns its active/hover/collapsed styles internally.
        
        

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


        self.sidebar_nav_layout.addWidget(self.dashboard_button)
        self.sidebar_nav_layout.addWidget(self.business_button)
        self.sidebar_nav_layout.addWidget(self.profile_button)
        self.sidebar_nav_layout.addWidget(self.supplier_button)
        self.sidebar_nav_layout.addWidget(self.salesrep_button)
        self.sidebar_nav_layout.addWidget(self.purchase_button)
        self.sidebar_nav_layout.addWidget(self.po_button)
        self.sidebar_nav_layout.addWidget(self.grn_button)
        self.sidebar_nav_layout.addWidget(self.sales_button)
        self.sidebar_nav_layout.addWidget(self.customer_button)
        self.sidebar_nav_layout.addWidget(self.product_button)
        self.sidebar_nav_layout.addWidget(self.employee_button)
        self.sidebar_nav_layout.addWidget(self.transaction_button)
        self.sidebar_nav_layout.addWidget(self.purchase_return)
        self.sidebar_nav_layout.addWidget(self.sales_return)
        self.sidebar_nav_layout.addWidget(self.expense_button)
        self.sidebar_nav_layout.addWidget(self.reports_button)
        # sidebar_layout.addWidget(self.holdsales_button)

        self.sidebar_footer = QWidget()
        self.sidebar_footer.setObjectName("SidebarFooter")
        self.sidebar_footer.setStyleSheet("""
            QWidget#SidebarFooter {
                background-color: #163B5C;
                border: 1px solid #244A62;
                border-radius: 16px;
            }
        """)
        self.sidebar_footer_layout = QHBoxLayout(self.sidebar_footer)
        self.sidebar_footer_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_footer_layout.setSpacing(10)

        self.sidebar_avatar = QLabel("JD")
        self.sidebar_avatar.setAlignment(Qt.AlignCenter)
        self.sidebar_avatar.setFixedSize(34, 34)
        self.sidebar_avatar.setStyleSheet("""
            background-color: #6DB6FF;
            color: #131121;
            border-radius: 10px;
            font-family: montserrat;
            font-size: 11px;
            font-weight: 800;
        """)

        self.sidebar_profile_text_wrap = QWidget()
        self.sidebar_profile_text_layout = QVBoxLayout(self.sidebar_profile_text_wrap)
        self.sidebar_profile_text_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_profile_text_layout.setSpacing(0)

        self.sidebar_profile_name = QLabel("User")
        self.sidebar_profile_name.setStyleSheet("""
            color: #F8F6F1;
            font-family: montserrat;
            font-size: 11px;
            font-weight: 700;
        """)
        self.sidebar_profile_role = QLabel("Active session")
        self.sidebar_profile_role.setStyleSheet("""
            color: #9088AB;
            font-family: montserrat;
            font-size: 10px;
            font-weight: 600;
        """)
        self.sidebar_profile_text_layout.addWidget(self.sidebar_profile_name)
        self.sidebar_profile_text_layout.addWidget(self.sidebar_profile_role)

        self.sidebar_footer_action = QPushButton("↪")
        self.sidebar_footer_action.setCursor(Qt.PointingHandCursor)
        self.sidebar_footer_action.setFixedSize(26, 26)
        self.sidebar_footer_action.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #B6B0CC;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """)
        self.sidebar_footer_layout.addWidget(self.sidebar_avatar)
        self.sidebar_footer_layout.addWidget(self.sidebar_profile_text_wrap, 1)
        self.sidebar_footer_action.hide()
        self.sidebar_panel_layout.addWidget(self.sidebar_footer)

        # Mini sidebar (rail) removed.
        self.rail_dashboard_button = None
        self.rail_business_button = None
        self.rail_profile_button = None
        self.rail_supplier_button = None
        self.rail_salesrep_button = None
        self.rail_purchase_button = None
        self.rail_po_button = None
        self.rail_grn_button = None
        self.rail_sales_button = None
        self.rail_customer_button = None
        self.rail_product_button = None
        self.rail_employee_button = None
        self.rail_transaction_button = None
        self.rail_purchase_return = None
        self.rail_sales_return = None
        self.rail_expense_button = None
        self.rail_reports_button = None
        self.rail_toggle_button = None

        self.main_sidebar_buttons = [
            self.dashboard_button,
            self.business_button,
            self.profile_button,
            self.supplier_button,
            self.salesrep_button,
            self.purchase_button,
            self.po_button,
            self.grn_button,
            self.sales_button,
            self.customer_button,
            self.product_button,
            self.employee_button,
            self.transaction_button,
            self.purchase_return,
            self.sales_return,
            self.expense_button,
            self.reports_button,
        ]

        self.main_sidebar_icon_map = {
            self.dashboard_button: "res/rail_icons/dashboard.svg",
            self.business_button: "res/rail_icons/business.svg",
            self.profile_button: "res/rail_icons/profile.svg",
            self.supplier_button: "res/rail_icons/supplier.svg",
            self.salesrep_button: "res/rail_icons/salesrep.svg",
            self.purchase_button: "res/rail_icons/purchase.svg",
            self.po_button: "res/rail_icons/po.svg",
            self.grn_button: "res/rail_icons/grn.svg",
            self.sales_button: "res/rail_icons/sales.svg",
            self.customer_button: "res/rail_icons/customer.svg",
            self.product_button: "res/rail_icons/product.svg",
            self.employee_button: "res/rail_icons/employee.svg",
            self.transaction_button: "res/rail_icons/transaction.svg",
            self.purchase_return: "res/rail_icons/purchase_return.svg",
            self.sales_return: "res/rail_icons/sales_return.svg",
            self.expense_button: "res/rail_icons/expense.svg",
            self.reports_button: "res/rail_icons/reports.svg",
        }

        self._configure_main_sidebar_icons()
        self._refresh_sidebar_profile()
        if self.sidebar_search_edit is not None:
            self.sidebar_search_edit.textChanged.connect(self._filter_sidebar_buttons)
        self.refresh_theme()

        self.rail_nav_buttons = []

    
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

        self.widget_sidebar_map = {
            self.dashboard: (self.dashboard_button, None),
            self.business: (self.business_button, None),
            self.profile: (self.profile_button, None),
            self.supplier: (self.supplier_button, None),
            self.salesrep: (self.salesrep_button, None),
            self.purchase: (self.purchase_button, None),
            self.po: (self.po_button, None),
            self.grn: (self.grn_button, None),
            self.base_sales: (self.sales_button, None),
            self.base_customer: (self.customer_button, None),
            self.product: (self.product_button, None),
            self.employee: (self.employee_button, None),
            self.transaction: (self.transaction_button, None),
            self.purchasereturn: (self.purchase_return, None),
            self.salesreturn: (self.sales_return, None),
            self.expense: (self.expense_button, None),
            self.reports: (self.reports_button, None),
        }

        self._set_sidebar_collapsed(False)
        self._set_active_sidebar_by_widget(self.main_content_layout.currentWidget())
        

        
        
        
        # making all widgets focusable
        self.make_all_focusable(self)

        
        self.layout.addWidget(self.sidebar_scroll, 0)
        self.layout.addWidget(content_area_widget, 1)
        self.layout.setStretch(0, 0)
        self.layout.setStretch(1, 1)

        self.register_nested_history_tracking()
        self.main_content_layout.currentChanged.connect(self.on_main_page_changed)
        QTimer.singleShot(0, self.initialize_navigation_history)
        QTimer.singleShot(0, self._sync_shell_layout)
        
        
        
    def _build_window_title(self):
        if not self.demo_mode:
            return 'ProCure Medical - Login'

        if self.demo_days_remaining is None:
            return 'ProCure Medical - Demo'

        day_label = "day" if self.demo_days_remaining == 1 else "days"
        return f'ProCure Medical - Demo ({self.demo_days_remaining} {day_label} left)'

    def refresh_theme(self):
        palette = get_theme_palette()
        primary = palette["primary_main"]
        primary_hover = palette["primary_hover"]
        active_text = palette["sidebar_active_text"]
        sidebar_bg = primary
        sidebar_border = primary_hover
        self._current_sidebar_bg = sidebar_bg
        self._current_sidebar_border = sidebar_border

        self.setStyleSheet(load_stylesheets())
        self.header_widget.setStyleSheet(f"""
            background-color: {primary};
            color: #F4F8FB;
            border-bottom: 1px solid {sidebar_border};
        """)

        self.sidebar_scroll.setStyleSheet(f""" 
                                    background-color: {sidebar_bg};

                                    QScrollArea {{
                                        background-color: {sidebar_bg};
                                        border: none;
                                    }}
                                    QScrollArea > QWidget > QWidget {{
                                        background-color: {sidebar_bg};
                                    }}
                                    QScrollBar:vertical,
                                    QScrollBar:horizontal {{
                                        width: 0px;
                                        height: 0px;
                                        background: transparent;
                                        border: none;
                                    }}
                                """)
        self.sidebar_panel.setStyleSheet(f"""
            QWidget#SidebarPanel {{
                background-color: {sidebar_bg};
                border: 1px solid {sidebar_border};
                border-radius: 0px;
            }}
        """)
        self._apply_sidebar_brand_logo()
        self.sidebar_search_wrap.setStyleSheet(f"""
            QWidget#SidebarSearchWrap {{
                background-color: {primary_hover};
                border: 1px solid {sidebar_border};
                border-radius: 12px;
            }}
        """)
        self.sidebar_avatar.setStyleSheet(f"""
            background-color: {primary};
            color: #FFFFFF;
            border-radius: 17px;
            font-weight: 800;
            font-size: 12px;
        """)
        self.sidebar_footer.setStyleSheet(f"""
            QWidget#SidebarFooter {{
                background-color: {sidebar_bg};
                border: 1px solid {sidebar_border};
                border-radius: 16px;
            }}
        """)
        self.sidebar_footer_action.setStyleSheet(f"""
            QPushButton {{
                color: {active_text};
                background-color: transparent;
                border: none;
                border-radius: 13px;
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {primary_hover};
            }}
        """)

        for btn in getattr(self, "main_sidebar_buttons", []):
            refresh = getattr(btn, "refresh_theme", None)
            if callable(refresh):
                refresh()

        current = self.main_content_layout.currentWidget() if hasattr(self, "main_content_layout") else None
        if current is not None:
            self._set_active_sidebar_by_widget(current)

    def apply_demo_restrictions(self):
        if not self.demo_mode:
            return
        demo_tooltip = "Demo mode: Reports can be viewed, but export and print actions are limited."
        self.reports_button.setEnabled(True)
        self.reports_button.setToolTip(demo_tooltip)

        
        
    
    
    
    
    
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
        if not self._require_any_permission(("reports.view",), "Reports"):
            return
        self.navigate_to_page(widget, layout)

    def navigate_to_page(self, widget, layout):
        if layout is not self.main_content_layout:
            layout.setCurrentWidget(widget)
            self._sync_shell_layout()
            QTimer.singleShot(0, self._sync_shell_layout)
            return

        if self.main_content_layout.currentWidget() is widget:
            self._set_active_sidebar_by_widget(widget)
            self._sync_shell_layout()
            QTimer.singleShot(0, self._sync_shell_layout)
            return

        self.main_content_layout.setCurrentWidget(widget)
        self._set_active_sidebar_by_widget(widget)
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)

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
        self._set_active_sidebar_by_widget(current_state[0])

    def on_main_page_changed(self, index):
        if self._is_history_navigation:
            return

        widget = self.main_content_layout.widget(index)
        if widget is None:
            return

        self._set_active_sidebar_by_widget(widget)

        self.record_history_state(self.capture_navigation_state(widget))
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)

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
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)

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

        self._set_active_sidebar_by_widget(main_widget)
        self.update_nav_buttons()
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)

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
            "dashboard": (self.dashboard_button, None),
            "business.view": (self.business_button, None),
            "profile.view": (self.profile_button, None),
            "supplier.view": (self.supplier_button, None),
            "rep.view": (self.salesrep_button, None),
            "purchase.view": (self.purchase_button, None),
            "po.view": (self.po_button, None),
            "grn.view": (self.grn_button, None),
            "sales.view": (self.sales_button, None),
            "customer.view": (self.customer_button, None),
            "product.view": (self.product_button, None),
            "employee.view": (self.employee_button, None),
            "transactions.view": (self.transaction_button, None),
            "purchasereturn.view": (self.purchase_return, None),
            "salesreturn.view": (self.sales_return, None),
            "expense.view": (self.expense_button, None),
            "reports.view": (self.reports_button, None),
        }

        for permission_name, buttons in permission_to_buttons.items():
            if Permissions.has_permission(permission_name):
                continue

            for btn in buttons:
                if btn is not None:
                    btn.hide()
            
            



    def expand_sidebar(self):
        self.sidebar_collapsed = False
        self._set_sidebar_collapsed(False)
        self._set_sidebar_column_width(self.sidebar_expanded_width)
        self.sidebar_scroll.show()

        if not self.ham_close_icon.isNull():
            self.ham_button.setIcon(self.ham_close_icon)
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)

    def collapse_sidebar(self):
        self.sidebar_collapsed = True
        self._set_sidebar_collapsed(True)
        self._set_sidebar_column_width(self.sidebar_collapsed_width)
        self.sidebar_scroll.show()

        if not self.ham_menu_icon.isNull():
            self.ham_button.setIcon(self.ham_menu_icon)
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)



    def hide_sidebar(self, sidebar):
        
        sidebar.hide()

    def _configure_main_sidebar_icons(self):
        for btn, icon_path in self.main_sidebar_icon_map.items():
            btn.setProperty("sidebar_icon_path", icon_path)
            icon = self._load_icon(icon_path)
            if not icon.isNull():
                btn.setIcon(icon)
                btn.setIconSize(QSize(18, 18))
            self._set_main_button_icon_tone(btn, "#DDD9EB")

    def _set_main_button_icon_tone(self, btn, color_hex):
        icon_relative_path = btn.property("sidebar_icon_path")
        if not icon_relative_path:
            return
        base_icon = self._load_icon(str(icon_relative_path))
        if base_icon.isNull():
            return
        pixmap = base_icon.pixmap(QSize(18, 18))
        if pixmap.isNull():
            return
        tinted = QPixmap(pixmap.size())
        tinted.fill(Qt.transparent)
        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QColor(color_hex))
        painter.end()
        btn.setIcon(QIcon(tinted))
        btn.setIconSize(QSize(18, 18))

    def _set_sidebar_collapsed(self, collapsed):
        for btn in getattr(self, "main_sidebar_buttons", []):
            btn.set_collapsed(collapsed)

        for widget in (
            getattr(self, "sidebar_search_wrap", None),
            getattr(self, "sidebar_brand_mark", None),
            getattr(self, "sidebar_profile_text_wrap", None),
        ):
            if widget is not None:
                widget.setVisible(not collapsed)

        if hasattr(self, "sidebar_brand_mark"):
            self.sidebar_brand_mark.setMinimumWidth(0 if collapsed else 136)
            self.sidebar_brand_mark.setMaximumWidth(0 if collapsed else 136)

        if hasattr(self, "sidebar_panel_layout"):
            margins = (4, 10, 4, 10) if collapsed else (14, 14, 14, 14)
            self.sidebar_panel_layout.setContentsMargins(*margins)

        if hasattr(self, "sidebar_nav_layout"):
            self.sidebar_nav_layout.setAlignment(
                (Qt.AlignTop | Qt.AlignHCenter) if collapsed else Qt.AlignTop
            )

        if hasattr(self, "sidebar_header_spacer"):
            self.sidebar_header_spacer.setVisible(not collapsed)

        if hasattr(self, "sidebar_header_layout"):
            self.sidebar_header_layout.setSpacing(0 if collapsed else 8)
            self.sidebar_header_layout.setContentsMargins(0, 2, 0, 2) if collapsed else self.sidebar_header_layout.setContentsMargins(4, 2, 4, 2)
            if hasattr(self, "sidebar_toggle_button"):
                self.sidebar_header_layout.setAlignment(
                    self.sidebar_toggle_button,
                    (Qt.AlignHCenter | Qt.AlignVCenter) if collapsed else (Qt.AlignRight | Qt.AlignVCenter),
                )

        if hasattr(self, "sidebar_footer_layout"):
            self.sidebar_footer_layout.setSpacing(0 if collapsed else 10)

        if hasattr(self, "sidebar_footer"):
            self.sidebar_footer.setStyleSheet("""
                QWidget#SidebarFooter {
                    background-color: %s;
                    border: 1px solid %s;
                    border-radius: 16px;
                }
            """ % (
                getattr(self, "_current_sidebar_bg", "#7B5AA6"),
                getattr(self, "_current_sidebar_border", "#684A8C"),
            ))

        if hasattr(self, "sidebar_avatar"):
            self.sidebar_avatar.setFixedSize(34, 34)

        toggle_icon = self.ham_menu_icon if collapsed else self.ham_close_icon
        if hasattr(self, "sidebar_toggle_button") and not toggle_icon.isNull():
            self.sidebar_toggle_button.setIcon(toggle_icon)
        if hasattr(self, "ham_button") and not toggle_icon.isNull():
            self.ham_button.setIcon(toggle_icon)

    def _apply_sidebar_brand_logo(self):
        if not hasattr(self, "sidebar_brand_mark"):
            return

        pixmap = QPixmap(resource_path("res/logo.png"))
        if pixmap.isNull():
            self.sidebar_brand_mark.setPixmap(QPixmap())
            self.sidebar_brand_mark.setText("P")
            self.sidebar_brand_mark.setStyleSheet("""
                background-color: #163B5C;
                color: #FFFFFF;
                border-radius: 14px;
                font-family: montserrat;
                font-size: 13px;
                font-weight: 800;
            """)
            return

        scaled = pixmap.scaled(130, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.sidebar_brand_mark.setText("")
        self.sidebar_brand_mark.setPixmap(scaled)
        self.sidebar_brand_mark.setStyleSheet("""
            background-color: transparent;
            border: none;
        """)

    def _set_rail_button_active(self, btn, active=False):
        if btn is None:
            return
        if btn.property("rail_variant") == "toggle":
            return

        btn.setProperty("rail_active", bool(active))

        if active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F8F6F1;
                    color: #17152A;
                    border: 1px solid #F3EBDD;
                    border-radius: 12px;
                    font-size: 10px;
                    font-weight: 700;
                    text-align: center;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #FFFFFF;
                    border: 1px solid #F3EBDD;
                    color: #17152A;
                }
                QPushButton:pressed {
                    background-color: #EFE8D9;
                    border: 1px solid #E9DFC9;
                    color: #17152A;
                }
            """)
            self._set_rail_button_icon_tone(btn, "#17152A")
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #DDD9EB;
                    border: 1px solid transparent;
                    border-radius: 12px;
                    font-size: 10px;
                    font-weight: 600;
                    text-align: center;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #F8F6F1;
                    border: 1px solid #F3EBDD;
                    color: #17152A;
                }
                QPushButton:pressed {
                    background-color: #EFE8D9;
                    border: 1px solid #E9DFC9;
                    color: #17152A;
                }
            """)
            self._set_rail_button_icon_tone(btn, "#DDD9EB")

    def _set_rail_button_icon_tone(self, btn, color_hex):
        icon_relative_path = btn.property("rail_icon_path")
        if not icon_relative_path:
            return
        base_icon = self._load_icon(str(icon_relative_path))
        if base_icon.isNull():
            return
        pixmap = base_icon.pixmap(QSize(18, 18))
        if pixmap.isNull():
            return
        tinted = QPixmap(pixmap.size())
        tinted.fill(Qt.transparent)
        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QColor(color_hex))
        painter.end()
        btn.setIcon(QIcon(tinted))
        btn.setIconSize(QSize(18, 18))

    def _set_active_sidebar_by_widget(self, widget):
        for btn in getattr(self, "main_sidebar_buttons", []):
            btn.set_active(False)
            self._set_main_button_icon_tone(btn, "#DDD9EB")

        for btn in getattr(self, "rail_nav_buttons", []):
            self._set_rail_button_active(btn, False)

        pair = getattr(self, "widget_sidebar_map", {}).get(widget)
        if pair:
            full_btn, rail_btn = pair
            if full_btn.isVisible():
                full_btn.set_active(True)
                self._set_main_button_icon_tone(full_btn, "#17152A")
            if rail_btn is not None and rail_btn.isVisible():
                self._set_rail_button_active(rail_btn, True)
            return

        for _owner, (full_btn, rail_btn) in getattr(self, "widget_sidebar_map", {}).items():
            if full_btn.isVisible():
                full_btn.set_active(True)
                self._set_main_button_icon_tone(full_btn, "#17152A")
                if rail_btn is not None and rail_btn.isVisible():
                    self._set_rail_button_active(rail_btn, True)
                break

    def _load_icon(self, primary_relative_path, fallback_relative_path=None):
        icon = QIcon()
        primary_path = resource_path(primary_relative_path)
        if primary_path.lower().endswith(".svg"):
            renderer = QSvgRenderer(primary_path)
            if renderer.isValid():
                pixmap = QPixmap(20, 20)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                icon = QIcon(pixmap)
        else:
            icon = QIcon(primary_path)

        if (icon.isNull() or not self._icon_can_render(icon, QSize(18, 18))) and fallback_relative_path:
            icon = QIcon(QPixmap(resource_path(fallback_relative_path)))
        return icon

    def _icon_can_render(self, icon, size):
        if icon.isNull():
            return False
        pixmap = icon.pixmap(size)
        return not pixmap.isNull()

    def collapse_sidebar_from_header(self):
        if self.sidebar_collapsed:
            self.expand_sidebar()
        else:
            self.collapse_sidebar()

    def reopen_sidebar_from_rail(self):
        self.expand_sidebar()

    def create_rail_button(self, icon_relative_path, tooltip, fallback_text="", variant="nav"):
        btn = QPushButton("")
        btn.setToolTip(tooltip)
        btn.setProperty("rail_variant", variant)
        btn.setProperty("rail_icon_path", icon_relative_path)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(42, 42)
        btn.setContentsMargins(0, 0, 0, 0)
        icon = self._load_icon(icon_relative_path)
        if self._icon_can_render(icon, QSize(18, 18)):
            btn.setIcon(icon)
            btn.setIconSize(QSize(18, 18))
        else:
            btn.setText(fallback_text)
        if variant == "toggle":
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #201C32;
                    color: #F8F6F1;
                    border: 1px solid #2C2742;
                    border-radius: 12px;
                    font-size: 10px;
                    font-weight: 700;
                    text-align: center;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #2A2442;
                    border: 1px solid #383251;
                    color: #ffffff;
                }
                QPushButton:pressed {
                    background-color: #171327;
                    border: 1px solid #2A2442;
                    color: #ffffff;
                }
            """)
        else:
            self._set_rail_button_active(btn, False)
        return btn

    def eventFilter(self, obj, event):
        if obj in getattr(self, "rail_nav_buttons", []):
            if event.type() == QEvent.Enter and not bool(obj.property("rail_active")):
                self._set_rail_button_icon_tone(obj, "#17152A")
            elif event.type() == QEvent.Leave and not bool(obj.property("rail_active")):
                self._set_rail_button_icon_tone(obj, "#DDD9EB")
        return super().eventFilter(obj, event)

    def _refresh_sidebar_profile(self):
        app = QApplication.instance()
        username = str((app.property("username") or "User")) if app else "User"
        role = str((app.property("user_role") or "Workspace")) if app else "Workspace"

        initials = "".join(part[:1] for part in username.split()[:2]).upper() or "U"
        self.sidebar_avatar.setText(initials[:2])
        self.sidebar_profile_name.setText(username)
        self.sidebar_profile_role.setText(role.replace("_", " ").title())

    def _filter_sidebar_buttons(self, text):
        needle = str(text or "").strip().lower()
        for btn in getattr(self, "main_sidebar_buttons", []):
            matches = (not needle) or (needle in btn.text().lower())
            btn.setVisible(matches)
        
        
    
    
    def reset_widget_size(self, layout, widget):
        
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        widget.setMinimumSize(0, 0)
        widget.setMaximumSize(16777215, 16777215)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _set_sidebar_column_width(self, width):
        width = int(max(0, width or 0))
        self.sidebar_scroll.setFixedWidth(width)
        self.sidebar_scroll.setMinimumWidth(width)
        self.sidebar_scroll.setMaximumWidth(width)

    def _sync_shell_layout(self):
        target_width = self.sidebar_collapsed_width if self.sidebar_collapsed else self.sidebar_expanded_width
        self._set_sidebar_column_width(target_width)
        self.sidebar_scroll.show()

        if hasattr(self, "content_area_widget"):
            self.content_area_widget.setMinimumWidth(0)
            self.content_area_widget.updateGeometry()

        if hasattr(self, "main_content_widget"):
            self.main_content_widget.setMinimumWidth(0)
            self.main_content_widget.updateGeometry()

        current = self.main_content_layout.currentWidget() if hasattr(self, "main_content_layout") else None
        if current is not None:
            current.updateGeometry()

        self.layout.invalidate()
        self.layout.activate()
        self.widget.updateGeometry()
        self.widget.update()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_shell_layout()



class SelectAllLineEditFilter(QObject):
    def eventFilter(self, obj, event):
        if isinstance(obj, QLineEdit) and event.type() == QEvent.FocusIn:
            QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)
    




    
if __name__ == '__main__':

    app = QApplication(sys.argv)

    select_all_filter = SelectAllLineEditFilter()
    app.installEventFilter(select_all_filter)


    app.setStyleSheet(load_stylesheets())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
