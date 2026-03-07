from PySide6.QtWidgets import QWidget, QSizePolicy, QPushButton, QLabel,QMessageBox, QComboBox, QLineEdit, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, QDate
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from utilities.stylus import load_stylesheets




class SalesReturnDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        layout = QVBoxLayout(self)
        
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)

        
        heading = QLabel("Sales Return Detail", objectName='SectionTitle')
        self.SalesReturnlist = QPushButton('Sales Return List', objectName='TopRightButton')
        
        grid_layout.addWidget(heading, 0,0,1,7)
        grid_layout.addWidget(self.SalesReturnlist, 0,7,1,1)
        
        orderlabel = QLabel("Sales Return Id")
        sellerorderlabel = QLabel("Sales Order Id")
        customerlabel = QLabel("Customer")
        datelabel = QLabel("Return Date")

        grid_layout.addWidget(orderlabel, 1, 0)
        grid_layout.addWidget(sellerorderlabel, 2, 0)
        grid_layout.addWidget(customerlabel, 3, 0)
        grid_layout.addWidget(datelabel, 4, 0)
        
        self.orderid = QLabel()
        self.salesorder = QLabel()
        self.customer = QLabel()
        self.dateandtime = QLabel()

        grid_layout.addWidget(self.orderid, 1, 1)
        grid_layout.addWidget(self.salesorder, 2, 1)
        grid_layout.addWidget(self.customer, 3, 1)
        grid_layout.addWidget(self.dateandtime, 4, 1)
        
        
        layout.addWidget(grid_widget)
        
        
        
        self.supplier_table = MyTable()
        
        self.supplier_table.setColumnCount(7)
        self.supplier_table.setHorizontalHeaderLabels([
            "#", "Product", "Brand", "Sold", "Returned", "Rate", "Total"
        ])
        self.supplier_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.supplier_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)#
        self.supplier_table.setFixedHeight(300)
        

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
        roundofflabel = QLabel("Roundoff")
        finalamountlabel = QLabel("Grand Total")
        paidlabel = QLabel("Paid")
        remanininglabel = QLabel("Remaining")
        writeofflabel = QLabel("Write-Off")

        grid_layout.addWidget(subtotallabel, 8, 0)
        grid_layout.addWidget(roundofflabel, 9, 0)
        grid_layout.addWidget(finalamountlabel, 10, 0)
        grid_layout.addWidget(paidlabel, 11, 0)
        grid_layout.addWidget(remanininglabel, 12, 0)
        grid_layout.addWidget(writeofflabel, 13, 0)
        
        self.subtotal = QLabel()
        self.roundoff = QLabel()
        self.finalamount = QLabel()
        self.paid = QLabel()
        self.remaining = QLabel()
        self.writeoff = QLabel()

        grid_layout.addWidget(self.subtotal, 8, 1)
        grid_layout.addWidget(self.roundoff, 9, 1)
        grid_layout.addWidget(self.finalamount, 10, 1)
        grid_layout.addWidget(self.paid, 11, 1)
        grid_layout.addWidget(self.remaining, 12, 1)
        grid_layout.addWidget(self.writeoff, 13, 1)
        
        
        self.setLayout(layout)
        
        layout.addStretch()
        
        self.setStyleSheet(load_stylesheets())




    # def load_sales_data(self, id):
        
    #     print("Loading Sales ID:", id)
    #     query = QSqlQuery()
    #     query.prepare("SELECT salesorder, customer, creation_date, subtotal, roundoff, total, paid, remaining, writeoff  FROM salesreturn WHERE id = ?")
    #     query.addBindValue(id)
        
    #     if query.exec() and query.next():
            
    #         orderid = query.value(0)
    #         customer_id = query.value(1)
            
    #         if customer_id == '':
    #             customer_id = None
            
    #         invoicedate = query.value(2)
            
    #         subtotal = query.value(3)
    #         roundoff = query.value(4)
    #         total = query.value(5)
    #         paid = query.value(6)
    #         remaining = query.value(7)
    #         writeoff = query.value(8)
            

            
    #         if isinstance(invoicedate, QDate):  # or QDateTime
    #             invoicedate = invoicedate.toString("dd-MM-yyyy")  # or "yyyy-MM-dd"
    #         else:
    #             invoicedate = str(invoicedate)
            
    #         self.orderid.setText(str(id))
    #         self.salesorder.setText(str(orderid))
    #         self.dateandtime.setText(str(invoicedate))
            
    #         self.subtotal.setText(str(subtotal))
    #         self.roundoff.setText(str(roundoff))
    #         self.finalamount.setText(str(total))
    #         self.paid.setText(str(paid))
    #         self.remaining.setText(str(remaining))
    #         self.writeoff.setText(str(writeoff))
        
        
    #         if customer_id is not None:
            
    #             query2 = QSqlQuery()
    #             query2.prepare("SELECT name FROM customer WHERE id = ?")
    #             query2.addBindValue(int(customer_id))
                
    #             if query2.exec() and query2.next():
                    
    #                 customer = query2.value(0)
    #                 self.customer.setText(customer)
                    
    #         else: 
    #             customer = 'Walk-In Customer'
    #             self.customer.setText(customer)

                
            
    #         self.load_items_into_table(orderid)
            
            
    #     else:
    #         QMessageBox.information(self, "Error", query.lastError().text() )


    def load_sales_data(self, salesreturn_id: int) -> None:
        
        print(f"Loading Sales Return ID: {salesreturn_id}")

        query = QSqlQuery()
        query.prepare("""
            SELECT salesorder, customer, creation_date,
                subtotal, roundoff, total,
                paid, remaining, writeoff
            FROM salesreturn
            WHERE id = ?
        """)
        query.addBindValue(salesreturn_id)

        if not query.exec() or not query.next():
            QMessageBox.information(self, "Error", query.lastError().text())
            return

        salesorder_id = query.value(0)
        customer_id   = query.value(1)
        invoice_date  = query.value(2)

        subtotal  = query.value(3)
        roundoff  = query.value(4)
        total     = query.value(5)
        paid      = query.value(6)
        remaining = query.value(7)
        writeoff  = query.value(8)

        # Date formatting
        if isinstance(invoice_date, QDate):
            invoice_date = invoice_date.toString("dd-MM-yyyy")
        else:
            invoice_date = str(invoice_date)

        # Set UI fields
        self.orderid.setText(str(salesreturn_id))
        self.salesorder.setText(str(salesorder_id))
        self.dateandtime.setText(invoice_date)

        self.subtotal.setText(str(subtotal))
        self.roundoff.setText(str(roundoff))
        self.finalamount.setText(str(total))
        self.paid.setText(str(paid))
        self.remaining.setText(str(remaining))
        self.writeoff.setText(str(writeoff))

        # Customer handling
        if customer_id:
            customer_query = QSqlQuery()
            customer_query.prepare("SELECT name FROM customer WHERE id = ?")
            customer_query.addBindValue(customer_id)

            if customer_query.exec() and customer_query.next():
                self.customer.setText(customer_query.value(0))
            else:
                self.customer.setText("Unknown Customer")
        else:
            self.customer.setText("Walk-In Customer")

        # 🔥 Correct call
        self.load_items_into_table(salesreturn_id)
        




    def load_items_into_table(self, salesreturn_id: int) -> None:

        print(f"Loading Sales Return Items for ID: {salesreturn_id}")

        query = QSqlQuery()
        query.prepare("""
            SELECT 
                s.product,
                p.display_name,
                p.brand,
                s.sold,
                s.returned,
                s.rate,
                s.total
            FROM salesreturn_item s
            LEFT JOIN product p ON s.product = p.id
            WHERE s.salesreturn = ?
        """)
        query.addBindValue(salesreturn_id)

        if not query.exec():
            print("Query failed:", query.lastError().text())
            return

        # Collect rows first
        rows = []
        while query.next():
            rows.append({
                "product_id": query.value(0),
                "name": query.value(1) or "Unknown",
                "brand": query.value(2) or "",
                "sold": query.value(3),
                "returned": query.value(4),
                "rate": query.value(5),
                "total": query.value(6),
            })
            
            print(f"Fetched item: {rows[-1]}")
            print("Data is ", query.value(0), query.value(1), query.value(2), query.value(3), query.value(4), query.value(5), query.value(6))

        # Clear table once
        self.supplier_table.setRowCount(len(rows))

        for row_index, data in enumerate(rows):
            self.supplier_table.setItem(row_index, 0, QTableWidgetItem(str(row_index + 1)))
            self.supplier_table.setItem(row_index, 1, QTableWidgetItem(str(data["name"])))
            self.supplier_table.setItem(row_index, 2, QTableWidgetItem(str(data["brand"])))
            self.supplier_table.setItem(row_index, 3, QTableWidgetItem(str(data["sold"])))
            self.supplier_table.setItem(row_index, 4, QTableWidgetItem(str(data["returned"])))
            self.supplier_table.setItem(row_index, 5, QTableWidgetItem(str(data["rate"])))
            self.supplier_table.setItem(row_index, 6, QTableWidgetItem(str(data["total"])))

        print(f"Loaded {len(rows)} items successfully.")
    
            


class MyTable(QTableWidget):
    
    def resizeEvent(self, event):
        
        total_width = self.viewport().width()
        
        self.setColumnWidth(0, int(total_width * 0.05))  
        self.setColumnWidth(1, int(total_width * 0.30))  
        self.setColumnWidth(2, int(total_width * 0.20))  
        self.setColumnWidth(3, int(total_width * 0.10))  
        self.setColumnWidth(4, int(total_width * 0.10))  
        self.setColumnWidth(5, int(total_width * 0.15)) 
        self.setColumnWidth(6, int(total_width * 0.15)) 
        
        super().resizeEvent(event)
        
        
        
        
        
        











