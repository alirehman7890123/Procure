from PySide6.QtWidgets import QWidget, QSizePolicy, QPushButton, QLabel, QSpacerItem, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtSql import QSqlQuery

from utilities.stylus import load_stylesheets
from utilities.app_messagebox import AppMessageBox





class HoldSalesDetailWidget(QWidget):
    
    
    reload_order_signal = Signal(int)

    def __init__(self, parent=None):

        super().__init__(parent)

        layout = QVBoxLayout(self)
        
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)

        
        heading = QLabel("Sales Orders - On Hold", objectName='SectionTitle')
        self.holdinglist = QPushButton('Hold Sales', objectName='TopRightButton')
        self.holdinglist.setCursor(Qt.PointingHandCursor)
        
        grid_layout.addWidget(heading, 0,0,1,7)
        grid_layout.addWidget(self.holdinglist, 0,7,1,1)
        
        orderlabel = QLabel("Hold Sale Id")
        statuslabel = QLabel("Order Status")
        customerlabel = QLabel("Customer")
        salesman = QLabel("User")
        datelabel = QLabel("Date")

        grid_layout.addWidget(orderlabel, 1, 0)
        grid_layout.addWidget(statuslabel, 2, 0)
        grid_layout.addWidget(customerlabel, 3, 0)
        grid_layout.addWidget(salesman, 4, 0)
        grid_layout.addWidget(datelabel, 5, 0)
        
        self.orderid = QLabel()
        self.status = QLabel()
        self.customer = QLabel()
        self.salesman = QLabel()
        self.orderdate = QLabel()

        grid_layout.addWidget(self.orderid, 1, 1)
        grid_layout.addWidget(self.status, 2, 1)
        grid_layout.addWidget(self.customer, 3, 1)
        grid_layout.addWidget(self.salesman, 4, 1)
        grid_layout.addWidget(self.orderdate, 5, 1)
        
        
        layout.addWidget(grid_widget)
        
        
        
        self.supplier_table = MyTable()
        
        self.supplier_table.setColumnCount(8)
        self.supplier_table.setHorizontalHeaderLabels([
            "##", "Product", "Qty", "Rate", "Disc (%)", "Disc", "Tax %", "Total"
        ])
        self.supplier_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.supplier_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        

        header = self.supplier_table.horizontalHeader()
        header.setStretchLastSection(False)

        self.supplier_table.setStyleSheet("QTableWidget::item { color: #333; }")

        

        self.supplier_table.verticalHeader().setFixedWidth(0)
        header = self.supplier_table.horizontalHeader()
        header.setFixedHeight(30)

        header.setStyleSheet("""
                             
                background-color: #333;
                color: white;              
                font-weight: 600;
            
        """)
        
        
        grid_layout.addWidget(self.supplier_table, 6, 0, 1, 8)
        
        
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer, 10, 0)
        
        self.reload_data_btn = QPushButton("Reload Sale Order")
        self.reload_data_btn.setObjectName("TopRightButton")
        self.reload_data_btn.setCursor(Qt.PointingHandCursor)
        
        
        grid_layout.addWidget(self.reload_data_btn, 8, 2, 1, 1)
        
        self.setLayout(layout)

        
        self.setStyleSheet(load_stylesheets())




    def load_holdsales_data(self, id):
        
        
        try:
            
            print("Loading Sales ID:", id)
            self.hold_id = int(id)
            query = QSqlQuery()
            query.prepare("SELECT customer, salesman, status, creation_date FROM holdsale WHERE id = ?")
            query.addBindValue(id)
            
            if query.exec() and query.next():
                
                customerid = int(query.value(0))
                salesmanid = int(query.value(1))
                status = query.value(2)
                invoicedate = query.value(3) 
                
                if isinstance(invoicedate, QDate):  # or QDateTime
                    invoicedate = invoicedate.toString("dd-MM-yyyy")  # or "yyyy-MM-dd"
                else:
                    invoicedate = str(invoicedate)
                    
                
                print("Customer is ...... ", customerid)
                
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
                    
                
                print("salesman Id isl ", salesmanid)
                salesman = "-"
                if salesmanid:
                    salesmanquery = QSqlQuery()
                    salesmanquery.prepare("SELECT username FROM auth WHERE id = ?")
                    salesmanquery.addBindValue(salesmanid)

                    if salesmanquery.exec() and salesmanquery.next():
                        salesman = str(salesmanquery.value(0) or "-")
                    else:
                        salesmanquery = QSqlQuery()
                        salesmanquery.prepare("SELECT name FROM employee WHERE id = ?")
                        salesmanquery.addBindValue(salesmanid)

                        if salesmanquery.exec() and salesmanquery.next():
                            salesman = str(salesmanquery.value(0) or "-")
        
                self.orderid.setText(str(id))
                self.status.setText(status)
                self.customer.setText(str(customer))
                self.salesman.setText(salesman)
                self.orderdate.setText(str(invoicedate))
            
                print("Sales data loaded successfully for ID:", id)
                
                self.load_items_into_table(id)
                
            
        except Exception as e:
            
            e = str(e)
            print("Error loading sales data:", e)
            AppMessageBox.critical(self, "Error", f"Error loading sales data: {e}")
            
            
            


    def load_items_into_table(self, id):
        
        print("Loading items into table")
        
        query = QSqlQuery()
        query.prepare("""
            SELECT product, qty, unitrate, discount, discountamount, COALESCE(tax, 0), total
            FROM holditems
            WHERE holdsale = ?
        """)
        query.addBindValue(id)

        self.supplier_table.setRowCount(0)  # Clear existing rows

        row = 0
        
       
        
        if query.exec():
            
            print("Loading items into table")
            
            while query.next():
                
                self.supplier_table.insertRow(row)
                
                product = int(query.value(0))
                quantity = str(query.value(1))
                rate = str(query.value(2))
                discount = str(query.value(3))
                discountamount = str(query.value(4))
                tax = str(query.value(5))
                total = str(query.value(6))

                query2 = QSqlQuery()
                query2.prepare("SELECT display_name FROM product WHERE id = ?")
                query2.addBindValue(product)
                
                if query2.exec() and query2.next():
                    
                    name = query2.value(0)
                    
                counter = QTableWidgetItem(str(row + 1))  # Row number starts from 1
                name = QTableWidgetItem(name)
                quantity = QTableWidgetItem(quantity)
                rate = QTableWidgetItem(rate)
                discount = QTableWidgetItem(discount)
                discountamount = QTableWidgetItem(discountamount)
                tax = QTableWidgetItem(tax)
                total = QTableWidgetItem(total)
                
                self.supplier_table.setItem(row, 0, counter)
                self.supplier_table.setItem(row, 1, name)
                self.supplier_table.setItem(row, 2, quantity)
                self.supplier_table.setItem(row, 3, rate)
                self.supplier_table.setItem(row, 4, discount)
                self.supplier_table.setItem(row, 5, discountamount)
                self.supplier_table.setItem(row, 6, tax)
                self.supplier_table.setItem(row, 7, total)
                

                row += 1
                print("row is increased...")

            
            # self.reload_data_btn.clicked.connect(partial(self.reload_btn_clicked))

            try:
                self.reload_data_btn.clicked.disconnect()
            except Exception:
                pass
            self.reload_data_btn.clicked.connect(lambda: self.reload_order_signal.emit(id))
            print("Signal connected!")

        

        else:
            print("Insert failed:", query.lastError().text())
            
            
        
            


class MyTable(QTableWidget):
    
    def resizeEvent(self, event):
        
        total_width = self.viewport().width()
        
        self.setColumnWidth(0, int(total_width * 0.05))  # #
        self.setColumnWidth(1, int(total_width * 0.35))  # Product
        self.setColumnWidth(2, int(total_width * 0.10))  # Qty
        self.setColumnWidth(3, int(total_width * 0.12))  # Rate
        self.setColumnWidth(4, int(total_width * 0.12))  # Disc (%)
        self.setColumnWidth(5, int(total_width * 0.12))  # Disc (Amt)
        self.setColumnWidth(6, int(total_width * 0.12))  # Total
        
        
        super().resizeEvent(event)
        
        
        
        
        
        








