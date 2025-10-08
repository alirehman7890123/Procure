from PySide6.QtWidgets import QWidget, QSizePolicy, QPushButton, QLabel, QHBoxLayout, QFrame, QLineEdit, QVBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, QDate, QDateTime
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from utilities.stylus import load_stylesheets




class SalesDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Receipt Detail", objectName="SectionTitle")
        self.receiptlist = QPushButton("Receipt List", objectName="TopRightButton")
        self.receiptlist.setCursor(Qt.PointingHandCursor)
        self.receiptlist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.receiptlist)

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
        self.layout.addSpacing(20)
        
        
        labels = ["Receipt Id", "Customer", "Salesman",  "Order Date"]
        
        
        self.orderid = QLabel()
        self.customer = QLabel()
        self.salesman = QLabel()
        self.orderdate = QLabel()
        
        fields = [self.orderid, self.customer, self.salesman, self.orderdate]
        
        for (label, field) in zip(labels, fields):

            row = QHBoxLayout()
            
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(lbl, 2)
            row.addWidget(field, 8)

            self.layout.addLayout(row)
            
        
        
        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10])
        headers = ["##", "Product", "Qty", "Rate", "Disc (%)", "Disc", "Total"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        
        self.table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)   

        self.table.setMinimumWidth(1000)
        
        # Hide vertical header (row numbers)
        self.table.verticalHeader().setVisible(False)
        
        # Alternating row colors
        self.table.setAlternatingRowColors(True)

        # Selection behaviour
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        
        self.layout.addStretch()    
        

        
        labels = ["Sub Total", "Discount", "Tax", "Total", "Round off", "Final Amount"]
        
        self.subtotal = QLabel()
        self.discount = QLabel()
        self.tax = QLabel()
        self.total = QLabel()
        self.roundoff = QLabel()
        self.finalamount = QLabel()
        
        fields = [ self.subtotal, self.discount, self.tax, self.total, self.roundoff, self.finalamount ]
        
        
        for (label, field) in zip(labels, fields):

            row = QHBoxLayout()

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(lbl, 2)
            row.addWidget(field, 8)

            self.layout.addLayout(row)
            
        
            
        self.layout.addStretch()
            
        # Load and Apply CSS
        self.setStyleSheet(load_stylesheets())

        
        




    def load_sales_data(self, id):
        
        print("Loading Sales ID:", id)
        query = QSqlQuery()
        query.prepare("SELECT customer,salesman,creation_date,subtotal,discamount,taxamount,totalaftertax,roundoff,total FROM sales WHERE id = ?")
        query.addBindValue(id)
        
        if query.exec() and query.next():
            
            customerid = query.value(0)
            
            print("Customer is ...... ", customerid)
            
            if customerid is None or customerid == '':
                customerid = 0
            
            if customerid != 0:
                
                customerid = int(customerid)
                customerquery = QSqlQuery()
                customerquery.prepare("SELECT name FROM customer WHERE id = ?")
                customerquery.addBindValue(customerid)
                
                if customerquery.exec() and customerquery.next():
                    customer = customerquery.value(0)
                else:
                    print("Customer not found for ID:", customerid)
                
            else:
                customer = 'Walk-in Customer'
                
            
            salesmanid = int(query.value(1))
            invoicedate = query.value(2)
            
            subtotal = float(query.value(3))
            discount = float(query.value(4))
            tax = float(query.value(5))
            totalaftertax = float(query.value(6))
            roundoff = float(query.value(7))
            total = float(query.value(8))


            if isinstance(invoicedate, QDate):  # or QDateTime
                invoicedate = invoicedate.toString("dd-MM-yyyy")  # or "yyyy-MM-dd"
            else:
                invoicedate = str(invoicedate)
                
            
            salesmanquery = QSqlQuery()
            salesmanquery.prepare("SELECT firstname, lastname FROM auth WHERE id = ?")
            salesmanquery.addBindValue(salesmanid)

            if salesmanquery.exec() and salesmanquery.next():
                firstname = salesmanquery.value(0)
                lastname = salesmanquery.value(1)
                
                salesman = f"{firstname} {lastname}"
            else:
                print("Salesman not found for ID:", salesmanid)
                
            self.orderid.setText(str(id))
            self.customer.setText(str(customer))
            self.salesman.setText(str(salesman))
            self.orderdate.setText(str(invoicedate))
            self.subtotal.setText(str(subtotal))
            self.discount.setText(str(discount))
            self.tax.setText(str(tax))
            self.total.setText(str(totalaftertax))
            self.roundoff.setText(str(roundoff))
            self.finalamount.setText(str(total))
        
            print("Sales data loaded successfully for ID:", id)
            
            
            self.load_items_into_table(id)
            
            




    def load_items_into_table(self, sale_id):
        print("Loading items into table")

        query = QSqlQuery()
        query.prepare("""
            SELECT product, qty, unitrate, discount, discountamount, total
            FROM salesitem 
            WHERE sales = ?
        """)
        query.addBindValue(sale_id)

        self.table.setRowCount(0)  # Clear existing rows
        row = 0

        if query.exec():
            while query.next():
                self.table.insertRow(row)

                product_id = int(query.value(0))
                qty = str(query.value(1))
                rate = str(query.value(2))
                discount = str(query.value(3))
                discount_amount = str(query.value(4))
                total = str(query.value(5))

                # Get product name
                product_name = ""
                query2 = QSqlQuery()
                query2.prepare("SELECT name FROM product WHERE id = ?")
                query2.addBindValue(product_id)

                if query2.exec() and query2.next():
                    product_name = query2.value(0)

                # Table items
                counter_item = QTableWidgetItem(str(row + 1))
                product_item = QTableWidgetItem(product_name)
                qty_item = QTableWidgetItem(qty)
                rate_item = QTableWidgetItem(rate)
                discount_item = QTableWidgetItem(discount)
                discount_amount_item = QTableWidgetItem(discount_amount)
                total_item = QTableWidgetItem(total)

                # Set into table
                self.table.setItem(row, 0, counter_item)
                self.table.setItem(row, 1, product_item)
                self.table.setItem(row, 2, qty_item)
                self.table.setItem(row, 3, rate_item)
                self.table.setItem(row, 4, discount_item)
                self.table.setItem(row, 5, discount_amount_item)
                self.table.setItem(row, 6, total_item)

                row += 1
        else:
            print("Query failed:", query.lastError().text())

                
            



class MyTable(QTableWidget):
    
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # user can drag

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            col_width = int(width * (ratio / total))
            self.setColumnWidth(i, col_width)


            
        









