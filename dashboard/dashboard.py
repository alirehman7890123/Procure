from PySide6.QtWidgets import QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QPushButton, QLabel, QFrame, QComboBox
from PySide6.QtCore import Qt, QFile, QDate
import sys, os
from PySide6.QtSql import QSqlQuery, QSqlDatabase
from PySide6.QtCore import QDate



import os
import sys


def resource_path(relative_path):
    """Return the absolute path to a resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS  # PyInstaller extracts files here
    except AttributeError:
        base_path = os.path.abspath(".")  # running from source
    return os.path.join(base_path, relative_path)



def load_stylesheets():
    """Load and combine all CSS files from the styles folder."""
    styles_dir = resource_path("styles")
    css_content = ""

    if os.path.exists(styles_dir):
        for file in os.listdir(styles_dir):
            if file.endswith(".css"):
                css_file = os.path.join(styles_dir, file)
                with open(css_file, "r") as f:
                    css_content += f.read() + "\n"
                    
    return css_content





class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # main vertical layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Business Dashboard", objectName="SectionTitle")
        # self.supplierlist = QPushButton("Date / Time", objectName="TopRightButton")
        # self.supplierlist.setCursor(Qt.PointingHandCursor)
        # self.supplierlist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        # header_layout.addWidget(self.supplierlist)

        self.layout.addLayout(header_layout)
        
        line = QFrame()
        line.setObjectName("lineSeparator")

        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
                QFrame#lineSeparator {
                    border: none;
                    border-top: 2px solid #333;
                }
            """)


        self.layout.addWidget(line)
        self.layout.addSpacing(10)

        
        filter_row = QHBoxLayout()
        
        select_label = QLabel('Select Duration for Insights')
        select_label.setStyleSheet("padding-left: 0px;")
        filter_row.addWidget(select_label, 0, Qt.AlignLeft)
        
        select_duration = QComboBox()
        select_duration.addItems(['Today', 'Past Week', 'Past Month', 'Past Year', 'All']) 
        select_duration.setFixedWidth(200)
        
        filter_row.addWidget(select_duration, 1, Qt.AlignLeft)
        
        select_duration.currentIndexChanged.connect(self.on_duration_changed)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate())
        
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate()) 
        
        filter_row.addWidget(self.date_from)
        filter_row.addWidget(self.date_to)
        
        self.layout.addLayout(filter_row)
        
        
        card_row = QHBoxLayout()
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        card1 = QWidget()
        card1.setObjectName("card")
        card1.setMinimumWidth(250)
        card1.setFixedHeight(150)
        card1.setStyleSheet("background-color: #47034E; border-radius: 5px; color: #fff;")
        
        card1.setSizePolicy(policy)
        
        card1_layout = QVBoxLayout(card1)
        
        
        
        card1_title = QLabel("Total Sales")
        card1_title.setObjectName("cardTitle")
        card1_title.setStyleSheet("font-size: 16px;")
        
        self.card1_data = QLabel("0.00")
        self.card1_data.setObjectName("cardData")
        self.card1_data.setAlignment(Qt.AlignCenter)
        self.card1_data.setStyleSheet("font-size: 40px;")
        
        self.card1_bottom = QLabel("Invoice(s)")
        self.card1_bottom.setObjectName("cardBottom")
        self.card1_bottom.setAlignment(Qt.AlignCenter)
        self.card1_bottom.setStyleSheet("font-size: 12px;")
        
        card1_layout.addWidget(card1_title)
        card1_layout.addWidget(self.card1_data)
        card1_layout.addWidget(self.card1_bottom)


        card2 = QWidget()
        
        card2.setObjectName("card")
        card2.setMinimumWidth(250)
        card2.setFixedHeight(150)
        card2.setStyleSheet("background-color: #47034E; border-radius: 5px; color: #fff;")
        card2.setSizePolicy(policy)
        
        card2_layout = QVBoxLayout(card2)
        
        card2_title = QLabel("Purchase Info")
        card2_title.setObjectName("cardTitle")
        card2_title.setStyleSheet("font-size: 16px;")
        
        self.card2_data = QLabel("0.00")
        self.card2_data.setObjectName("cardData")
        self.card2_data.setAlignment(Qt.AlignCenter)
        self.card2_data.setStyleSheet("font-size: 40px;")
        
        self.card2_bottom = QLabel("No of invoice")
        self.card2_bottom.setObjectName("cardBottom")
        self.card2_bottom.setAlignment(Qt.AlignCenter)
        self.card2_bottom.setStyleSheet("font-size: 12px;")
        
        card2_layout.addWidget(card2_title)
        card2_layout.addWidget(self.card2_data)
        card2_layout.addWidget(self.card2_bottom)
        
        
        
        card3 = QWidget()
        
        card3.setObjectName("card")
        card3.setMinimumWidth(250)
        card3.setFixedHeight(150)
        card3.setStyleSheet("background-color: #47034E; border-radius: 5px; color: #fff;")
        card3.setSizePolicy(policy)
        
        card3_layout = QVBoxLayout(card3)
        
        card3_title = QLabel("Expenses")
        card3_title.setObjectName("cardTitle")
        card3_title.setStyleSheet("font-size: 16px;")
        
        self.card3_data = QLabel("0.00")
        self.card3_data.setObjectName("cardData")
        self.card3_data.setAlignment(Qt.AlignCenter)
        self.card3_data.setStyleSheet("font-size: 40px;")
        
        self.card3_bottom = QLabel("No of invoice")
        self.card3_bottom.setObjectName("cardBottom")
        self.card3_bottom.setAlignment(Qt.AlignCenter)
        self.card3_bottom.setStyleSheet("font-size: 12px;")
        
        card3_layout.addWidget(card3_title)
        card3_layout.addWidget(self.card3_data)
        card3_layout.addWidget(self.card3_bottom)
        
        card_row.addWidget(card1, 1)
        card_row.addWidget(card2, 1)
        card_row.addWidget(card3, 1)
        
        card_row.setAlignment(Qt.AlignLeft)
        self.layout.addLayout(card_row)
        
        self.layout.addSpacing(20)
        
        
        
        
        
        stock_row = QHBoxLayout()
        
        
        card4 = QWidget()
        
        card4.setObjectName("card")
        card4.setMinimumWidth(330)
        card4.setFixedHeight(150)
        card4.setStyleSheet("background-color: #47034E; border-radius: 5px; color: #fff;")
        card4.setSizePolicy(policy)
        
        card4_layout = QVBoxLayout(card4)
        
        card4_title = QLabel("Stock")
        card4_title.setObjectName("cardTitle")
        card4_title.setStyleSheet("font-size: 16px;")
        
        # total Products row
        total_products_row = QHBoxLayout()
        
        total_products_label = QLabel('Total Products: ')
        self.total_products_data = QLabel('')
        
        total_products_row.addWidget(total_products_label, 1)
        total_products_row.addWidget(self.total_products_data, 1)
        
        card4_layout.addLayout(total_products_row)
        
        # low stock row
        
        low_stock_row = QHBoxLayout()
        
        low_stock_label = QLabel('Low Stock Products: ')
        self.low_stock_data = QLabel('')
        
        low_stock_row.addWidget(low_stock_label, 1)
        low_stock_row.addWidget(self.low_stock_data, 1)
        
        card4_layout.addLayout(low_stock_row)
        
        
        
        
        
        
        
        card5 = QWidget()
        
        card5.setObjectName("card")
        card5.setMinimumWidth(330)
        card5.setFixedHeight(150)
        card5.setStyleSheet("background-color: #47034E; border-radius: 5px; color: #fff;")
        card5.setSizePolicy(policy)
        
        card5_layout = QVBoxLayout(card5)
        
        card4_title = QLabel("OutStanding Dues")
        card4_title.setObjectName("cardTitle")
        card4_title.setStyleSheet("font-size: 16px;")
        
        supplier_row = QHBoxLayout()
        
        supplier_label = QLabel('Supplier Dues: ')
        self.supplier_payable = QLabel('0.00')
        self.supplier_receiveable = QLabel('0.00')
        
        supplier_row.addWidget(supplier_label, 1)
        supplier_row.addWidget(self.supplier_payable, 1)
        supplier_row.addWidget(self.supplier_receiveable, 1)
        
        card5_layout.addLayout(supplier_row)
        
        # low stock row
        
        customer_row = QHBoxLayout()
        
        customer_label = QLabel('Customer Dues: ')
        self.customer_payable = QLabel('0.00')
        self.customer_receiveable = QLabel('0.00')
        
        customer_row.addWidget(customer_label, 1)
        customer_row.addWidget(self.customer_payable, 1)
        customer_row.addWidget(self.customer_receiveable, 1)
        
        card5_layout.addLayout(customer_row)
        
        
        
        stock_row.addWidget(card4)
        stock_row.addWidget(card5)

        self.layout.addLayout(stock_row)
        
        
        
        # add label and hbox to main layout
        self.layout.addStretch()
        
        total_sales, total_invoices = self.get_sales_summary('today')
        
        self.card1_data.setText(f"{total_sales:.2f}")
        self.card1_bottom.setText(f"{total_invoices} Invoice(s) ")
        
        total_expense, num_records = self.get_total_expenses('today')
        self.card3_data.setText(f"{total_expense:.2f}")
        self.card3_bottom.setText(f"{num_records} Expense(s) ")
        
        # Card 2 = Purchase Invoices
        total_purchase, invoice_count = self.get_purchase_summary('today')
        
        self.card2_data.setText(f"{total_purchase:.2f}")
        self.card2_bottom.setText(f"{total_invoices} Invoice(s) ")
        
        
        
        
        self.get_stock_summary()
        self.get_supplier_summary()
        self.get_customer_summary()
        
        
        # set stylesheets
        self.setStyleSheet(load_stylesheets())
        






    def get_sales_summary(self, duration="today"):
        """
        Fetch total sales and invoice count for a given duration.
        
        duration: str
            "today", "week", "month", "year", "all"
        Returns:
            total_sales (float), total_invoices (int)
        """
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            print("Database is not open")
            return 0, 0

        # Build WHERE clause using date ranges
        duration = duration.lower()
        if duration == "today":
            where_clause = "DATE(creation_date) = DATE('now')"
        elif duration == "week":
            # Last 7 days including today
            where_clause = "DATE(creation_date) >= DATE('now','-6 days')"
        elif duration == "month":
            # Last 30 days including today
            where_clause = "DATE(creation_date) >= DATE('now','-29 days')"
        elif duration == "year":
            # Last 1 year including today
            where_clause = "DATE(creation_date) >= DATE('now','-1 year')"
        elif duration == "all":
            where_clause = "1=1"
        else:
            print("Invalid duration. Use: today, week, month, year, all.")
            return 0, 0

        # Query total sales and invoice count
        query = QSqlQuery()
        sql = f"""
            SELECT IFNULL(SUM(total),0), COUNT(*)
            FROM sales
            WHERE {where_clause}
        """
        if not query.exec(sql):
            print("Query failed:", query.lastError().text())
            return 0, 0

        total_sales = 0
        total_invoices = 0
        if query.next():
            total_sales = query.value(0) or 0
            total_invoices = query.value(1) or 0

        return total_sales, total_invoices



    def get_purchase_summary(self, duration="today"):
        """
        Fetch total purchase amount and number of purchase invoices for a given duration.
        
        duration: str
            "today", "week", "month", "year", "all"
        Returns:
            total_purchase (float), total_invoices (int)
        """
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            print("Database is not open")
            return 0.0, 0

        # Build WHERE clause using date ranges
        duration = duration.lower()
        if duration == "today":
            where_clause = "DATE(creation_date) = DATE('now')"
        elif duration == "week":
            where_clause = "DATE(creation_date) >= DATE('now','-6 days')"
        elif duration == "month":
            where_clause = "DATE(creation_date) >= DATE('now','-29 days')"
        elif duration == "year":
            where_clause = "DATE(creation_date) >= DATE('now','-1 year')"
        elif duration == "all":
            where_clause = "1=1"
        else:
            print("Invalid duration. Use: today, week, month, year, all.")
            return 0.0, 0

        # Query total purchases and invoice count
        query = QSqlQuery()
        sql = f"""
            SELECT IFNULL(SUM(total),0), COUNT(*)
            FROM purchase
            WHERE {where_clause}
        """
        if not query.exec(sql):
            print("Query failed:", query.lastError().text())
            return 0.0, 0

        total_purchase = 0.0
        total_invoices = 0
        if query.next():
            total_purchase = query.value(0) or 0.0
            total_invoices = query.value(1) or 0

        return total_purchase, total_invoices





    from PySide6.QtSql import QSqlQuery

    def get_total_expenses(self, duration="today"):
        """
        Fetch total expenses and number of expense records for a given duration.

        duration: str
            "today", "week", "month", "year", "all"
        Returns:
            total_expenses (float), num_records (int)
        """
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            print("Database is not open")
            return 0.0, 0

        # Build WHERE clause using date ranges
        duration = duration.lower()
        if duration == "today":
            where_clause = "DATE(creation_date) = DATE('now')"
        elif duration == "week":
            where_clause = "DATE(creation_date) >= DATE('now','-6 days')"
        elif duration == "month":
            where_clause = "DATE(creation_date) >= DATE('now','-29 days')"
        elif duration == "year":
            where_clause = "DATE(creation_date) >= DATE('now','-1 year')"
        elif duration == "all":
            where_clause = "1=1"
        else:
            print("Invalid duration. Use: today, week, month, year, all.")
            return 0.0, 0

        # Query total expenses and count of records
        query = QSqlQuery()
        sql = f"""
            SELECT IFNULL(SUM(amount),0), COUNT(*)
            FROM expense
            WHERE {where_clause}
        """
        if not query.exec(sql):
            print("Query failed:", query.lastError().text())
            return 0.0, 0

        total_expenses = 0.0
        num_records = 0
        if query.next():
            total_expenses = query.value(0) or 0.0
            num_records = query.value(1) or 0

        return total_expenses, num_records



    def get_stock_summary(self):
        """
        Fetch total products and low stock products.

        Returns:
            total_products (int), low_stock_products (int)
        """
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            print("Database is not open")
            return 0, 0

        # 1. Total products
        total_products = 0
        query = QSqlQuery()
        if query.exec("SELECT COUNT(*) FROM product"):
            if query.next():
                total_products = query.value(0) or 0
        else:
            print("Query failed for total products:", query.lastError().text())

        # 2. Low stock products
        low_stock_products = 0
        query2 = QSqlQuery()
        sql = "SELECT COUNT(*) FROM stock WHERE units <= reorder"
        if query2.exec(sql):
            if query2.next():
                low_stock_products = query2.value(0) or 0
        else:
            print("Query failed for low stock products:", query2.lastError().text())
            
        
        self.total_products_data.setText(f"{total_products}")
        self.low_stock_data.setText(f"{low_stock_products}")    
        

        return total_products, low_stock_products



    def get_supplier_summary(self):
        """
        Fetch total payable and total receivable for suppliers.

        Returns:
            total_payable (float), total_receivable (float)
        """
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            print("Database is not open")
            return 0.0, 0.0

        total_payable = 0.0
        total_receivable = 0.0

        query = QSqlQuery()
        sql = """
            SELECT IFNULL(SUM(payable_after),0), IFNULL(SUM(receiveable_after),0)
            FROM supplier_transaction
        """
        if query.exec(sql):
            if query.next():
                total_payable = query.value(0) or 0.0
                total_receivable = query.value(1) or 0.0
        else:
            print("Query failed for supplier summary:", query.lastError().text())
            
            
            
        self.supplier_payable.setText(f"{abs(total_payable)} ---payable")
        self.supplier_receiveable.setText(f"{abs(total_receivable)} ---receivables")



    

    def get_customer_summary(self):
        """
        Fetch total payable and total receivable for customers.

        Returns:
            total_payable (float), total_receivable (float)
        """
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            print("Database is not open")
            return 0.0, 0.0

        total_payable = 0.0       # Customers owe you
        total_receivable = 0.0    # You owe customers

        query = QSqlQuery()
        sql = """
            SELECT IFNULL(SUM(payable_after),0), IFNULL(SUM(receiveable_after),0)
            FROM customer_transaction
        """
        if query.exec(sql):
            if query.next():
                total_payable = query.value(0) or 0.0
                total_receivable = query.value(1) or 0.0
        else:
            print("Query failed for customer summary:", query.lastError().text())
            
            
        self.customer_payable.setText(f"{abs(total_payable)} ---payable")
        self.customer_receiveable.setText(f"{abs(total_receivable)} ----receivables")
        
        



    def on_duration_changed(self, index):
        # Map combo box selection to your method's duration parameter
        duration_map = {
            0: "today",
            1: "week",
            2: "month",
            3: "year",
            4: "all",
        }
        duration_key = duration_map.get(index, "today")

        # Card 1 = Sales Invoices
        total_sales, total_invoices = self.get_sales_summary(duration_key)
        self.card1_data.setText(f"{total_sales:.2f}")
        self.card1_bottom.setText(f"{total_invoices} Sales Invoice(s) ")
        
        
        # Card 2 = Purchase Invoices
        total_purchase, invoice_count = self.get_purchase_summary(duration_key)
        self.card2_data.setText(f"{total_purchase:.2f}")
        self.card2_bottom.setText(f"{invoice_count} Purchase Invoice(s) ")
        
        
        # Card 3 = Expenses
        total_expenses, num_records = self.get_total_expenses(duration_key)
        self.card3_data.setText(f"{total_expenses:.2f}")
        self.card3_bottom.setText(f"{num_records} Expense(s) ")
        
        
        
        
        
        
        
        
        


