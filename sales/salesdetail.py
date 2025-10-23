from PySide6.QtWidgets import QWidget, QSizePolicy, QPushButton, QLabel, QHBoxLayout, QFrame, QLineEdit, QVBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, QDate, QDateTime
from PySide6.QtSql import QSqlDatabase, QSqlQuery

import os
import sys
import platform
from PySide6.QtGui import QPdfWriter, QPainter, QPageSize, QFont, QTextOption, QPen, QColor
from PySide6.QtCore import Qt, QRectF

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
            
            
        
        print_button = QPushButton("Print Invoice", objectName="TopRightButton")
        print_button.clicked.connect(lambda: self.export_pdf('salesinvoice.pdf'))
            
        self.layout.addWidget(print_button)
            
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
        
        self.invoice_id = sale_id
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
            
        
        
        



    
    def export_pdf(self, filename="salesinvoice.pdf"):
        
        
        sales_id = self.invoice_id
        print("Exporting PDF")
        
        print("Sales id is: ", sales_id)
        
        # Loading Sales data 
        
        salesquery = QSqlQuery()
        salesquery.prepare("SELECT customer,salesman,creation_date,subtotal,discamount,taxamount,totalaftertax,roundoff,total FROM sales WHERE id = ?")
        salesquery.addBindValue(sales_id)
        
        if salesquery.exec() and salesquery.next():
            
            customerid = salesquery.value(0)
            
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
                
            
            salesmanid = int(salesquery.value(1))
            invoicedate = salesquery.value(2)

            subtotal = float(salesquery.value(3))
            salesdiscount = float(salesquery.value(4))
            salestax = float(salesquery.value(5))
            totalaftertax = float(salesquery.value(6))
            roundoff = float(salesquery.value(7))
            finaltotal = float(salesquery.value(8))


            if isinstance(invoicedate, QDate):  # or QDateTime
                invoicedate = invoicedate.toString("dd-MM-yyyy")  # or "yyyy-MM-dd"
            else:
                invoicedate = str(invoicedate)
                
            print("Invoice Date is: ", invoicedate)
            salesmanquery = QSqlQuery()
            salesmanquery.prepare("SELECT firstname, lastname FROM auth WHERE id = ?")
            salesmanquery.addBindValue(salesmanid)

            if salesmanquery.exec() and salesmanquery.next():
                firstname = salesmanquery.value(0)
                lastname = salesmanquery.value(1)
                
                salesman = f"{firstname} {lastname}"
            else:
                print("Salesman not found for ID:", salesmanid)
                
        else:
            print("Sales Error..., ", salesquery.lastError().text())
        
        # Loading Sales Items data
        
        query = QSqlQuery()
        query.prepare("""
            SELECT product, qty, unitrate, discount, discountamount, total
            FROM salesitem 
            WHERE sales = ?
        """)
        query.addBindValue(sales_id)
        
        items = []
        
        if query.exec():
            
            print("Query has been executed successfully")
            
            while query.next():
                
                product_id = int(query.value(0))
                qty = query.value(1)
                rate = query.value(2)
                discount = query.value(3)
                discount_amount = query.value(4)
                price = rate - discount_amount
                total = query.value(5)
                
                print("Rate is: ", rate)
                print("Discount is; ", discount)
                print("Discount Amount is: ", discount_amount)
                print("Price is: ", price)
                
                

                # Get product name
                product_name = ""
                query2 = QSqlQuery()
                query2.prepare("SELECT name, strength, form FROM product WHERE id = ?")
                query2.addBindValue(product_id)

                if query2.exec() and query2.next():
                    product_name = query2.value(0)
                    strength = query2.value(1)
                    form = query2.value(2)
                    if strength:
                        product_name += f" {strength}"
                    if form:
                        product_name += f" {form}"
                else:
                    print("Product not found for ID:", product_id)
                    
                items.append((product_name, qty, rate, discount, price, total))
                print(items)



        else:
            print("Query failed:", query.lastError().text())

        
    
        pdf = QPdfWriter(filename)
        pdf.setPageSize(QPageSize(QPageSize.A4))
        pdf.setResolution(300)

        

        painter = QPainter(pdf)
        painter.setFont(QFont("Arial", 12))
        painter.setPen(Qt.black)
        
        
        
        x = 100
        y = 200

        business_font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(business_font)

        business_name = "Muzammil Medical & General Store"
        painter.drawText(x, y, business_name)

        y += 80
        
        address_font = QFont("Arial", 12)
        painter.setFont(address_font)
        
        address = "123 Health St, Wellness City"
        painter.drawText(x, y, address)
        
        y += 70
        contact = "Phone: (123) 456-7890"
        painter.drawText(x, y, contact)
        
        
        invoice_font = QFont("Arial", 36, QFont.Bold)
        painter.setFont(invoice_font)

        invoice_title = "Invoice"
        painter.drawText(1700, 230, invoice_title)
        
        invoice_no_font = QFont("Arial", 12)
        painter.setFont(invoice_no_font)
        
        rect = QRectF(1700, 250, 500, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, f"# {sales_id}", option)
        
        
        invoice_date_font = QFont("Arial", 12)
        painter.setFont(invoice_date_font)

        rect = QRectF(1700, 320, 500, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, invoicedate, option)

        y += 150
        
        customer_font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(customer_font)
        painter.drawText(x, y, f"To: {customer}")
        
        y += 80
        
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x, y, pdf.width() - 200, y)
        
        y += 70
        header_font = QFont("Arial", 11, QFont.Bold)
        painter.setFont(header_font)

        item_name = "Item"
        painter.drawText(x + 20, y, item_name)
        
        item_name = "qty"
        painter.drawText(x + 900, y, item_name)
        
        item_name = "rate"
        painter.drawText(x + 1100, y, item_name)
        
        item_name = "discount"
        painter.drawText(x + 1400, y, item_name)
        
        item_name = "Price"
        painter.drawText(x + 1650, y, item_name)
        
        item_name = "Total"
        painter.drawText(x + 1900, y, item_name)

        
        y += 40
        
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x, y, pdf.width() - 200, y)

        y += 100
        
        items_font = QFont("Arial", 11)
        painter.setFont(items_font)
        
        # Sample items
        # items = [
        #         ("Panadol tab 250mg", 2, 10.00, "2%", 9.80, 18.16), 
        #         ("Amoxil Cap 500mg", 1, 20.00, "0%", 20.00, 20.00), 
        #         ("Floxacin Drops 10ml", 5, 5.00, "5%", 4.75, 23.75),
        #         ("Clementrin Syrup 160ml", 3, 15.00, "10%", 13.50, 40.50),
        #         ("Tibe Cream 75gm", 4, 12.00, "5%", 11.40, 45.60)
        #     ]
        
        print("Drawing Items into Table")
        
        for item, qty, rate, discount, net_price, item_total in items:

            painter.drawText(x + 20, y, item)
            painter.drawText(x + 900, y, str(qty))
            painter.drawText(x + 1100, y, f"{rate:.2f}")
            painter.drawText(x + 1400, y, f"{discount:.1f} %")
            painter.drawText(x + 1650, y, f"{net_price:.2f}")
            painter.drawText(x + 1900, y, f"{item_total:.2f}")
            
            y += 80

        y += 40
        
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x, y, pdf.width() - 200, y)
        
        y += 60
        
        rect = QRectF(1500, y, 400, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, "Sub Total", option)
        
        total_font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(total_font)
        rect = QRectF(1950, y, 200, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, f"{subtotal}", option)
        
        
        y += 100
        painter.drawText(x + 1600, y, f"Discount: ")
        painter.drawText(x + 1900, y, f"{salesdiscount}")
        
        y += 80
        painter.drawText(x + 1600, y, f"Sales Tax: ")
        painter.drawText(x + 1900, y, f"{salestax:.2f}")
        
        y += 80
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x + 1500, y, pdf.width() - 200, y) 
        
        y += 80
        total_font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(total_font)
        painter.drawText(x + 1500, y, f"Total Amount: ")
        painter.drawText(x + 1950, y, f"{finaltotal:.2f}")

        painter.end()
        
        self.print_pdf(filename)
        
        
    

    def print_pdf(self, filename):
        
        system = platform.system()
        if system in ("Linux", "Darwin"):
            os.system(f"lp '{filename}'")
        elif system == "Windows":
            os.startfile(filename, "print")

                
            



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


            
        









