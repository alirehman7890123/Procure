
from PySide6.QtWidgets import QApplication, QWidget,QTableWidget, QMainWindow,QMessageBox, QPushButton, QHBoxLayout, QVBoxLayout, QStackedLayout, QLabel,  QSizePolicy
from PySide6.QtCore import QSize, Qt, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import QScrollArea
from utilities.sidebarbutton import SideBarButton

from utilities.database import SQLiteConnectionManager
# from database import PostgresConnectionManager
from PySide6.QtGui import QPalette, QColor, QPixmap, QIcon
from business.basebusiness import BaseBusinessWidget
from supplier.basesupplier import BaseSupplierWidget
from salesrep.basesalesrep import BaseSalesRepWidget
from customer.basecustomer import BaseCustomerWidget
from product.baseproduct import BaseProductWidget
from userprofile.baseprofile import BaseProfileWidget
from purchase.basepurchase import BasePurchaseWidget
from sales.basesales import BaseSalesWidget
from employee.baseemployee import BaseEmployeeWidget
from transaction.basetransaction import BaseTransactionWidget
from purchasereturn.base_purchase_return import BasePurchaseReturnWidget
from salesreturn.base_sales_return import BaseSalesReturnWidget
from expense.baseexpense import BaseExpenseWidget
from reports.basereports import BaseReportsWidget
from salehold.basehold import BaseHoldSalesWidget

from dashboard.dashboard import DashboardWidget
from dashboard.welcome import WelcomeWidget
from utilities.sizehintfinder import print_size_hints
from functools import wraps
from PySide6.QtWidgets import QMessageBox, QApplication
from utilities.permissions import Permissions



permission = Permissions()


