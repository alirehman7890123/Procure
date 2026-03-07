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
        
        self.supplier_table.setColumnCount(7)
        self.supplier_table.setHorizontalHeaderLabels([
            "Product", "Brand", "Batch", "Purchased", "Return", "Rate", "Total"
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




    # def load_purchase_data(self, id):
        
    #     print("Loading purchase ID:", id)
    #     query = QSqlQuery()
    #     query.prepare("SELECT * FROM purchase_return WHERE id = ?")
    #     query.addBindValue(id)
        
    #     if query.exec() and query.next():
            
    #         orderid = query.value(0)
    #         supplierid = query.value(1)
    #         invoicedate = query.value(3)
            
    #         subtotal = query.value(4)
    #         roundoff = query.value(7)
    #         total = query.value(8)
            
            
    #         # get supplier name
    #         supplier_query = QSqlQuery()
    #         supplier_query.prepare("SELECT name FROM supplier WHERE id = ?")
    #         supplier_query.addBindValue(supplierid)
            
    #         if query.exec() and supplier_query.next():
    #             supplier_name = supplier_query.value(0)
    #             self.supplier.setText(supplier_name)
                
                
    #         if isinstance(invoicedate, QDate):  # or QDateTime
    #             invoicedate = invoicedate.toString("dd-MM-yyyy")  # or "yyyy-MM-dd"
    #         else:
    #             invoicedate = str(invoicedate)
            
    #         self.orderid.setText(str(orderid))
    #         self.dateandtime.setText(str(invoicedate))
            
    #         self.subtotal.setText(str(subtotal))
    #         self.roundoff.setText(str(roundoff))
    #         self.finalamount.setText(str(total))
        
            
    #         query2 = QSqlQuery()
    #         query2.prepare("SELECT name FROM supplier WHERE id = ?")
    #         query2.addBindValue(supplierid)
            
    #         if query2.exec() and query2.next():
                
    #             supplier = query2.value(0)
    #             self.supplier.setText(supplier)
                
            
    #         self.load_items_into_table(orderid)
            
            
    #     else:
    #         self.supplier.setText("Purchase not found.")


    def load_purchase_data(self, purchase_return_id: int) -> None:
        """
        Load purchase return header data and populate UI fields.
        """

        print(f"Loading Purchase Return ID: {purchase_return_id}")

        query = QSqlQuery()
        query.prepare("""
            SELECT 
                id,
                supplier,
                creation_date,
                subtotal,
                roundoff,
                total
            FROM purchase_return
            WHERE id = ?
        """)
        query.addBindValue(purchase_return_id)

        if not query.exec() or not query.next():
            self.supplier.setText("Purchase not found.")
            return

        order_id     = query.value(0)
        supplier_id  = query.value(1)
        invoice_date = query.value(2)
        subtotal     = query.value(3)
        roundoff     = query.value(4)
        total        = query.value(5)

        # Format date safely
        if isinstance(invoice_date, QDate):
            invoice_date = invoice_date.toString("dd-MM-yyyy")
        else:
            invoice_date = str(invoice_date)

        # Set header fields
        self.orderid.setText(str(order_id))
        self.dateandtime.setText(invoice_date)
        self.subtotal.setText(str(subtotal))
        self.roundoff.setText(str(roundoff))
        self.finalamount.setText(str(total))

        # Load supplier name (single query, properly executed)
        supplier_name = "Unknown Supplier"

        if supplier_id:
            supplier_query = QSqlQuery()
            supplier_query.prepare("SELECT name FROM supplier WHERE id = ?")
            supplier_query.addBindValue(supplier_id)

            if supplier_query.exec() and supplier_query.next():
                supplier_name = supplier_query.value(0)

        self.supplier.setText(supplier_name)

        # Load associated items
        self.load_items_into_table(purchase_return_id)


         
    
    def load_items_into_table(self, purchase_return_id: int) -> None:
        

        print(f"Loading Purchase Return Items for ID: {purchase_return_id}")

        query = QSqlQuery()
        query.prepare("""
            SELECT
                pri.product,
                p.display_name,
                p.brand,
                pri.batch,
                pri.purchased,
                pri.returned,
                pri.rate,
                pri.total
            FROM purchase_return_item pri
            LEFT JOIN product p ON pri.product = p.id
            WHERE pri.purchase_return = ?
        """)
        query.addBindValue(purchase_return_id)

        if not query.exec():
            print("Query failed:", query.lastError().text())
            return

        rows = []

        while query.next():
            rows.append({
                "name": query.value(1) or "Unknown",
                "brand": query.value(2) or "",
                "batch": query.value(3),
                "purchased": query.value(4),
                "returned": query.value(5),
                "rate": query.value(6),
                "total": query.value(7),
            })

        # Disable UI updates for performance
        self.supplier_table.setUpdatesEnabled(False)
        self.supplier_table.setRowCount(len(rows))

        for row_index, data in enumerate(rows):

            self.supplier_table.setItem(row_index, 0, QTableWidgetItem(str(data["name"])))
            self.supplier_table.setItem(row_index, 1, QTableWidgetItem(str(data["brand"])))
            self.supplier_table.setItem(row_index, 2, QTableWidgetItem(str(data["batch"])))
            self.supplier_table.setItem(row_index, 3, QTableWidgetItem(str(data["purchased"])))
            self.supplier_table.setItem(row_index, 4, QTableWidgetItem(str(data["returned"])))
            self.supplier_table.setItem(row_index, 5, QTableWidgetItem(str(data["rate"])))
            self.supplier_table.setItem(row_index, 6, QTableWidgetItem(str(data["total"])))

        self.supplier_table.setUpdatesEnabled(True)

        print(f"Loaded {len(rows)} items successfully.")

     
     
            

class MyTable(QTableWidget):
    
    def resizeEvent(self, event):
        
        total_width = self.viewport().width()
        
        self.setColumnWidth(0, int(total_width * 0.30))  
        self.setColumnWidth(2, int(total_width * 0.10))  
        self.setColumnWidth(3, int(total_width * 0.10))  
        self.setColumnWidth(4, int(total_width * 0.10))  
        self.setColumnWidth(5, int(total_width * 0.10)) 
        self.setColumnWidth(6, int(total_width * 0.10))
        self.setColumnWidth(7, int(total_width * 0.10))
        
        super().resizeEvent(event)
        
        
        
        
        
        











