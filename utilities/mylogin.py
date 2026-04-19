
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget,QTableWidget, QMainWindow,QMessageBox, QPushButton, QHBoxLayout, QVBoxLayout, QStackedLayout, QLabel, QSizePolicy, QGraphicsOpacityEffect, QToolButton, QCompleter, QMenu
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
        self._shutdown_logout_logged = False
        
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
        self.sidebar_force_hidden = False
        self._background_warmup_started = False
        self._background_warmup_queue = []
        self._background_warmup_token = 0
        self._sales_phase_warmup_started = False
        self._purchase_phase_warmup_started = False

        
        
        
        # Self Widget and Layout
        
        self.widget = QWidget()
        self.layout = QHBoxLayout()
        self.reset_widget_size(self.layout, self.widget)

        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        app = QApplication.instance()
        if app and not app.property("_logout_exit_hook_connected"):
            app.aboutToQuit.connect(self._log_shutdown_logout_once)
            app.setProperty("_logout_exit_hook_connected", True)
       
        
        
        # SIDE-BAR SCROLL
        self.sidebar_expanded_width = 224
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
        self.sidebar_rail_width = 40
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
        self.sidebar_panel_layout.setContentsMargins(12, 12, 12, 12)
        self.sidebar_panel_layout.setSpacing(8)
        sidebar_layout.addWidget(self.sidebar_panel)

        # COMPACT SIDEBAR RAIL WIDGET
        rail_widget = QWidget()
        rail_layout = QVBoxLayout(rail_widget)
        self.sidebar_rail_layout = rail_layout
        self.reset_widget_size(rail_layout, rail_widget)
        rail_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        rail_layout.setSpacing(6)
        rail_widget.setLayout(rail_layout)
        self.sidebar_rail_scroll.setWidget(rail_widget)

        self.rail_profile_button = self.create_rail_button("res/rail_icons/profile.svg", "Profile", "P")
        self.rail_profile_button.clicked.connect(self._open_profile_from_sidebar_footer)
        self.rail_profile_button.installEventFilter(self)
        self.rail_nav_buttons = [self.rail_profile_button]

        rail_layout.addStretch()
        rail_layout.addWidget(self.rail_profile_button, 0, Qt.AlignBottom | Qt.AlignHCenter)
        
        
        
        # CONTENT AREA WIDGET
        content_area_widget = QWidget()
        self.content_area_widget = content_area_widget
        content_area_widget.setStyleSheet("background-color: #fff;")
        content_area_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        content_area_layout = QVBoxLayout()
        self.content_area_layout = content_area_layout
        self.reset_widget_size(content_area_layout, content_area_widget)
        
        
        
        
        
        
        # HEADER WIDGET
        self.header_widget = QWidget()
        header_layout = QHBoxLayout()
        self.header_layout = header_layout
        self.header_base_margins = (16, 4, 16, 4)

        self.reset_widget_size(header_layout, self.header_widget)
        
        self.header_widget.setFixedHeight(52)
        header_layout.setContentsMargins(*self.header_base_margins)
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
        self.ham_button.setFixedSize(30, 30)
        self.ham_button.setIconSize(QSize(16, 16))
        self.ham_button.clicked.connect(self.collapse_sidebar_from_header)
        self.ham_button.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background-color: #2B5B7E;
                border: 1px solid #3B7198;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #35698F;
                border: 1px solid #4A81AA;
            }
            QPushButton:pressed {
                background-color: #234A68;
                border: 1px solid #35637F;
            }
        """)

        self.ham_menu_icon = self._load_icon("res/rail_icons/ham.svg", "res/ham.png")
        self.ham_close_icon = self._load_icon("res/rail_icons/ham_close.svg")
        self.ham_button.setIcon(self.ham_close_icon if not self.ham_close_icon.isNull() else self.ham_menu_icon)

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
        if not self.ham_close_icon.isNull():
            self.sidebar_toggle_button.setIcon(self.ham_close_icon)

        self.header_sidebar_slot = QWidget()
        self.header_sidebar_slot.setObjectName("HeaderSidebarSlot")
        self.header_sidebar_slot.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.header_sidebar_layout = QHBoxLayout(self.header_sidebar_slot)
        self.header_sidebar_layout.setContentsMargins(0, 0, 10, 0)
        self.header_sidebar_layout.setSpacing(8)
        self.header_sidebar_layout.addWidget(self.sidebar_brand_mark, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.header_sidebar_layout.addStretch()
        self.header_sidebar_layout.addWidget(self.sidebar_toggle_button, 0, Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(self.header_sidebar_slot, 0, Qt.AlignVCenter)
        header_layout.addSpacing(10)
        
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
        self.back_nav_btn.setFixedSize(30, 30)
        self.back_nav_btn.setIconSize(QSize(13, 13))
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
        self.forward_nav_btn.setFixedSize(30, 30)
        self.forward_nav_btn.setIconSize(QSize(13, 13))
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
        
        
        
        
        
        # main content now lives inside the shared workspace shell with the sidebar
        
        
        
        
        

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
        self.sidebar_nav_layout.setContentsMargins(0, 4, 0, 0)
        self.sidebar_nav_layout.setSpacing(1)
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
        self.sidebar_footer.setCursor(Qt.PointingHandCursor)
        self.sidebar_avatar.setCursor(Qt.PointingHandCursor)
        self.sidebar_profile_text_wrap.setCursor(Qt.PointingHandCursor)
        self.sidebar_profile_name.setCursor(Qt.PointingHandCursor)
        self.sidebar_profile_role.setCursor(Qt.PointingHandCursor)
        self.sidebar_footer.mousePressEvent = self._handle_sidebar_profile_click
        self.sidebar_avatar.mousePressEvent = self._handle_sidebar_profile_click
        self.sidebar_profile_text_wrap.mousePressEvent = self._handle_sidebar_profile_click
        self.sidebar_profile_name.mousePressEvent = self._handle_sidebar_profile_click
        self.sidebar_profile_role.mousePressEvent = self._handle_sidebar_profile_click

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
        self.profile_button.hide()
        if self.sidebar_search_edit is not None:
            self.sidebar_search_edit.textChanged.connect(self._filter_sidebar_buttons)
        self.refresh_theme()

        self.apply_role_permissions()
        self.apply_demo_restrictions()



        
        

        
        
        
        
        


        self.dashboard = None
        self.welcome = None
        
        self.profile = None
        self.business = None
        self.supplier = None
        
        self.salesrep = None
        self.purchase = None
        self.po = None
        self.grn = None
        
        self.base_sales = None
        
        self.base_customer = None
        self.product = None
        
        
        self.employee = None
        self.transaction = None
        self.purchasereturn = None
        self.salesreturn = None
        self.expense = None
        self.reports = None

        self._page_factories = {
            "dashboard": lambda: BaseDashboardWidget(),
            "welcome": lambda: WelcomeWidget(),
            "profile": lambda: BaseProfileWidget(),
            "business": lambda: BaseBusinessWidget(),
            "supplier": lambda: BaseSupplierWidget(),
            "salesrep": lambda: BaseSalesRepWidget(),
            "purchase": lambda: BasePurchaseWidget(),
            "po": lambda: BasePOWidget(),
            "grn": lambda: BaseGRNWidget(),
            "base_sales": lambda: BaseSalesWidget(controller=self),
            "base_customer": lambda: BaseCustomerWidget(controller=self),
            "product": lambda: BaseProductWidget(),
            "employee": lambda: BaseEmployeeWidget(),
            "transaction": lambda: BaseTransactionWidget(),
            "purchasereturn": lambda: BasePurchaseReturnWidget(),
            "salesreturn": lambda: BaseSalesReturnWidget(),
            "expense": lambda: BaseExpenseWidget(),
            "reports": lambda: BaseReportsWidget(),
        }
        self._page_sidebar_buttons = {
            "dashboard": self.dashboard_button,
            "business": self.business_button,
            "profile": self.profile_button,
            "supplier": self.supplier_button,
            "salesrep": self.salesrep_button,
            "purchase": self.purchase_button,
            "po": self.po_button,
            "grn": self.grn_button,
            "base_sales": self.sales_button,
            "base_customer": self.customer_button,
            "product": self.product_button,
            "employee": self.employee_button,
            "transaction": self.transaction_button,
            "purchasereturn": self.purchase_return,
            "salesreturn": self.sales_return,
            "expense": self.expense_button,
            "reports": self.reports_button,
        }
        
        # self.holdsales = BaseHoldSalesWidget(controller=self)
        
        
        # self.dashboard.sales_page_signal.connect(lambda: self.set_sales(self.base_sales, self.main_content_layout))
        # self.dashboard.product_page_signal.connect(lambda: self.set_product(self.product, self.main_content_layout))
        
        

        self.dashboard_button.clicked.connect(lambda: self.set_dashboard(None, self.main_content_layout))
        self.business_button.clicked.connect(lambda: self.set_business(None, self.main_content_layout))
        self.profile_button.clicked.connect(lambda: self.set_profile(None, self.main_content_layout))
        self.supplier_button.clicked.connect(lambda: self.set_supplier(None, self.main_content_layout))
        self.salesrep_button.clicked.connect(lambda: self.set_salesrep(None, self.main_content_layout))
        self.purchase_button.clicked.connect(lambda: self.set_purchase(None, self.main_content_layout))
        self.po_button.clicked.connect(lambda: self.set_po(None, self.main_content_layout))
        self.grn_button.clicked.connect(lambda: self.set_grn(None, self.main_content_layout))
        self.sales_button.clicked.connect(lambda: self.set_sales(None, self.main_content_layout))
        self.customer_button.clicked.connect(lambda: self.set_customer(None, self.main_content_layout))
        self.product_button.clicked.connect(lambda: self.set_product(None, self.main_content_layout))
        self.employee_button.clicked.connect(lambda: self.set_employee(None, self.main_content_layout))
        self.transaction_button.clicked.connect(lambda: self.set_transaction(None, self.main_content_layout))
        self.purchase_return.clicked.connect(lambda: self.set_purchasereturn(None, self.main_content_layout))
        self.sales_return.clicked.connect(lambda: self.set_salesreturn(None, self.main_content_layout))
        self.expense_button.clicked.connect(lambda: self.set_expense(None, self.main_content_layout))
        self.reports_button.clicked.connect(lambda: self.set_reports(None, self.main_content_layout))
        # self.holdsales_button.clicked.connect(lambda: self.set_holdsales(self.holdsales, self.main_content_layout))

        from PySide6.QtGui import QKeySequence, QShortcut

        
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self.set_dashboard(None, self.main_content_layout))  # Dashboard
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self.set_profile(None, self.main_content_layout))  # Profile
        QShortcut(QKeySequence("Ctrl+3"), self, activated=lambda: self.set_supplier(None, self.main_content_layout))  # Supplier
        QShortcut(QKeySequence("Ctrl+4"), self, activated=lambda: self.set_salesrep(None, self.main_content_layout))  # Sales Rep
        QShortcut(QKeySequence("Ctrl+5"), self, activated=lambda: self.set_purchase(None, self.main_content_layout))  # Purchase
        QShortcut(QKeySequence("Ctrl+6"), self, activated=lambda: self.set_sales(None, self.main_content_layout))  # Sales
        QShortcut(QKeySequence("Ctrl+7"), self, activated=lambda: self.set_customer(None, self.main_content_layout))  # Customer
        QShortcut(QKeySequence("Ctrl+8"), self, activated=lambda: self.set_product(None, self.main_content_layout))  # Product
        QShortcut(QKeySequence("Ctrl+9"), self, activated=lambda: self.set_employee(None, self.main_content_layout))  # Employee
        QShortcut(QKeySequence("Ctrl+0"), self, activated=lambda: self.set_transaction(None, self.main_content_layout))  # Transaction
        QShortcut(QKeySequence("Alt+Left"), self, activated=self.go_back)
        QShortcut(QKeySequence("Alt+Right"), self, activated=self.go_forward)
        # QShortcut(QKeySequence("Ctrl+P"), self, activated=lambda: self.set_purchasereturn(self.purchasereturn, self.main_content_layout))  # Purchase Return
        # QShortcut(QKeySequence("Ctrl+S"), self, activated=lambda: self.set_salesreturn(self.salesreturn, self.main_content_layout))  # Sales Return
        # QShortcut(QKeySequence("Ctrl+E"), self, activated=lambda: self.set_expense(self.expense, self.main_content_layout))  # Expense
        # QShortcut(QKeySequence("Ctrl+R"), self, activated=lambda: self.set_reports(self.reports, self.main_content_layout))  # Reports
        # QShortcut(QKeySequence("Ctrl+H"), self, activated=lambda: self.set_holdsales(self.holdsales, self.main_content_layout))  # On-Hold Sales
        
        
        self._build_top_navigation_strip()
        self.widget_sidebar_map = {}

        if Permissions.has_permission("dashboard"):
            self._ensure_page("dashboard")
        else:
            self._ensure_page("welcome")

        self._set_sidebar_collapsed(False)
        self._set_active_sidebar_by_widget(self.main_content_layout.currentWidget())
        self._refresh_top_navigation_strip()
        self._update_navigation_mode_visibility()
        

        
        
        
        # making all widgets focusable
        self.make_all_focusable(self)

        self.workspace_widget = QWidget()
        self.workspace_widget.setObjectName("WorkspaceShell")
        self.workspace_widget.setStyleSheet("""
            QWidget#WorkspaceShell {
                background-color: transparent;
            }
        """)
        self.workspace_layout = QHBoxLayout(self.workspace_widget)
        self.reset_widget_size(self.workspace_layout, self.workspace_widget)
        self.workspace_layout.addWidget(self.sidebar_rail_scroll, 0)
        self.workspace_layout.addWidget(self.sidebar_scroll, 0)
        self.workspace_layout.addWidget(main_content_scroll, 1)
        self.workspace_layout.setStretch(0, 0)
        self.workspace_layout.setStretch(1, 0)
        self.workspace_layout.setStretch(2, 1)

        content_area_layout.addWidget(self.workspace_widget, 1)

        self.layout.addWidget(content_area_widget, 1)
        self.layout.setStretch(0, 1)

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

    def _ensure_page(self, page_key):
        widget = getattr(self, page_key, None)
        if widget is not None:
            return widget

        factory = self._page_factories.get(page_key)
        if factory is None:
            raise KeyError(f"Unknown page key: {page_key}")

        widget = factory()
        setattr(self, page_key, widget)
        self.main_content_layout.addWidget(widget)

        sidebar_button = self._page_sidebar_buttons.get(page_key)
        if sidebar_button is not None:
            self.widget_sidebar_map[widget] = (sidebar_button, None)

        self._connect_nested_history_tracking(widget)
        return widget

    def _connect_nested_history_tracking(self, owner):
        if owner is None:
            return
        if owner in self._nested_history_connections:
            return

        nested_layout = getattr(owner, "stacked_layout", None)
        if nested_layout is None:
            return

        nested_layout.currentChanged.connect(
            lambda _index, owner=owner: self.on_nested_page_changed(owner)
        )
        self._nested_history_connections.append(owner)

    def _schedule_background_page_warmup(self):
        if self._background_warmup_started:
            return

        self._background_warmup_started = True
        self._start_background_warmup_batch(
            ["base_sales", "purchase"],
            start_delay_ms=300,
            step_delay_ms=250,
        )

    def _start_background_warmup_batch(self, page_keys, *, start_delay_ms=0, step_delay_ms=250):
        queue = [key for key in page_keys if key]
        if not queue:
            return

        self._background_warmup_token += 1
        token = self._background_warmup_token
        self._background_warmup_queue = queue
        QTimer.singleShot(start_delay_ms, lambda: self._run_next_background_page_warmup(token, step_delay_ms))

    def _start_sales_phase_warmup(self):
        if self._sales_phase_warmup_started:
            return
        self._sales_phase_warmup_started = True
        self._start_background_warmup_batch(
            ["product", "base_customer", "reports", "expense"],
            start_delay_ms=250,
            step_delay_ms=220,
        )

    def _start_purchase_phase_warmup(self):
        if self._purchase_phase_warmup_started:
            return
        self._purchase_phase_warmup_started = True
        self._start_background_warmup_batch(
            ["supplier", "transaction", "business", "salesrep", "po", "grn"],
            start_delay_ms=250,
            step_delay_ms=220,
        )

    def _run_next_background_page_warmup(self, token, step_delay_ms):
        if token != self._background_warmup_token:
            return
        if not self._background_warmup_queue:
            return

        page_key = self._background_warmup_queue.pop(0)
        self._warm_page_for_fast_navigation(page_key)

        if self._background_warmup_queue:
            QTimer.singleShot(step_delay_ms, lambda: self._run_next_background_page_warmup(token, step_delay_ms))

    def _warm_page_for_fast_navigation(self, page_key):
        try:
            widget = self._ensure_page(page_key)
        except Exception as exc:
            print(f"Background warmup skipped for {page_key}: {exc}")
            return

        # Warm the most common landing screens, not just the outer module shell.
        if page_key == "base_sales":
            try:
                if Permissions.has_permission("sales.create") and hasattr(widget, "set_createsales_widget"):
                    widget.set_createsales_widget()
                else:
                    reset = getattr(widget, "reset_to_default", None)
                    if callable(reset):
                        reset()
                return
            except Exception as exc:
                print(f"Background warmup sales init skipped: {exc}")

        if page_key == "purchase":
            try:
                if Permissions.has_permission("purchase.create") and hasattr(widget, "set_addpurchase_widget"):
                    widget.set_addpurchase_widget()
                else:
                    reset = getattr(widget, "reset_to_default", None)
                    if callable(reset):
                        reset()
                return
            except Exception as exc:
                print(f"Background warmup purchase init skipped: {exc}")

        reset = getattr(widget, "reset_to_default", None)
        if callable(reset):
            try:
                reset()
            except Exception as exc:
                print(f"Background warmup reset skipped for {page_key}: {exc}")

    def _pause_background_page_warmup(self):
        self._background_warmup_queue = []
        self._background_warmup_token += 1

        
        
    
    
    
    
    
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
            self._shutdown_logout_logged = True
            if app is not None:
                app.setProperty("_logout_already_logged", True)
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

    def _log_shutdown_logout_once(self):
        if self._shutdown_logout_logged:
            return

        app = QApplication.instance()
        if app is None:
            return

        if app.property("_logout_already_logged"):
            self._shutdown_logout_logged = True
            return

        username = app.property("username")
        user_id = app.property("user_id")
        login_session_id = app.property("login_session_id")
        if not username or not login_session_id:
            return

        try:
            log_activity(
                category="login",
                action="logout",
                entity_type="user",
                entity_id=user_id,
                note=f"{username} exited the application."
            )
            self._shutdown_logout_logged = True
            app.setProperty("_logout_already_logged", True)
        except Exception as exc:
            print("Shutdown logout audit failed (non-blocking):", exc)

    def closeEvent(self, event):
        self._log_shutdown_logout_once()
        super().closeEvent(event)
            
            
    
    
    
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
        self._pause_background_page_warmup()
        widget = self._ensure_page("dashboard")
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
        self._pause_background_page_warmup()
        widget = self._ensure_page("business")
        self.business.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_profile(self, widget, layout):
        if not self._require_any_permission(
            ("profile.view", "profile.update", "users.view", "users.create"),
            "Profile",
        ):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("profile")
        self.profile.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_supplier(self, widget, layout):
        if not self._require_any_permission(("supplier.view", "supplier.create"), "Suppliers"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("supplier")
        self.supplier.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_salesrep(self, widget, layout):
        if not self._require_any_permission(("rep.view", "rep.create"), "Sales Reps"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("salesrep")
        self.salesrep.reset_to_default()
        self.navigate_to_page(widget, layout)
    
    def set_purchase(self, widget, layout):
        if not self._require_any_permission(("purchase.view", "purchase.create"), "Purchases"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("purchase")
        if hasattr(self.purchase, "set_addpurchase_widget") and Permissions.has_permission('purchase.create'):
            self.purchase.set_addpurchase_widget()
        else:
            self.purchase.reset_to_default()
        self.navigate_to_page(widget, layout)
        self._start_purchase_phase_warmup()
    
    def set_po(self, widget, layout):
        if not self._require_any_permission(("po.view", "po.create"), "Purchase Orders"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("po")
        self.po.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_grn(self, widget, layout):
        if not self._require_any_permission(("grn.view", "grn.create"), "GRN"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("grn")
        self.grn.reset_to_default()
        self.navigate_to_page(widget, layout)
    
    def set_sales(self, widget, layout):
        if not self._require_any_permission(("sales.view", "sales.create"), "Sales"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("base_sales")
        if hasattr(self.base_sales, "set_createsales_widget") and Permissions.has_permission('sales.create'):
            self.base_sales.set_createsales_widget()
        else:
            self.base_sales.reset_to_default()
        self.navigate_to_page(widget, layout)
        self._start_sales_phase_warmup()

    def set_customer(self, widget, layout):
        if not self._require_any_permission(("customer.view", "customer.create"), "Customers"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("base_customer")
        self.base_customer.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_product(self, widget, layout):
        if not self._require_any_permission(("product.view", "product.create"), "Products"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("product")
        self.product.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_employee(self, widget, layout):
        if not self._require_any_permission(("employee.view", "employee.create"), "Employees"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("employee")
        self.employee.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_transaction(self, widget, layout):
        if not self._require_any_permission(("transactions.view", "transactions.create"), "Transactions"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("transaction")
        self.transaction.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_purchasereturn(self, widget, layout):
        if not self._require_any_permission(
            ("purchasereturn.view", "purchasereturn.create"),
            "Purchase Returns",
        ):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("purchasereturn")
        self.purchasereturn.reset_to_default()
        self.navigate_to_page(widget, layout)

    def set_salesreturn(self, widget, layout):
        if not self._require_any_permission(
            ("salesreturn.view", "salesreturn.create"),
            "Sales Returns",
        ):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("salesreturn")
        self.salesreturn.reset_to_default()
        self.navigate_to_page(widget, layout)


    def set_expense(self, widget, layout):
        if not self._require_any_permission(("expense.view", "expense.create"), "Expenses"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("expense")
        self.expense.reset_to_default()
        self.navigate_to_page(widget, layout)
    
        
    def set_reports(self, widget, layout):
        if not self._require_any_permission(("reports.view",), "Reports"):
            return
        self._pause_background_page_warmup()
        widget = self._ensure_page("reports")
        self.reports.reset_to_default()
        self.navigate_to_page(widget, layout)

    def navigate_to_page(self, widget, layout):
        if layout is not self.main_content_layout:
            layout.setCurrentWidget(widget)
            self._refresh_top_navigation_strip()
            self._update_navigation_mode_visibility()
            self._sync_shell_layout()
            QTimer.singleShot(0, self._sync_shell_layout)
            return

        if self.main_content_layout.currentWidget() is widget:
            self._set_active_sidebar_by_widget(widget)
            self._refresh_top_navigation_strip()
            self._update_navigation_mode_visibility()
            self._sync_shell_layout()
            QTimer.singleShot(0, self._sync_shell_layout)
            return

        self.main_content_layout.setCurrentWidget(widget)
        self._set_active_sidebar_by_widget(widget)
        self._refresh_top_navigation_strip()
        self._update_navigation_mode_visibility()
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
        self._refresh_top_navigation_strip()
        self._update_navigation_mode_visibility()
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
            self._connect_nested_history_tracking(owner)

    def on_nested_page_changed(self, owner):
        if self._is_history_navigation:
            return

        if self.main_content_layout.currentWidget() is not owner:
            return

        self.record_history_state(self.capture_navigation_state(owner))
        self._refresh_top_navigation_strip()
        self._update_navigation_mode_visibility()
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
        self._refresh_top_navigation_strip()
        self._update_navigation_mode_visibility()
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)

    def update_nav_buttons(self):
        can_go_back = self.current_index > 0
        can_go_forward = self.current_index >= 0 and self.current_index < len(self.history) - 1

        self.back_nav_btn.setEnabled(can_go_back)
        self.forward_nav_btn.setEnabled(can_go_forward)
        if hasattr(self, "top_nav_back_btn"):
            self.top_nav_back_btn.setEnabled(can_go_back)
        if hasattr(self, "top_nav_forward_btn"):
            self.top_nav_forward_btn.setEnabled(can_go_forward)

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

        if hasattr(self, "top_nav_buttons_layout"):
            self._refresh_top_navigation_strip()
            
            



    def expand_sidebar(self):
        self.sidebar_force_hidden = False
        self.sidebar_collapsed = False
        self._set_sidebar_collapsed(False)
        self._set_sidebar_column_width(self.sidebar_expanded_width)
        self.sidebar_scroll.show()
        self._update_navigation_mode_visibility()

        if not self.ham_close_icon.isNull():
            self.ham_button.setIcon(self.ham_close_icon)
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)

    def collapse_sidebar(self):
        self.sidebar_force_hidden = False
        self.sidebar_collapsed = True
        self._set_sidebar_collapsed(True)
        self._set_sidebar_column_width(self.sidebar_collapsed_width)
        self.sidebar_scroll.show()
        self._update_navigation_mode_visibility()

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
            getattr(self, "sidebar_profile_text_wrap", None),
        ):
            if widget is not None:
                widget.setVisible(not collapsed)

        if hasattr(self, "sidebar_panel_layout"):
            margins = (4, 18, 4, 10) if collapsed else (14, 10, 14, 14)
            self.sidebar_panel_layout.setContentsMargins(*margins)

        if hasattr(self, "sidebar_nav_layout"):
            self.sidebar_nav_layout.setContentsMargins(0, 10 if collapsed else 4, 0, 0)
            self.sidebar_nav_layout.setAlignment(
                (Qt.AlignTop | Qt.AlignHCenter) if collapsed else Qt.AlignTop
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

    def _build_top_navigation_strip(self):
        self.top_nav_widget = QWidget()
        self.top_nav_widget.setObjectName("TopNavigationStrip")
        self.top_nav_widget.setFixedHeight(44)
        self.top_nav_widget.setStyleSheet("""
            QWidget#TopNavigationStrip {
                background-color: #163B5C;
                border-bottom: 1px solid #244A62;
            }
        """)

        top_nav_layout = QHBoxLayout(self.top_nav_widget)
        top_nav_layout.setContentsMargins(14, 6, 10, 6)
        top_nav_layout.setSpacing(10)

        self.top_nav_left_wrap = QWidget()
        self.top_nav_left_wrap.setStyleSheet("background: transparent;")
        self.top_nav_left_layout = QHBoxLayout(self.top_nav_left_wrap)
        self.top_nav_left_layout.setContentsMargins(0, 0, 0, 0)
        self.top_nav_left_layout.setSpacing(6)
        self.top_nav_left_layout.addWidget(self.ham_button, 0, Qt.AlignVCenter)
        self.top_nav_left_layout.addSpacing(20)

        self.top_nav_menu_wrap = QWidget()
        self.top_nav_menu_wrap.setStyleSheet("background: transparent;")
        self.top_nav_menu_layout = QHBoxLayout(self.top_nav_menu_wrap)
        self.top_nav_menu_layout.setContentsMargins(0, 0, 0, 0)
        self.top_nav_menu_layout.setSpacing(6)
        self.top_nav_left_layout.addWidget(self.top_nav_menu_wrap, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.top_nav_left_layout.addStretch()
        top_nav_layout.addWidget(self.top_nav_left_wrap, 0, Qt.AlignLeft | Qt.AlignVCenter)

        self.top_nav_center_wrap = QWidget()
        self.top_nav_center_wrap.setStyleSheet("background: transparent;")
        self.top_nav_center_layout = QHBoxLayout(self.top_nav_center_wrap)
        self.top_nav_center_layout.setContentsMargins(0, 0, 0, 0)
        self.top_nav_center_layout.setSpacing(0)

        self.top_nav_search = QLineEdit()
        self.top_nav_search.setPlaceholderText("Jump to page...")
        self.top_nav_search.setClearButtonEnabled(True)
        self.top_nav_search.setFixedHeight(28)
        self.top_nav_search.setMinimumWidth(240)
        self.top_nav_search.setMaximumWidth(340)
        self.top_nav_search.setStyleSheet("""
            QLineEdit {
                background-color: #1E4A6B;
                color: #F4F8FB;
                border: 1px solid #315C7A;
                border-radius: 7px;
                padding: 0 10px;
                font-family: arial;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #5E8EB2;
                background-color: #235376;
            }
        """)
        self.top_nav_search_model = QStringListModel(self)
        self.top_nav_search_completer = QCompleter(self.top_nav_search_model, self)
        self.top_nav_search_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.top_nav_search_completer.setFilterMode(Qt.MatchContains)
        self.top_nav_search_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.top_nav_search.setCompleter(self.top_nav_search_completer)
        self.top_nav_search.returnPressed.connect(self._handle_top_nav_search_submit)
        self.top_nav_search_completer.activated.connect(self._handle_top_nav_search_choice)
        self.top_nav_center_layout.addWidget(self.top_nav_search)
        top_nav_layout.addStretch(1)

        self.top_nav_right_wrap = QWidget()
        self.top_nav_right_wrap.setStyleSheet("background: transparent;")
        self.top_nav_right_layout = QHBoxLayout(self.top_nav_right_wrap)
        self.top_nav_right_layout.setContentsMargins(0, 0, 0, 0)
        self.top_nav_right_layout.setSpacing(6)

        self.top_nav_right_dynamic_wrap = QWidget()
        self.top_nav_right_dynamic_wrap.setStyleSheet("background: transparent;")
        self.top_nav_right_dynamic_layout = QHBoxLayout(self.top_nav_right_dynamic_wrap)
        self.top_nav_right_dynamic_layout.setContentsMargins(0, 0, 0, 0)
        self.top_nav_right_dynamic_layout.setSpacing(6)

        self.top_nav_sidebar_toggle_btn = self._create_top_nav_text_button(
            "Hide Sidebar",
            callback=self._toggle_force_hide_sidebar,
            active=False,
            enabled=True,
        )

        self.top_nav_back_btn = QPushButton()
        self.top_nav_back_btn.setToolTip("Previous page")
        self.top_nav_back_btn.setCursor(Qt.PointingHandCursor)
        self.top_nav_back_btn.setObjectName("HeaderControlButton")
        self.top_nav_back_btn.setFixedSize(30, 30)
        self.top_nav_back_btn.setIconSize(QSize(13, 13))
        self.top_nav_back_btn.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background-color: #2B5B7E;
                border: 1px solid #3B7198;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #35698F;
                border: 1px solid #4A81AA;
            }
            QPushButton:pressed {
                background-color: #234A68;
                border: 1px solid #35637F;
            }
            QPushButton:disabled {
                color: #B8D0E1;
                background-color: #244B68;
                border: 1px solid #315B79;
            }
        """)
        if not self._icon_can_render(self.back_nav_icon, QSize(14, 14)):
            self.top_nav_back_btn.setText("<")
        else:
            self.top_nav_back_btn.setIcon(self.back_nav_icon)
        self.top_nav_back_btn.clicked.connect(self.go_back)

        self.top_nav_forward_btn = QPushButton()
        self.top_nav_forward_btn.setToolTip("Next page")
        self.top_nav_forward_btn.setCursor(Qt.PointingHandCursor)
        self.top_nav_forward_btn.setObjectName("HeaderControlButton")
        self.top_nav_forward_btn.setFixedSize(30, 30)
        self.top_nav_forward_btn.setIconSize(QSize(13, 13))
        self.top_nav_forward_btn.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background-color: #2B5B7E;
                border: 1px solid #3B7198;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #35698F;
                border: 1px solid #4A81AA;
            }
            QPushButton:pressed {
                background-color: #234A68;
                border: 1px solid #35637F;
            }
            QPushButton:disabled {
                color: #B8D0E1;
                background-color: #244B68;
                border: 1px solid #315B79;
            }
        """)
        if not self._icon_can_render(self.forward_nav_icon, QSize(14, 14)):
            self.top_nav_forward_btn.setText(">")
        else:
            self.top_nav_forward_btn.setIcon(self.forward_nav_icon)
        self.top_nav_forward_btn.clicked.connect(self.go_forward)

        top_nav_layout.addWidget(self.top_nav_back_btn, 0, Qt.AlignRight | Qt.AlignVCenter)
        top_nav_layout.addWidget(self.top_nav_forward_btn, 0, Qt.AlignRight | Qt.AlignVCenter)
        top_nav_layout.addSpacing(6)
        top_nav_layout.addWidget(self.top_nav_center_wrap, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.top_nav_right_layout.addWidget(self.top_nav_right_dynamic_wrap, 0, Qt.AlignRight | Qt.AlignVCenter)
        self.top_nav_right_layout.addWidget(self.top_nav_sidebar_toggle_btn, 0, Qt.AlignRight | Qt.AlignVCenter)

        top_nav_layout.addWidget(self.top_nav_right_wrap, 0, Qt.AlignRight | Qt.AlignVCenter)

        self._top_nav_search_targets = {}

        self.content_area_layout.insertWidget(0, self.top_nav_widget)

    def _clear_layout_widgets(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout_widgets(child_layout)

    def _create_top_nav_text_button(self, text, callback=None, *, active=False, subdued=False, enabled=True):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor if callback and enabled else Qt.ArrowCursor)
        button.setFlat(True)
        button.setEnabled(enabled)
        button.setMinimumHeight(28)
        button.setStyleSheet("""
            QPushButton {
                background: %s;
                border: 1px solid %s;
                border-radius: 5px;
                color: %s;
                font-family: arial;
                font-size: 14px;
                font-weight: %s;
                padding: 4px 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: %s;
                border: 1px solid %s;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                color: %s;
                background-color: %s;
                border: 1px solid transparent;
            }
        """ % (
            "#2D5D82" if active else "transparent",
            "#4A81AA" if active else "transparent",
            "#FFFFFF" if active else "#F4F8FB",
            "700" if active else "500",
            "#28557A" if not subdued else "#224B6D",
            "#4A81AA" if not subdued else "#3E7296",
            "#F4F8FB" if active else "#CFE0EE",
            "#2D5D82" if active else "transparent",
        ))
        if callback and enabled:
            button.clicked.connect(callback)
        return button

    def _create_top_nav_menu_button(self, text, entries, *, active=False):
        button = QToolButton()
        button.setText(f"{text}  ▾")
        button.setPopupMode(QToolButton.InstantPopup)
        button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet("""
            QToolButton {
                color: %s;
                background-color: %s;
                border: 1px solid %s;
                border-radius: 5px;
                padding: 4px 10px;
                font-family: arial;
                font-size: 14px;
                font-weight: %s;
            }
            QToolButton:hover {
                background-color: #28557A;
                border: 1px solid #4A81AA;
                color: #FFFFFF;
            }
            QToolButton::menu-indicator {
                image: none;
                width: 0px;
            }
        """ % (
            "#FFFFFF" if active else "#F4F8FB",
            "#2D5D82" if active else "transparent",
            "#4A81AA" if active else "transparent",
            "700" if active else "500",
        ))
        menu = QMenu(button)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        menu.setStyleSheet("""
            QMenu {
                background-color: #274663;
                color: #F3F4F6;
                border: 1px solid #3E6283;
                border-radius: 12px;
                padding: 6px 0px;
                margin-top: 6px;
            }
            QMenu::item {
                padding: 10px 18px;
                margin: 2px 8px;
                border-radius: 7px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #335777;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background: #416483;
                margin: 6px 12px;
            }
        """)
        for label, callback, enabled in entries:
            action = menu.addAction(label)
            action.setEnabled(enabled)
            if callback and enabled:
                action.triggered.connect(callback)
        button.setMenu(menu)
        return button

    def _create_top_nav_separator(self, text="|"):
        label = QLabel(text)
        label.setStyleSheet("""
            color: #8E8E8E;
            font-family: arial;
            font-size: 12px;
            padding: 0 4px;
        """)
        return label

    def _top_level_navigation_entries(self):
        return [
            (self.dashboard_button, self.dashboard),
            (self.business_button, self.business),
            (self.profile_button, self.profile),
            (self.supplier_button, self.supplier),
            (self.salesrep_button, self.salesrep),
            (self.purchase_button, self.purchase),
            (self.po_button, self.po),
            (self.grn_button, self.grn),
            (self.sales_button, self.base_sales),
            (self.customer_button, self.base_customer),
            (self.product_button, self.product),
            (self.employee_button, self.employee),
            (self.transaction_button, self.transaction),
            (self.purchase_return, self.purchasereturn),
            (self.sales_return, self.salesreturn),
            (self.expense_button, self.expense),
            (self.reports_button, self.reports),
        ]

    def _top_nav_group_definitions(self):
        return [
            ("Sales", [self.sales_button]),
            ("Purchase", [self.purchase_button, self.po_button, self.grn_button, self.salesrep_button]),
            ("Returns", [self.purchase_return, self.sales_return]),
            ("Inventory", [self.product_button]),
            ("People", [self.customer_button, self.supplier_button, self.employee_button]),
            ("Finance", [self.transaction_button, self.expense_button, self.business_button]),
        ]

    def _sidebar_button_label(self, sidebar_button):
        return getattr(sidebar_button, "_full_text", "") or sidebar_button.text().strip()

    def _refresh_top_navigation_strip(self):
        if not hasattr(self, "top_nav_menu_layout"):
            return

        self._clear_layout_widgets(self.top_nav_menu_layout)
        if hasattr(self, "top_nav_right_dynamic_layout"):
            self._clear_layout_widgets(self.top_nav_right_dynamic_layout)
        current_main = self.main_content_layout.currentWidget() if hasattr(self, "main_content_layout") else None
        self._top_nav_search_targets = {}

        top_level_entries = self._top_level_navigation_entries()
        visible_entries = []
        for sidebar_button, widget in top_level_entries:
            if sidebar_button.isHidden():
                continue
            label = self._sidebar_button_label(sidebar_button)
            if label:
                self._top_nav_search_targets[label.lower()] = sidebar_button
            visible_entries.append((sidebar_button, widget))

        dashboard_entry = next(((btn, widget) for btn, widget in visible_entries if btn is self.dashboard_button), None)
        if dashboard_entry is not None:
            dashboard_button, dashboard_widget = dashboard_entry
            dashboard_nav = self._create_top_nav_text_button(
                self._sidebar_button_label(dashboard_button),
                callback=dashboard_button.click,
                active=(dashboard_widget is current_main),
                enabled=dashboard_button.isEnabled(),
            )
            self.top_nav_menu_layout.addWidget(dashboard_nav, 0, Qt.AlignVCenter)

        widget_by_button = {button: widget for button, widget in visible_entries}
        for group_label, group_buttons in self._top_nav_group_definitions():
            group_entries = []
            group_active = False
            for sidebar_button in group_buttons:
                if sidebar_button.isHidden():
                    continue
                label = self._sidebar_button_label(sidebar_button)
                group_entries.append((label, sidebar_button.click, sidebar_button.isEnabled()))
                if widget_by_button.get(sidebar_button) is current_main:
                    group_active = True
            if not group_entries:
                continue
            menu_button = self._create_top_nav_menu_button(group_label, group_entries, active=group_active)
            self.top_nav_menu_layout.addWidget(menu_button, 0, Qt.AlignVCenter)

        if not self.reports_button.isHidden():
            reports_nav = self._create_top_nav_text_button(
                self._sidebar_button_label(self.reports_button),
                callback=self.reports_button.click,
                active=(self.reports is current_main),
                enabled=self.reports_button.isEnabled(),
            )
            self.top_nav_menu_layout.addWidget(reports_nav, 0, Qt.AlignVCenter)

        self.top_nav_search_model.setStringList(
            sorted(
                [self._sidebar_button_label(btn) for btn in self._top_nav_search_targets.values()],
                key=str.lower,
            )
        )

        if hasattr(self, "top_nav_sidebar_toggle_btn"):
            self.top_nav_sidebar_toggle_btn.setText("Show Sidebar" if self.sidebar_force_hidden else "Hide Sidebar")

    def _handle_top_nav_search_choice(self, text):
        self._navigate_from_top_nav_label(text)

    def _handle_top_nav_search_submit(self):
        self._navigate_from_top_nav_label(self.top_nav_search.text())

    def _navigate_from_top_nav_label(self, raw_text):
        label = (raw_text or "").strip().lower()
        if not label:
            return

        target_button = self._top_nav_search_targets.get(label)
        if target_button is None:
            for candidate_label, sidebar_button in self._top_nav_search_targets.items():
                if candidate_label.startswith(label):
                    target_button = sidebar_button
                    break

        if target_button is None or not target_button.isEnabled():
            return

        target_button.click()
        self.top_nav_search.clear()

    def _handle_sidebar_profile_click(self, event):
        self._open_profile_from_sidebar_footer()
        event.accept()

    def _open_profile_from_sidebar_footer(self):
        if hasattr(self, "main_content_layout"):
            self.set_profile(None, self.main_content_layout)

    def _toggle_force_hide_sidebar(self):
        self.sidebar_force_hidden = not bool(self.sidebar_force_hidden)
        self._refresh_top_navigation_strip()
        self._update_navigation_mode_visibility()
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)

    def _update_navigation_mode_visibility(self):
        if hasattr(self, "top_nav_widget"):
            self.top_nav_widget.setVisible(bool(getattr(self, "sidebar_collapsed", False) or getattr(self, "sidebar_force_hidden", False)))
        if hasattr(self, "header_widget"):
            self.header_widget.setVisible(not bool(getattr(self, "sidebar_collapsed", False) or getattr(self, "sidebar_force_hidden", False)))
        if hasattr(self, "sidebar_scroll"):
            self.sidebar_scroll.setVisible(not bool(getattr(self, "sidebar_force_hidden", False)))
        if hasattr(self, "sidebar_rail_scroll"):
            self.sidebar_rail_scroll.setVisible(bool(getattr(self, "sidebar_force_hidden", False)))
        self._update_header_sidebar_slot()

    def _update_header_sidebar_slot(self):
        if not hasattr(self, "header_sidebar_slot"):
            return

        slot_width = 0 if (getattr(self, "sidebar_collapsed", False) or getattr(self, "sidebar_force_hidden", False)) else int(getattr(self, "sidebar_expanded_width", 0) or 0)
        self.header_sidebar_slot.setFixedWidth(slot_width)
        self.header_sidebar_slot.setMinimumWidth(slot_width)
        self.header_sidebar_slot.setMaximumWidth(slot_width)
        self.header_sidebar_slot.setVisible(slot_width > 0)

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
        rail_width = self.sidebar_rail_width if getattr(self, "sidebar_force_hidden", False) else 0
        self.sidebar_rail_scroll.setFixedWidth(rail_width)
        self.sidebar_rail_scroll.setMinimumWidth(rail_width)
        self.sidebar_rail_scroll.setMaximumWidth(rail_width)

        target_width = 0 if getattr(self, "sidebar_force_hidden", False) else (self.sidebar_collapsed_width if self.sidebar_collapsed else self.sidebar_expanded_width)
        self._set_sidebar_column_width(target_width)
        if getattr(self, "sidebar_force_hidden", False):
            self.sidebar_scroll.hide()
            self.sidebar_rail_scroll.show()
        else:
            self.sidebar_scroll.show()
            self.sidebar_rail_scroll.hide()

        if hasattr(self, "content_area_widget"):
            self.content_area_widget.setMinimumWidth(0)
            self.content_area_widget.updateGeometry()

        if hasattr(self, "main_content_widget"):
            self.main_content_widget.setMinimumWidth(0)
            self.main_content_widget.updateGeometry()

        if hasattr(self, "workspace_widget"):
            self.workspace_widget.setMinimumWidth(0)
            self.workspace_widget.updateGeometry()

        current = self.main_content_layout.currentWidget() if hasattr(self, "main_content_layout") else None
        if current is not None:
            current.updateGeometry()

        if hasattr(self, "workspace_layout"):
            self.workspace_layout.invalidate()
            self.workspace_layout.activate()
        self.layout.invalidate()
        self.layout.activate()
        self.widget.updateGeometry()
        self.widget.update()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_shell_layout()
        QTimer.singleShot(0, self._sync_shell_layout)
        self._schedule_background_page_warmup()

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
