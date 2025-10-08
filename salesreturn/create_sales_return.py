
from PySide6.QtWidgets import QWidget, QCompleter, QDateEdit, QVBoxLayout,  QHBoxLayout, QFrame, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
from PySide6.QtCore import QFile, Qt, QStringListModel, QDate, QDateTime, QTimer, Signal
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import QPalette, QColor, QKeyEvent
from functools import partial
import csv    
import os
import math

from utilities.stylus import load_stylesheets




class KeyUpLineEdit(QLineEdit):
    keyReleased = Signal(QKeyEvent)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.keyReleased.emit(event)




class AddSalesReturnWidget(QWidget):


    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Sales Return Invoice", objectName="SectionTitle")
        self.invoicelist = QPushButton("Sales Returns List", objectName="TopRightButton")
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
        
        
        # === Get Order Row ===
        
        get_record_row = QHBoxLayout()
        
        order_label = QLabel("Enter Sales Order Id")
        self.salesorder = QLineEdit()
        self.salesorder.setPlaceholderText("Enter Id")
        
        self.get_oder_btn = QPushButton("Get Order", objectName='TopRightButton')
        self.get_oder_btn.clicked.connect(self.get_sales_order)
        self.get_oder_btn.setCursor(Qt.PointingHandCursor)
        
        
        get_record_row.addWidget(order_label)
        get_record_row.addWidget(self.salesorder)
        get_record_row.addWidget(self.get_oder_btn)
        
        self.layout.addLayout(get_record_row)
        
        
        # === Customer + Salesman Row ===
        
        top_row = QHBoxLayout()
        
        customerlabel = QLabel("Customer")
        self.customer = QLabel()
        
        salesmanlabel = QLabel("Salesman")
        self.salesman = QLabel()
        
        date_label = QLabel("Date/Time")
        self.invoicedate = QLabel()
        
        top_row.addWidget(customerlabel)
        top_row.addWidget(self.customer, 2)
        
        top_row.addWidget(salesmanlabel)
        top_row.addWidget(self.salesman, 2)
        
        top_row.addWidget(date_label)
        top_row.addWidget(self.invoicedate, 2)
        
        
        top_row.addSpacing(40)
        
        self.layout.addLayout(top_row)
        
        
        self.min_visible_rows = 5
        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10, 0.10])
        headers = ["#", "Product","Manufacturer", " Sold", "Return", "Rate", "Disc %", "Total"]
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
        

        # === Sub Total Row ===
        
        subtotal_row = QHBoxLayout()
        
        subtotal_label = QLabel("Sub Total")
        self.subtotal = QLabel("0.00")
        
        subtotal_row.addWidget(subtotal_label)
        subtotal_row.addWidget(self.subtotal)
        
        self.layout.addLayout(subtotal_row)
        
        
        
        # === Sub Total Row ===
        
        roundoff_row = QHBoxLayout()
        
        roundoff_label = QLabel("Round Off")
        self.roundoff = QLabel("0.00")
        
        roundoff_row.addWidget(roundoff_label)
        roundoff_row.addWidget(self.roundoff)
        
        self.layout.addLayout(roundoff_row)
        
        
        
        # === Final Amount Row ===
        
        final_amount_row = QHBoxLayout()
        
        final_amount = QLabel("Final Amount")
        self.final_amountdata = QLabel("0.00")
        
        final_amount_row.addWidget(final_amount)
        final_amount_row.addWidget(self.final_amountdata)
        
        self.layout.addLayout(final_amount_row)
        
        
        
        
        # === Paid Amount Row ===
        
        paid_amount_row = QHBoxLayout()
        
        paid_amount = QLabel("Paid Amount")
        self.paid = QLineEdit()
        self.paid.setPlaceholderText("0.00")
        
        paid_amount_row.addWidget(paid_amount)
        paid_amount_row.addWidget(self.paid)
        
        self.layout.addLayout(paid_amount_row)
        self.paid.textChanged.connect(self.calculate_payment)
        
        
        # === Remaining Amount Row ===
        
        remaining_row = QHBoxLayout()
        
        remaining_amount = QLabel("Remaining Amount")
        self.remaining = QLabel()
        self.paid.setPlaceholderText("0.00")
        
        self.checkbox = QCheckBox("Write off")
        self.checkbox.toggled.connect(self.writeoffcheck)
        
        remaining_row.addWidget(remaining_amount)
        remaining_row.addWidget(self.remaining)
        remaining_row.addWidget(self.checkbox)
        
        self.layout.addLayout(remaining_row)
        
        
        
        # 8th Line
        self.note = QLabel("Note")
        self.layout.addWidget(self.note)
        
        
        # === Add Button ===
        savebutton = QPushButton("Save Return Information", objectName="SaveButton")
        savebutton.setCursor(Qt.PointingHandCursor)
        savebutton.clicked.connect(lambda: self.save_sales_return())

        self.layout.addWidget(savebutton)
        self.layout.addStretch()
        
        
        
        # Apply stylesheet
        
        self.setStyleSheet(load_stylesheets())

        self.layout.addStretch()






        
        
        
    def get_sales_order(self):
        
        order_id = self.salesorder.text()
        if order_id == '':
            QMessageBox.information(self, "Error", "Please enter the sales id")
            return
        else:
            order_id = int(order_id) if order_id else 0
            
            self.load_sales_data(order_id)
            
            

    
    
    def load_sales_data(self, id):
        
        self.salesorder_id = id
        print("Loading Sales ID:", id)
        query = QSqlQuery()
        query.prepare("SELECT * FROM sales WHERE id = ?")
        query.addBindValue(id)
        
        if query.exec() and query.next():
            
            customer = query.value(1)
            salesman = query.value(2)
            
            self.customer_id = customer
            self.salesman_id = salesman
            
            print("customer and salesman is: ", customer, salesman)
            
            discount = query.value(4)
            tax = query.value(7)
            
            invoicedate = query.value(17)
            
            joining_date = invoicedate
            
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)

            invoicedate = joining_date
            
            self.invoicedate.setText(str(invoicedate))
            print("Customer is : ", customer)
            print("Customer type is: ", type(customer))
            
            if customer == '':
                customer = None
                
            if customer is not None:
            
                customer_query = QSqlQuery()
                customer_query.prepare("SELECT name FROM customer WHERE id = ?")
                customer_query.addBindValue(int(customer))
                
                if customer_query.exec() and customer_query.next():
                    
                    customername = customer_query.value(0)
                    customerwithid = f"{customer} - {customername}"
                    print("Customer with id ", customerwithid)
                    self.customer.setText(customerwithid)   
                    
                else:
                    print("Error ", customer_query.lastError().text())
            
            else:
                
                print("customer is None")
                self.customer.setText('Walk-In Customer')  
            
            
            salesman_query = QSqlQuery()
            salesman_query.prepare("SELECT firstname, lastname FROM auth WHERE id = ?")
            salesman_query.addBindValue(int(salesman))
            
            if salesman_query.exec() and salesman_query.next():
                
                firstname = salesman_query.value(0)
                lastname = salesman_query.value(1)
                
                salesman_name = f"{firstname} {lastname}"
                
                salesmanwithid = f"{salesman} - {salesman_name}"
                salesmanwithid = str(salesmanwithid)
                print("Salesman with id ", salesmanwithid)
                self.salesman.setText(salesmanwithid)
                
                
            self.load_items_into_table(id)
            
        else:
            print(query.lastError().text())
            QMessageBox.critical(self, 'Error', query.lastError().text())    
        



    def load_items_into_table(self, id):
        
        print("Loading Sales items into table")
        
        query = QSqlQuery()
        query.prepare("SELECT * FROM salesitem where sales = ?")
        query.addBindValue(id)

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
       
        if query.exec():
            
            print("Loading items into table")
            
            while query.next():
                
                self.table.insertRow(row)
                
                item_id = str(query.value(0))
                product = int(query.value(2))
                
                quantity = str(query.value(3))
                rate = str(query.value(5))
                
                returned = QLineEdit()
                returned.setText("0")
                returned.textChanged.connect(lambda _: self.update_amount(returned))
                                
                discount = str(query.value(6))
                total = "0.0"
                query2 = QSqlQuery()
                query2.prepare("SELECT name, brand FROM product WHERE id = ?")
                query2.addBindValue(product)
                
                if query2.exec() and query2.next():
                    
                    name = str(query2.value(0))
                    maker = str(query2.value(1))
                    
                
                item_id = QTableWidgetItem(item_id)
                name = QTableWidgetItem(name)
                maker = QTableWidgetItem(maker)
                quantity = QTableWidgetItem(quantity)
                rate = QTableWidgetItem(rate)
                discount = QTableWidgetItem(discount)
                total = QTableWidgetItem(total)
                
                item_id.setFlags(Qt.ItemIsEnabled)
                name.setFlags(Qt.ItemIsEnabled)
                maker.setFlags(Qt.ItemIsEnabled)
                quantity.setFlags(Qt.ItemIsEnabled)
                rate.setFlags(Qt.ItemIsEnabled)
                discount.setFlags(Qt.ItemIsEnabled)
                total.setFlags(Qt.ItemIsEnabled)
                
                self.table.setItem(row, 0, item_id)
                self.table.setItem(row, 1, name)
                self.table.setItem(row, 2, maker)
                self.table.setItem(row, 3, quantity)
                self.table.setCellWidget(row, 4, returned)
                self.table.setItem(row, 5, rate)
                self.table.setItem(row, 6, discount)
                self.table.setItem(row, 7, total)
                

                row += 1
        

        else:
            print("Error Loading Sales Data ", query.lastError().text())
            
          
    
    
    
    
    
    def writeoffcheck(self):
        
        remaining = self.remaining.text()
        remaining = float(remaining) if remaining else 0
        
        if remaining > 0:
            
            if self.checkbox.isChecked():
                
                self.note.setText(f"Amount {remaining} will be wrote-off / Cleared")
            else:
                self.note.setText(f"Amount {remaining} will be added to payables")
        
        else:
            
            self.note.setText(f"Amount {remaining} is excessive and will be added to reciveables from customer")    
    
    

    def update_total_amount(self):
        
        
        subtotal = 0.00
        for row in range(self.table.rowCount()):
            
            linetotal = self.table.item(row, 7).text()
            
            if linetotal:
                try:
                   
                    value = float(linetotal)
                    subtotal = subtotal + value
                    
                except ValueError:
                    pass  # skip empty or invalid cells
                
            else:
                continue
                
        self.subtotal.setText(f"{subtotal:.2f}")
        
        
        rounded_total = math.floor(subtotal)
        roundoff = round(subtotal - rounded_total, 2)
        print("round off is: ", roundoff)
        # set Round off
        
        finaltotal = rounded_total
        
        self.roundoff.setText(f"{roundoff:.2f}")
        self.final_amountdata.setText(f"{finaltotal:.2f}")
        
        

    def calculate_payment(self):
        
        finalamount = self.final_amountdata.text()
        finalamount = float(finalamount) if finalamount else 0.00
        
        paid = self.paid.text()
        paid = float(paid) if paid else 0.00
        
        remaining = finalamount - paid
        self.remaining.setText(str(remaining))
        
        self.writeoffcheck()
         
       
        
        

    def update_table_height(self):
        
        row_count = self.table.rowCount()
        visible_rows = max(row_count, self.min_visible_rows)
        header_height = self.table.horizontalHeader().height()
        total_height = visible_rows * self.row_height + header_height + self.table.frameWidth() * 2 + 6
        self.table.setFixedHeight(total_height)
        
    
    def showEvent(self, event):
        super().showEvent(event)
        print("Widget shown — refreshing data")
        # self.populate_salesman()
        


    def populate_salesman(self):
        
        self.salesman.blockSignals(True)
        
        self.salesman.clear()
        
        query = QSqlQuery()
        
        if query.exec("SELECT id, name FROM employee WHERE status = 'active';"):
            
            while query.next():
                salesman_id = query.value(0)
                salesman_name = query.value(1)
                
                print(salesman_id, salesman_name)
                
                self.salesman.addItem(salesman_name, salesman_id)  # Text shown, ID stored as data
            
        else:
            QMessageBox.information(None, 'Error', query.lastError().text() )
        
        self.salesman.blockSignals(False)
        
        
        
    def save_sales_return(self):
        
        
        db = QSqlDatabase.database()
        db.transaction()
        
        try: 
        
            # salesman = self.salesman.currentData()
            
            # if salesman is None :
                
            #     QMessageBox.warning(self, "Error", "Please select a salesman")
            #     return
            
            print('Starting to save sales return!')
            
            subtotal = self.subtotal.text()
            roundoff = self.roundoff.text()
            total = self.final_amountdata.text()
            paid = self.paid.text()
            remaining = self.remaining.text()
            
            
            subtotal = float(subtotal) if subtotal else 0
            roundoff = float(roundoff) if roundoff else 0
            total = float(total) if total else 0
            paid = float(paid) if paid else 0
            remaining = float(remaining) if remaining else 0
            
            
            if remaining == 0.0:
                
                writeoff = 0.0
                payable = 0.0
                receiveable = 0.0
                
            elif remaining > 0.0 and self.checkbox.isChecked():
                
                writeoff = remaining
                payable = 0.0
                receiveable = 0.0
                
            elif remaining > 0.0 and not self.checkbox.isChecked():
                
                writeoff = 0.0
                payable = remaining
                receiveable = 0.0
                
            else:
                
                writeoff = 0.0
                payable = 0.0
                receiveable = abs(remaining)
                
            print('Preparing Query to save salesreturn')
            query = QSqlQuery()
            
            query.prepare("""
                INSERT INTO salesreturn (salesorder, customer, salesman, subtotal, roundoff, total, paid, remaining, writeoff, payable, receiveable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """)                   
            
            print("cusotmer id is", self.customer_id)
            if self.customer_id == '':
                self.customer_id = None
                
                if remaining != 0 and not self.checkbox.isChecked():
                    
                    QMessageBox.critical(self, "Error", "A Walk-In Customer has to be Paid Full Amount")
                    return
                
                
            query.addBindValue(self.salesorder_id)    
            query.addBindValue(self.customer_id)   
            query.addBindValue(self.salesman_id)
                 
            query.addBindValue(subtotal)
            query.addBindValue(roundoff)
            query.addBindValue(total)
            
            query.addBindValue(paid)
            query.addBindValue(remaining)
            query.addBindValue(writeoff)
            
            query.addBindValue(payable)
            query.addBindValue(receiveable)
            
            print("Prepared Query: ", query.lastQuery())
                
            if not query.exec():
                
                print("Insert failed:", query.lastError().text())
                raise Exception
            
            else:
                
                QMessageBox.information(None, "Success", 'Sales Return Saved Successfully')
                return_id = query.lastInsertId()
                print("Sales return is Saved with Id ", return_id)
                
                
                
            #####################################
            ####      SALES TRANSACTIONS     ####
            #####################################
            
            # get the customer
            print("Staring sales transaction")
            print("CUSTOMER ID is ", self.customer_id)
            
            if self.customer_id is not None:
                
                customer_id = int(self.customer_id)
                
                print("Customer Id is ", customer_id)
                
                customer_query = QSqlQuery()
                customer_query.prepare("SELECT payable, receiveable FROM customer where id = ?")
                customer_query.addBindValue(customer_id)
                
                if customer_query.exec() and customer_query.next():
                    
                    payable_before = customer_query.value(0)
                    receiveable_before = customer_query.value(1)
                    
                    payable_before = float(payable_before)
                    receiveable_before = float(receiveable_before)
                    
                else:
                    
                    print("Error ", customer_query.lastError().text())
                    QMessageBox.critical(self, "Error", "Customer not found or database error.")
                    raise Exception 
                
                
                customer = customer_id
                transaction_type = 'sales return'
                ref_no = None
                return_ref = return_id
                
                payable_before = payable_before
                due_amount = total
                paid = paid
                remaining_due = total - paid
                payable_after = payable_before + total - paid
                
                receiveable_before = receiveable
                receiveable_now = 0.00
                received = 0.00
                remaining_now = 0.00
                receiveable_after = receiveable
                
            else: 
                
                print("We have reached, Walked in Customer which is ", self.customer_id)
                
                customer = None
                transaction_type = 'sales return'
                ref_no = None
                return_ref = return_id
                
                payable_before = 0.00
                due_amount = total
                paid = paid
                remaining_due = total - paid
                payable_after = 0.00
                
                receiveable_before = 0.00
                receiveable_now = 0.00
                received = 0.00
                remaining_now = 0.00
                receiveable_after = 0.00
            

            print("ALL THE VALUES ARE")
            print(customer, transaction_type, ref_no, remaining_due)
            
            salesman = self.salesman_id
            print("Inserting Sales Transaction")
            
            # insert transaction
            query = QSqlQuery()
            query.prepare("""
                          INSERT INTO customer_transaction 
                          (customer, transaction_type, ref, return_ref,
                          payable_before, due_amount, paid, remaining_due, payable_after,
                          receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                          salesman) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                          
                          """)
            
            query.addBindValue(customer)
            query.addBindValue(transaction_type)
            query.addBindValue(ref_no)
            query.addBindValue(return_ref)
            query.addBindValue(payable_before)
            query.addBindValue(due_amount)
            query.addBindValue(paid)
            query.addBindValue(remaining_due)
            query.addBindValue(payable_after)
            query.addBindValue(receiveable_before)
            query.addBindValue(receiveable_now)
            query.addBindValue(received)
            query.addBindValue(remaining_now)
            query.addBindValue(receiveable_after)
            query.addBindValue(salesman)
            
            
            if query.exec():
                
                insert_id = query.lastInsertId()
                print("Transaction is saved ...")
                QMessageBox.information(None, "Success", "Customer Transaction Stored Successfully with ID: " + str(insert_id) )
                
                
            else:
                
                QMessageBox.critical(None, "Error", query.lastError().text())
                print("Query error:", query.lastError().text())
                raise Exception 
            
            print("no2... Customer is : n", customer)
            
            if self.customer_id is not None:
                
                customer_query = QSqlQuery()
                customer_query.prepare("SELECT payable, receiveable FROM customer where id = ?")
                customer_query.addBindValue(self.customer_id)
                
                if customer_query.exec() and customer_query.next():
                    
                    customer_payable = customer_query.value(0)
                    customer_receiveable = customer_query.value(1)

                    customer_payable = float(customer_payable)
                    customer_receiveable = float(customer_receiveable)
                                
                else:
                    
                    print("Error ", customer_query.lastError().text())
                    QMessageBox.critical(self, "Error", "customer not found or database error.")
                    raise Exception
            
            
                print("Payable and Receiveable are : ", customer_payable, customer_receiveable)
                
                customer_payable = customer_payable + payable
                customer_receiveable = customer_receiveable + receiveable
                
                update_customer = QSqlQuery()
                update_customer.prepare("UPDATE customer SET payable = ? , receiveable = ? WHERE id = ?")
                
                update_customer.addBindValue(customer_payable)
                update_customer.addBindValue(customer_receiveable)
                update_customer.addBindValue(self.customer_id)
                
                print("New Payable and Receiveable are : ", customer_payable, customer_receiveable)
                
                if update_customer.exec(): 
                    
                    print("customer Balance updated successfully")
                
                else:
                    QMessageBox.critical(self, "Error", update_customer.lastError().text())
                    raise Exception
                
                
            for row in range(self.table.rowCount()):

                try:
                    
                    item = self.table.item(row, 0).text()
                    item = int(item)
                    
                    product_query = QSqlQuery()
                    product_query.prepare("SELECT product from salesitem where id = ?")
                    product_query.addBindValue(item)
                    
                    if product_query.exec() & product_query.next():
                        
                       product = product_query.value(0)
                       
                    
                    sold = self.table.item(row, 3).text()
                    returned = int(self.table.cellWidget(row, 4).text())
                    returned = int(returned) if returned else 0
                    rate = float(self.table.item(row, 5).text())
                    discount = float(self.table.item(row, 6).text())
                    total = float(self.table.item(row, 7).text())
                    
                    
                    # get the Sales order by
                    
                    
                except Exception as e:
                    
                    print("Exception: ", str(e))


                item_query = QSqlQuery()
                item_query.prepare("""
                    INSERT INTO salesreturn_item (salesreturn, product, sold, returned, rate, discount, total)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                """)
                
                item_query.addBindValue(return_id)
                item_query.addBindValue(product)
                item_query.addBindValue(sold)
                item_query.addBindValue(returned)
                item_query.addBindValue(rate)
                item_query.addBindValue(discount)
                item_query.addBindValue(total)

                if not item_query.exec():
                    print("Error inserting salesitem:", item_query.lastError().text())
                
                else:
                    print("Sales item inserted successfully")
                    item = item_query.lastInsertId()
                    
                    

                # ✅ Check and update stock
                stock_query = QSqlQuery()
                stock_query.prepare("SELECT units FROM stock WHERE product = ?")
                stock_query.addBindValue(product)

                if stock_query.exec() and stock_query.next():
                    
                    units = stock_query.value(0)
                    
                    units = int(units)
                    
                    update_query = QSqlQuery()
                    update_query.prepare("UPDATE stock SET units = ? WHERE product = ?")
                    update_query.addBindValue(units)
                    update_query.addBindValue(product)

                    if update_query.exec():
                        
                        print("Stock increased because of return...  successfully")

                        self.clear_fields()
                    else:
                        print("Failed to update stock:", update_query.lastError().text())
                
                    
            
        
        
        except Exception as e:
            print("An error occurred:", str(e))
            QMessageBox.critical(None, "Error", f"An error occurred while saving the Sales: {str(e)}")
            db.rollback()
        
        else:
            db.commit()
            print("Transaction committed successfully")
            QMessageBox.information(None, "Success", "Sales saved successfully")
        
        finally:
            print("Database connection closed")
        
        
        
    def load_product_suggestions(self, item, completer):
        
        print("Loading Medicine Suggestions")
        item = item
        completer = completer
        current_text = item.currentText() 
        print("Current Text is: ", current_text)
        
        if current_text == '':
            return 
        
        query = QSqlQuery()
        query.prepare("""
            SELECT id, name, form, strength
            FROM product
            WHERE name LIKE ? LIMIT 10 """)
        
        value = f"%{current_text}%"
        query.addBindValue(value)
        
        products = []
        
        if not query.exec():
            
            print("Something wrong happened...")
        
        else:
        
            while query.next():
                
                product_id = query.value(0)
                name = query.value(1)
                form = query.value(2)
                strength = query.value(3)
                
                label = f"{name} {form} {strength}".strip()
                products.append(label)
                item.addItem(label, product_id)
                
        print(products)

        
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        data = products
        model = QStringListModel()
        model.setStringList(data)
        
        
        completer.setModel(model)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        item.setCompleter(completer)
        
        completer.highlighted[str].connect(partial(self.on_completer_highlighted, item=item))

        print("Setting Current Text")
        item.lineEdit().setText(current_text)        
        
        
        

    def on_batch_highlighted(self, text, item):
        
        
        # Prevent redundant triggers for the same value
        # if hasattr(self, "_last_highlighted") and self._last_highlighted == text:
        #     return
        
        # self._last_highlighted = text
        
        # index = item.findText(text, Qt.MatchFixedString)
        # if index >= 0:
        #     item.setCurrentIndex(index)
            
            
        row = self.table.indexAt(item.pos()).row()
        batch = self.table.cellWidget(row, 2).currentText()
        
        self.table.cellWidget(row, 3).clear()
        
        
        print("Batch is: ", batch)

        stock_query = QSqlQuery()
        stock_query.prepare("SELECT Salesitem FROM batch WHERE batch = ?")
        stock_query.addBindValue(batch)
        

        try:
            
            if stock_query.exec() and stock_query.next():
                
                Salesitem = stock_query.value(0)
                Salesitem = int(Salesitem)
                
                print(f"Sales item info is: {Salesitem}")
                
                item_query = QSqlQuery()
                item_query.prepare("SELECT qty, rate, discount, tax, Sales FROM Salesitem WHERE id = ?")
                item_query.addBindValue(Salesitem)
                
                if item_query.exec() and item_query.next():
                    
                    self.table.cellWidget(row, 3).setText('')
                    
                    qty = item_query.value(0)
                    qty = str(qty)
                    rate = item_query.value(1)
                    rate = str(rate)
                    discount = item_query.value(2)
                    tax = item_query.value(3)
                    discount = str(discount)
                    tax = str(tax)
                    
                    Sales = item_query.value(4)
                    Sales = int(Sales)
                    
                    self.table.cellWidget(row, 3).setText(str(Sales))
                    self.table.cellWidget(row, 4).setText(qty)
                    self.table.cellWidget(row, 6).setText(rate)
                    self.table.cellWidget(row, 7).setText(discount)
                    self.table.cellWidget(row, 8).setText(tax)
                    
                    Sales_query = QSqlQuery()
                    Sales_query.prepare("SELECT id, discount, tax FROM Sales WHERE id = ?")
                    Sales_query.addBindValue(Sales)
                    
                    if Sales_query.exec() and Sales_query.next():
                        
                        self.table.cellWidget(row, 8).setText('')
                        self.table.cellWidget(row, 9).setText('')
                        
                        po = str(Sales_query.value(0))
                        po_discount = str(Sales_query.value(1))
                        po_tax = str(Sales_query.value(2))
                        
                        self.table.cellWidget(row, 8).setText(po_discount)
                        self.table.cellWidget(row, 9).setText(po_tax)
                        
                        
                    else:
            
                        QMessageBox.information(None, 'Error', Sales_query.lastError().text())
                
                else:
            
                        QMessageBox.information(None, 'Error', item_query.lastError().text())        
                    
            else:
            
                QMessageBox.information(None, 'Error', stock_query.lastError().text())

        except Exception as e:
                
            print(str(e))
        
        

    def on_completer_highlighted(self, text, item):
        
        
        # Prevent redundant triggers for the same value
        if hasattr(self, "_last_highlighted") and self._last_highlighted == text:
            return
        self._last_highlighted = text
        
        index = item.findText(text, Qt.MatchFixedString)
        if index >= 0:
            item.setCurrentIndex(index)
            
            
        row = self.table.indexAt(item.pos()).row()
        product_id = self.table.cellWidget(row, 1).currentData()
        
        self.table.cellWidget(row, 2).clear()
        
        
        print("Product id is: ", product_id)

        stock_query = QSqlQuery()
        stock_query.prepare("SELECT batch FROM batch WHERE product = ?")
        stock_query.addBindValue(product_id)
        

        try:
            
            if stock_query.exec():
                
                while stock_query.next():  
                      
                    batch = stock_query.value(0)
                    
                    print(f"Batch info is: {batch}")
                    
                    self.table.cellWidget(row, 2).addItem(batch)
                    
                
                widget = self.table.cellWidget(row, 2)
                self.table.cellWidget(row, 2).setCurrentIndex(0)
                self.table.cellWidget(row, 3).setText('')
                
                widget.activated.connect(partial(self.update_amount(widget)))
                
                
            else:
            
                QMessageBox.information(None, 'Error', stock_query.lastError().text())

        except Exception as e:
                
            print(str(e))
        
        


    def on_item_selected(self, item):
        
        text = item.currentText()
        data = item.currentData()

        
        print("Selected text is: ",text, data)
        data = int(data)
        
        query = QSqlQuery()
        query.prepare("""
            SELECT * FROM product
            WHERE id = ? """)
        
        query.addBindValue(data)
        
        if not query.exec():
            
            print("Cannot Get the product")
            
        else:
            
            print("Got the product")
                
                



    def update_amount(self, edited_widget):
        
        row = self.table.indexAt(edited_widget.pos()).row()
        
        try:
            
            sold = self.table.item(row, 3).text()
            qty_text = self.table.cellWidget(row, 4).text()
            
            if int(qty_text) > int(sold):
                
                QMessageBox.information(None, "Error", "Returned Quantity cannot be greater than Sold Qty")
                self.table.cellWidget(row, 4).setText("0")
                qty_text = 0
            
            rate_text = self.table.item(row, 5).text()
            discount_edit = self.table.item(row,6).text()
            
            qty = int(qty_text) if qty_text else 0
            rate = float(rate_text) if rate_text else 0
            discount = float(discount_edit) if discount_edit else 0
            
            amount = qty * rate
            
            discount = amount * discount / 100
            amount = amount - discount
            
            
            amount = float(f"{amount:.2f}")
            amount = str(amount)
            
            amount = QTableWidgetItem(amount)            
            self.table.setItem(row, 7, amount)
            print("Updating Final Amount")
            self.update_total_amount()
            
            
        except ValueError:
        
            self.table.cellWidget(row, 7).setText("0.00")



    def on_cell_focus(self, row, column):
        
        index = self.table.model().index(row, column)
        self.table.edit(index)  # Start editing cell

        QTimer.singleShot(0, lambda: self._select_all_in_focus_widget())
    
    

    def _select_all_in_focus_widget(self):
        
        editor = self.table.focusWidget()
        if isinstance(editor, QLineEdit):
            editor.selectAll()
        elif isinstance(editor, QComboBox) and editor.isEditable():
            editor.lineEdit().selectAll()
    
    
    def clear_fields(self):
        
        self.salesorder.clear()
        self.customer.clear()
        self.salesman.clear()
        self.subtotal.clear()
        self.roundoff.clear()
        self.final_amountdata.clear()
        self.paid.clear()
        self.remaining.clear()
        self.checkbox.setChecked(False)        
        self.note.clear()
        self.table.setRowCount(0)
        
        
  

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