import sys
import os


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
        
        self.setWindowTitle('ProCure Medical - Login')
        
        connection = SQLiteConnectionManager('ProcureApp')
        # connection = PostgresConnectionManager()
        connection.open()
        
        screen_geometry = QApplication.primaryScreen().geometry()
        
        width = screen_geometry.width()
        height = screen_geometry.height()
        
        self.setGeometry(0,0, width, height)
        
        
        self.history = []
        self.current_index = 0

        
        
        
        # Self Widget and Layout
        
        self.widget = QWidget()
        self.layout = QHBoxLayout()
        self.reset_widget_size(self.layout, self.widget)

        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
       
        
        
        # SIDE-BAR SCROLL
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setFixedWidth(210)
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        sidebar_scroll.setStyleSheet(""" 
                                    background-color: #47034E;
                                    
                                    QScrollArea {
                                        background-color: #47034E;
                                        border: none;
                                    }
                                """)
    
    
        # SIDE-BAR WIDGET
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        
        self.reset_widget_size(sidebar_layout, sidebar_widget)
        

        sidebar_widget.setLayout(sidebar_layout)
        sidebar_scroll.setWidget(sidebar_widget)
        
        
        
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

        self.header_widget.setLayout(header_layout)
        self.header_widget.setStyleSheet("""color: #333; border-bottom: 3px solid #333;""")
        
        
        ham = QPushButton()
        ham.setCursor(Qt.PointingHandCursor)
        ham.setStyleSheet('border: none;')
        ham.setCheckable(True)
        ham.setChecked(True)

        icon = QIcon(QPixmap(resource_path("res/ham.png")))
        ham.setIcon(icon)

        ham.toggled.connect(lambda: self.toggle_sidebar(sidebar_scroll, ham))

        header_layout.addWidget(ham)
        
        business_title = QLabel("Muzammil Traders")
        business_name = self.set_business_name()
        business_title.setText(business_name)
        
        font = business_title.font()
        font.setUnderline(False)
        business_title.setFont(font)
        business_title.setStyleSheet("border:none; font-family: 'arial'; font-size: 20px; margin-left: 20px; font-weight: 700;")
        
        header_layout.addWidget(business_title)
        
        # self.back_button = QPushButton("Back")
        # header_layout.addWidget(self.back_button)
        
        # self.forward_button = QPushButton("Forward")
        # header_layout.addWidget(self.forward_button)
        
        
        
        
       
        header_layout.addStretch()
        
        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet("color: #fff; border-radius: 5px; padding: 5px 10px; background-color:  #47034E; margin-right: 20px;")
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
        
        self.main_content_widget.setStyleSheet("background-color: #fff;")
        
        
        
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
        self.sales_button = SideBarButton('Sales')
        self.customer_button = SideBarButton('Customers')
        self.product_button = SideBarButton('Product')
        self.employee_button = SideBarButton('Employees')
        self.transaction_button = SideBarButton('Transactions')
        self.purchase_return = SideBarButton('Purchase Return')
        self.sales_return = SideBarButton('Sales Return')
        self.expense_button = SideBarButton('Expenses')
        self.reports_button = SideBarButton('Reports')
        self.holdsales_button = SideBarButton('On-Hold Sales')
        
        footer_button = QPushButton()
        footer_button.setStyleSheet("""
                                    margin-top: 100px;
                                    background-color: #47034E;
                                    padding-right: 0px;
                                    height: 0px;
                                    """)

        button_styles = """
        
            QPushButton {
                padding: 15px 0;
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
                background-color: #000755;
                color: #fff;
            }
            
        """

        self.dashboard_button.setStyleSheet(button_styles)
        self.business_button.setStyleSheet(button_styles)
        self.profile_button.setStyleSheet(button_styles)
        self.supplier_button.setStyleSheet(button_styles)
        self.salesrep_button.setStyleSheet(button_styles)
        self.purchase_button.setStyleSheet(button_styles)
        self.customer_button.setStyleSheet(button_styles)
        self.product_button.setStyleSheet(button_styles)
        self.sales_button.setStyleSheet(button_styles)
        self.employee_button.setStyleSheet(button_styles)
        self.transaction_button.setStyleSheet(button_styles)
        self.purchase_return.setStyleSheet(button_styles)
        self.sales_return.setStyleSheet(button_styles)
        self.expense_button.setStyleSheet(button_styles)
        self.reports_button.setStyleSheet(button_styles)
        self.holdsales_button.setStyleSheet(button_styles)
        
        

        self.dashboard_button.setCursor(Qt.PointingHandCursor)
        self.business_button.setCursor(Qt.PointingHandCursor)
        self.profile_button.setCursor(Qt.PointingHandCursor)
        self.supplier_button.setCursor(Qt.PointingHandCursor)
        self.salesrep_button.setCursor(Qt.PointingHandCursor)
        self.purchase_button.setCursor(Qt.PointingHandCursor)
        self.customer_button.setCursor(Qt.PointingHandCursor)
        self.product_button.setCursor(Qt.PointingHandCursor)
        self.sales_button.setCursor(Qt.PointingHandCursor)
        self.employee_button.setCursor(Qt.PointingHandCursor)
        self.transaction_button.setCursor(Qt.PointingHandCursor)
        self.purchase_return.setCursor(Qt.PointingHandCursor)
        self.sales_return.setCursor(Qt.PointingHandCursor)
        self.expense_button.setCursor(Qt.PointingHandCursor)
        self.reports_button.setCursor(Qt.PointingHandCursor)
        self.holdsales_button.setCursor(Qt.PointingHandCursor)


        sidebar_layout.addWidget(self.dashboard_button)
        sidebar_layout.addWidget(self.business_button)
        sidebar_layout.addWidget(self.profile_button)
        sidebar_layout.addWidget(self.supplier_button)
        sidebar_layout.addWidget(self.salesrep_button)
        sidebar_layout.addWidget(self.purchase_button)
        sidebar_layout.addWidget(self.sales_button)
        sidebar_layout.addWidget(self.customer_button)
        sidebar_layout.addWidget(self.product_button)
        sidebar_layout.addWidget(self.employee_button)
        sidebar_layout.addWidget(self.transaction_button)
        sidebar_layout.addWidget(self.purchase_return)
        sidebar_layout.addWidget(self.sales_return)
        sidebar_layout.addWidget(self.expense_button)
        sidebar_layout.addWidget(self.reports_button)
        sidebar_layout.addWidget(self.holdsales_button)
        
        sidebar_layout.addWidget(footer_button)

        sidebar_layout.addStretch()  # Push buttons to the top

    




        
        

        
        
        
        
        


        self.dashboard = DashboardWidget()
        self.welcome = WelcomeWidget()
        self.profile = BaseProfileWidget()
        self.business = BaseBusinessWidget()
        self.supplier = BaseSupplierWidget()
        
        
        self.salesrep = BaseSalesRepWidget()
        self.purchase = BasePurchaseWidget()
        
        self.base_sales = BaseSalesWidget(controller=self)
        
        self.base_customer = BaseCustomerWidget(controller=self)
        self.product = BaseProductWidget()
        self.employee = BaseEmployeeWidget()
        self.transaction = BaseTransactionWidget()
        self.purchasereturn = BasePurchaseReturnWidget()
        self.salesreturn = BaseSalesReturnWidget()
        self.expense = BaseExpenseWidget()
        self.reports = BaseReportsWidget()
        
        self.holdsales = BaseHoldSalesWidget(controller=self)
        
        

        self.dashboard_button.clicked.connect(lambda: self.set_dashboard(self.dashboard, self.main_content_layout))
        self.business_button.clicked.connect(lambda: self.set_business(self.business, self.main_content_layout))
        self.profile_button.clicked.connect(lambda: self.set_profile(self.profile, self.main_content_layout))
        self.supplier_button.clicked.connect(lambda: self.set_supplier(self.supplier, self.main_content_layout))
        self.salesrep_button.clicked.connect(lambda: self.set_salesrep(self.salesrep, self.main_content_layout))
        self.purchase_button.clicked.connect(lambda: self.set_salesrep(self.purchase, self.main_content_layout))
        self.sales_button.clicked.connect(lambda:self.set_sales(self.base_sales, self.main_content_layout))
        self.customer_button.clicked.connect(lambda: self.set_customer(self.base_customer, self.main_content_layout))
        self.product_button.clicked.connect(lambda: self.set_product(self.product, self.main_content_layout))
        self.employee_button.clicked.connect(lambda: self.set_employee(self.employee, self.main_content_layout))
        self.transaction_button.clicked.connect(lambda: self.set_transaction(self.transaction, self.main_content_layout))
        self.purchase_return.clicked.connect(lambda: self.set_purchasereturn(self.purchasereturn, self.main_content_layout))
        self.sales_return.clicked.connect(lambda: self.set_salesreturn(self.salesreturn, self.main_content_layout))
        self.expense_button.clicked.connect(lambda: self.set_expense(self.expense, self.main_content_layout))
        self.reports_button.clicked.connect(lambda: self.set_reports(self.reports, self.main_content_layout))
        self.holdsales_button.clicked.connect(lambda: self.set_holdsales(self.holdsales, self.main_content_layout))
        
        
        
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
        # QShortcut(QKeySequence("Ctrl+P"), self, activated=lambda: self.set_purchasereturn(self.purchasereturn, self.main_content_layout))  # Purchase Return
        # QShortcut(QKeySequence("Ctrl+S"), self, activated=lambda: self.set_salesreturn(self.salesreturn, self.main_content_layout))  # Sales Return
        # QShortcut(QKeySequence("Ctrl+E"), self, activated=lambda: self.set_expense(self.expense, self.main_content_layout))  # Expense
        # QShortcut(QKeySequence("Ctrl+R"), self, activated=lambda: self.set_reports(self.reports, self.main_content_layout))  # Reports
        # QShortcut(QKeySequence("Ctrl+H"), self, activated=lambda: self.set_holdsales(self.holdsales, self.main_content_layout))  # On-Hold Sales
        
        
        role = QApplication.instance().property('user_role')
        if role == 'admin' or role == 'manager':
            self.main_content_layout.addWidget(self.dashboard)
        else:
            self.main_content_layout.addWidget(self.welcome)
        
        
        self.main_content_layout.addWidget(self.business)
        self.main_content_layout.addWidget(self.profile)
        self.main_content_layout.addWidget(self.supplier)
        self.main_content_layout.addWidget(self.salesrep)
        self.main_content_layout.addWidget(self.purchase)
        self.main_content_layout.addWidget(self.base_sales)
        self.main_content_layout.addWidget(self.base_customer)
        self.main_content_layout.addWidget(self.product)
        self.main_content_layout.addWidget(self.employee)
        self.main_content_layout.addWidget(self.transaction)
        self.main_content_layout.addWidget(self.purchasereturn)
        self.main_content_layout.addWidget(self.salesreturn)
        self.main_content_layout.addWidget(self.expense)
        self.main_content_layout.addWidget(self.reports)
        self.main_content_layout.addWidget(self.holdsales)
        

        
        
        
        # making all widgets focusable
        self.make_all_focusable(self)

        
        self.layout.addWidget(sidebar_scroll)
        self.layout.addWidget(content_area_widget)
    
    
    
    
    
    def go_to_page(self, index):
        self.main_content_layout.setCurrentIndex(index)
        
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
            
        self.history.append(index)
        self.current_index = len(self.history) - 1

    def next_page(self):
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            self.main_content_layout.setCurrentIndex(self.history[self.current_index])

    def prev_page(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.main_content_layout.setCurrentIndex(self.history[self.current_index])
        
        
    
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
        reply = QMessageBox.question(
            self,
            "Logout Confirmation",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.close()                # Close main window
            QApplication.quit()
            
            
    
    
    
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


    def eventFilter(self, obj, event):
        if obj is self.table and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                if self.table.currentRow() == self.table.rowCount() - 1 and \
                self.table.currentColumn() == self.table.columnCount() - 1:
                    # last cell → move focus out
                    self.focusNextChild()
                    return True
            elif event.key() == Qt.Key_Backtab:
                if self.table.currentRow() == 0 and self.table.currentColumn() == 0:
                    # first cell + shift+tab → move focus backwards
                    self.focusPreviousChild()
                    return True
        return super().eventFilter(obj, event)

    
    
    
    
    
    
    @permission.require_permission('dashboard')
    def set_dashboard(self, widget, layout):
        layout.setCurrentWidget(widget)
        self.go_to_page(0)
        
    def set_business(self, widget, layout):
        layout.setCurrentWidget(widget)
        self.go_to_page(1)

    def set_profile(self, widget, layout):
        self.profile.reset_to_default()
        layout.setCurrentWidget(widget)
        self.go_to_page(2)

    def set_supplier(self, widget, layout):
        self.supplier.reset_to_default()
        layout.setCurrentWidget(widget)
        self.go_to_page(3)

    def set_salesrep(self, widget, layout):
        self.salesrep.reset_to_default()
        layout.setCurrentWidget(widget)
        self.go_to_page(4)
    
    def set_purchase(self, widget, layout):
        self.purchase.reset_to_default()
        layout.setCurrentWidget(widget)
        self.go_to_page(5)
    
    def set_sales(self, widget, layout):
        self.base_sales.reset_to_default()
        layout.setCurrentWidget(widget)
        self.go_to_page(6)

    def set_customer(self, widget, layout):
        self.base_customer.reset_to_default()
        layout.setCurrentWidget(widget)
        self.go_to_page(7)

    def set_product(self, widget, layout):
        self.product.reset_to_default()
        layout.setCurrentWidget(widget)

    def set_employee(self, widget, layout):
        self.employee.reset_to_default()
        layout.setCurrentWidget(widget)

    def set_transaction(self, widget, layout):
        self.transaction.reset_to_default()
        layout.setCurrentWidget(widget)

    def set_purchasereturn(self, widget, layout):
        self.purchasereturn.reset_to_default()
        layout.setCurrentWidget(widget)

    def set_salesreturn(self, widget, layout):
        self.salesreturn.reset_to_default()
        layout.setCurrentWidget(widget)


    def set_expense(self, widget, layout):
        self.expense.reset_to_default()
        layout.setCurrentWidget(widget)
    
        
    def set_reports(self, widget, layout):
        print("Setting Reports apge by clikcing")
        layout.setCurrentWidget(widget)
    
    
    def set_holdsales(self, widget, layout):
        layout.setCurrentWidget(widget)
    
 
    # Function to toggle sidebar visibility
    # This function is called when the hamburger button is toggled
    # It shows the sidebar when the button is checked and hides it when unchecked   


    def toggle_sidebar(self, sidebar, button):

        if button.isChecked():
            sidebar.show()
        else: 
            sidebar.hide()


    
    
    def reset_widget_size(self, layout, widget):
        
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        widget.setMinimumSize(0, 0)
        widget.setMaximumSize(16777215, 16777215)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)




if __name__ == '__main__':

    app = QApplication([])
    
    style = ""
    for css_file in css_files:
        path = resource_path(css_file)
        with open(path, "r") as f:
            style += f.read() + "\n"


    app.setStyleSheet(style)
    
    window = MainWindow()
    
    window.show()
    app.exec()
    
    
