from PySide6.QtWidgets import QWidget, QSizePolicy, QPushButton, QLabel, QComboBox, QLineEdit, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, QDate
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from utilities.stylus import load_stylesheets





class PurchaseReturnDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        layout = QVBoxLayout(self)
        
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)

        
        heading = QLabel("Purchase Return Detail", objectName='myheading')
        self.purchasereturnlist = QPushButton('Purchse Return List', objectName='supplierlist')
        
        grid_layout.addWidget(heading, 0,0,1,7)
        grid_layout.addWidget(self.purchasereturnlist, 0,7,1,1)
        
        orderlabel = QLabel("Purchase Invoice Id")
        sellerorderlabel = QLabel("Seller Invoice Id")
        supplierlabel = QLabel("Supplier")
        datelabel = QLabel("Return Date")

        grid_layout.addWidget(orderlabel, 1, 0)
        grid_layout.addWidget(sellerorderlabel, 2, 0)
        grid_layout.addWidget(supplierlabel, 3, 0)
        grid_layout.addWidget(datelabel, 4, 0)
        
        self.orderid = QLabel()
        self.sellerorder = QLabel()
        self.supplier = QLabel()
        self.dateandtime = QLabel()

        grid_layout.addWidget(self.orderid, 1, 1)
        grid_layout.addWidget(self.sellerorder, 2, 1)
        grid_layout.addWidget(self.supplier, 3, 1)
        grid_layout.addWidget(self.dateandtime, 4, 1)
        
        
        layout.addWidget(grid_widget)
        
        
        
        self.supplier_table = MyTable()
        
        self.supplier_table.setColumnCount(9)
        self.supplier_table.setHorizontalHeaderLabels([
            "#", "Product", "Batch", "Purchased", "Return", "Rate", "Disc (%)", "Tax (%)", "Total"
        ])
        self.supplier_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.supplier_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        

        header = self.supplier_table.horizontalHeader()
        header.setStretchLastSection(False)

        self.supplier_table.setStyleSheet("""
                                QTableWidget { margin: 30px; color: #333; }
                                QHeaderView::section { background-color: #333; } 
                                
                                
                QTableWidget::item {
                    padding: 0px;
                }

                QLineEdit {
                    margin: 4px;
                    border: 1px solid #ccc;
                    border-radius: 2px;
                    padding: 4px;
                    background-color: #fdfdfd;
                    font-size: 14px;
                }
                
                QLineEdit::placeholder {
                    color: green;
                }

                QComboBox {
                    border: 1px solid #ccc;
                    border-radius: 2px;
                    padding: 2px 4px;
                    background-color: #fdfdfd;
                    font-size: 14px;
                }

                QPushButton {
                    border: 1px solid #888;
                    border-radius: 3px;
                    background-color: #333;
                    padding: 2px 8px;
                    color: #ccc;
                    width: 100px;
                    
                }

                QPushButton:hover {
                    background-color: #555;
                }

                QPushButton:pressed {
                    background-color: #ccc;
                }
            """)

        

        self.supplier_table.verticalHeader().setFixedWidth(0)
        header = self.supplier_table.horizontalHeader()
        header.setFixedHeight(30)

        header.setStyleSheet("""
                             
                background-color: #333;
                color: white;              
                font-weight: 600;
            
        """)
        
        
        grid_layout.addWidget(self.supplier_table, 6, 0, 1, 8)
        
        
        subtotallabel = QLabel("Sub Total")
        discountlabel = QLabel("Total Discount")
        taxlabel = QLabel("Total Tax")
        roundofflabel = QLabel("Roundoff")
        finalamountlabel = QLabel("Grand Total")

        grid_layout.addWidget(subtotallabel, 8, 0)
        grid_layout.addWidget(discountlabel, 9, 0)
        grid_layout.addWidget(taxlabel, 10, 0)
        grid_layout.addWidget(roundofflabel, 11, 0)
        grid_layout.addWidget(finalamountlabel, 12, 0)
        
        self.subtotal = QLabel()
        self.discount = QLabel()
        self.tax = QLabel()
        self.roundoff = QLabel()
        self.finalamount = QLabel()

        grid_layout.addWidget(self.subtotal, 8, 1)
        grid_layout.addWidget(self.discount, 9, 1)
        grid_layout.addWidget(self.tax, 10, 1)
        grid_layout.addWidget(self.roundoff, 11, 1)
        grid_layout.addWidget(self.finalamount, 12, 1)
        
        
        
        self.setLayout(layout)

        self.setStyleSheet(load_stylesheets())




    def load_purchase_data(self, id):
        
        print("Loading purchase ID:", id)
        query = QSqlQuery()
        query.prepare("SELECT * FROM purchase_return WHERE id = ?")
        query.addBindValue(id)
        
        if query.exec() and query.next():
            
            orderid = query.value(0)
            supplierid = query.value(1)
            invoicedate = query.value(3)
            
            subtotal = query.value(4)
            roundoff = query.value(7)
            total = query.value(8)
            
            

            
            if isinstance(invoicedate, QDate):  # or QDateTime
                invoicedate = invoicedate.toString("dd-MM-yyyy")  # or "yyyy-MM-dd"
            else:
                invoicedate = str(invoicedate)
            
            self.orderid.setText(str(orderid))
            self.dateandtime.setText(str(invoicedate))
            
            self.subtotal.setText(str(subtotal))
            self.roundoff.setText(str(roundoff))
            self.finalamount.setText(str(total))
        
            
            query2 = QSqlQuery()
            query2.prepare("SELECT name FROM supplier WHERE id = ?")
            query2.addBindValue(supplierid)
            
            if query2.exec() and query2.next():
                
                supplier = query2.value(0)
                self.supplier.setText(supplier)
                
            
            self.load_items_into_table(orderid)
            
            
        else:
            self.supplier.setText("Purchase not found.")



    def load_items_into_table(self, id):
        
        print("Loading items into table")
        
        query = QSqlQuery()
        query.prepare("SELECT * FROM purchase_return_item where purchase_return = ?")
        query.addBindValue(id)

        self.supplier_table.setRowCount(0)  # Clear existing rows

        row = 0
        
       
        
        if query.exec():
            
            print("Loading items into table")
            
            while query.next():
                
                self.supplier_table.insertRow(row)
                
                med = int(query.value(2))
                quantity = str(query.value(3))
                rate = str(query.value(4))
                
                print("med is: ", med)
                
                discount = str(query.value(5))
                discountamount = str(query.value(6))
                
                tax = str(query.value(7))
                taxamount = str(query.value(8))
                
                total = str(query.value(9))
                
                query2 = QSqlQuery()
                query2.prepare("SELECT name, maker FROM med WHERE id = ?")
                query2.addBindValue(med)
                
                if query2.exec() and query2.next():
                    
                    name = query2.value(0)
                    maker = query2.value(1)
                    
                
                quantity = QTableWidgetItem(quantity)
                rate = QTableWidgetItem(rate)
                discount = QTableWidgetItem(discount)
                discountamount = QTableWidgetItem(discountamount)
                tax = QTableWidgetItem(tax)
                taxamount = QTableWidgetItem(taxamount)
                total = QTableWidgetItem(total)
                
                self.supplier_table.setItem(row, 0, name)
                self.supplier_table.setItem(row, 1, maker)
                self.supplier_table.setItem(row, 2, quantity)
                self.supplier_table.setItem(row, 3, rate)
                self.supplier_table.setItem(row, 4, discount)
                self.supplier_table.setItem(row, 5, discountamount)
                self.supplier_table.setItem(row, 6, tax)
                self.supplier_table.setItem(row, 7, taxamount)
                self.supplier_table.setItem(row, 8, total)
                

                row += 1
        

        else:
            print("Insert failed:", query.lastError().text())
            
            


class MyTable(QTableWidget):
    
    def resizeEvent(self, event):
        
        total_width = self.viewport().width()
        
        self.setColumnWidth(0, int(total_width * 0.30))  
        self.setColumnWidth(1, int(total_width * 0.15))  
        self.setColumnWidth(2, int(total_width * 0.10))  
        self.setColumnWidth(3, int(total_width * 0.10))  
        self.setColumnWidth(4, int(total_width * 0.10))  
        self.setColumnWidth(5, int(total_width * 0.05)) 
        self.setColumnWidth(6, int(total_width * 0.05))
        self.setColumnWidth(7, int(total_width * 0.05)) 
        self.setColumnWidth(8, int(total_width * 0.05)) 
        self.setColumnWidth(9, int(total_width * 0.05)) 
        
        super().resizeEvent(event)
        
        
        
        
        
        











