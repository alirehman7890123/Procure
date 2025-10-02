from PySide6.QtWidgets import QWidget, QSizePolicy, QPushButton, QLabel, QHBoxLayout, QFrame, QHeaderView, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, QDate, QDateTime
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from utilities.stylus import load_stylesheets





class PurchaseDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Invoice Detail", objectName="SectionTitle")
        self.invoicelist = QPushButton("Invoice List", objectName="TopRightButton")
        self.invoicelist.setCursor(Qt.PointingHandCursor)
        self.invoicelist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.invoicelist)

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
        
        
        labels = ["Invoice Id", "Supplier", "Seller Invoice",  "Order Date"]

        
        
        self.invoice_data = QLabel()
        self.supplier_data = QLabel()
        self.sellerinvoice_data = QLabel()
        self.orderdate_data = QLabel()
        
        
        fields = [
            self.invoice_data,
            self.supplier_data,
            self.sellerinvoice_data,
            self.orderdate_data,
        ]
        
        
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

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10, 0.10, 0.10])
        headers = ["Product", "Company", "Qty", "Rate", "Disc (%)", "Disc", "Tax (%)",  "Tax", "Total"]
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
        

        
        
        labels = ["Sub Total", "Discount", "Tax", "Round off", "Grand Total"]

        
        self.subtotal = QLabel()
        self.discount = QLabel()
        self.tax = QLabel()
        self.roundoff = QLabel()
        self.finalamount = QLabel()
        
        fields = [
            self.subtotal,
            self.discount,
            self.tax,
            self.roundoff,
            self.finalamount
        ]        

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
            
            
            
            

    def load_purchase_data(self, id):
        
        print("Loading purchase ID:", id)
        query = QSqlQuery()
        query.prepare("SELECT id, supplier, sellerinvoice, creation_date, subtotal, discamount, taxamount, roundoff, total, paid, remaining  FROM purchase WHERE id = ?")
        query.addBindValue(id)
        
        if query.exec() and query.next():
            
            orderid = query.value(0)
            supplierid = query.value(1)
            sellerinvoice = query.value(2)
            print("Seller invoice is: ", sellerinvoice)
            invoicedate = query.value(3)
            
            subtotal = query.value(4)
            discount = query.value(5)
            tax = query.value(6)
            roundoff = query.value(7)
            total = query.value(8)
            
            joining_date = invoicedate
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)
            
            invoicedate = joining_date
            self.invoice_data.setText(str(orderid))
            self.sellerinvoice_data.setText(str(sellerinvoice))
            self.orderdate_data.setText(str(invoicedate))
            
            self.subtotal.setText(str(subtotal))
            self.discount.setText(str(discount))
            self.tax.setText(str(tax))
            self.roundoff.setText(str(roundoff))
            self.finalamount.setText(str(total))
        
            
            query2 = QSqlQuery()
            query2.prepare("SELECT name FROM supplier WHERE id = ?")
            query2.addBindValue(supplierid)
            
            if query2.exec() and query2.next():
                
                supplier = query2.value(0)
                self.supplier_data.setText(supplier)
                
            
            self.load_items_into_table(orderid)
            
            
        else:
            self.supplier_data.setText("Purchase not found.")


        




    def load_items_into_table(self, id):
        
        print("Loading items into table")
        
        query = QSqlQuery()
        query.prepare("SELECT * FROM purchaseitem where purchase = ?")
        query.addBindValue(id)

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
       
        
        if query.exec():
            
            print("Loading items into table")
            
            while query.next():
                
                self.table.insertRow(row)
                
                med = int(query.value(2))
                quantity = str(query.value(3))
                rate = str(query.value(5))
                
                print("Product is: ", med)
                
                discount = str(query.value(6))
                discountamount = str(query.value(7))
                
                tax = str(query.value(8))
                taxamount = str(query.value(9))
                
                total = str(query.value(10))
                
                query2 = QSqlQuery()
                query2.prepare("SELECT name, brand FROM product WHERE id = ?")
                query2.addBindValue(med)
                
                if query2.exec() and query2.next():
                    
                    name = query2.value(0)
                    maker = query2.value(1)
                    

                
                            
                name = QTableWidgetItem(name)
                maker = QTableWidgetItem(maker)
                quantity = QTableWidgetItem(quantity)
                rate = QTableWidgetItem(rate)
                discount = QTableWidgetItem(discount)
                discountamount = QTableWidgetItem(discountamount)
                tax = QTableWidgetItem(tax)
                taxamount = QTableWidgetItem(taxamount)
                total = QTableWidgetItem(total)
                
                self.table.setItem(row, 0, name)
                self.table.setItem(row, 1, maker)
                self.table.setItem(row, 2, quantity)
                self.table.setItem(row, 3, rate)
                self.table.setItem(row, 4, discount)
                self.table.setItem(row, 5, discountamount)
                self.table.setItem(row, 6, tax)
                self.table.setItem(row, 7, taxamount)
                self.table.setItem(row, 8, total)
                

                row += 1
        

        else:
            print("Insert failed:", query.lastError().text())
            
            





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


            
        









