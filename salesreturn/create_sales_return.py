
from PySide6.QtWidgets import QWidget, QCompleter, QDateEdit, QVBoxLayout,  QHBoxLayout, QFrame, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
from PySide6.QtCore import QFile, Qt, QStringListModel, QDate, QDateTime, QTimer, Signal
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import QPalette, QColor, QKeyEvent
from functools import partial
import csv    
import os
import math

from medic.utilities.stylus import load_stylesheets
from medic.utilities.activity_logger import log_activity
from medic.utilities.permissions import Permissions
from medic.utilities.session_gate import require_open_session
from medic.utilities.session_service import get_active_session_id
from medic.utilities.payment_handler import PaymentMethodHandler
from medic.utilities.app_messagebox import AppMessageBox
from services.inventory_movement_service import fetch_product_batch_numbers
from services.sales_return_service import (
    build_sales_return_header_payload,
    build_sales_return_transaction_payload,
    compute_sales_return_inventory_plan,
    compute_sales_return_settlement,
    normalize_sales_return_item_row,
)
from services.sales_return_transaction_service import (
    fetch_already_returned_qty,
    fetch_customer_balances_for_return,
    fetch_sales_item_qty_sold,
    fetch_sold_batch_rows_for_return,
    increment_sold_batch_returned,
    insert_customer_return_transaction,
    insert_sales_return_header,
    insert_sales_return_item,
    restore_batch_quantity,
    update_customer_return_balances,
)


class KeyUpLineEdit(QLineEdit):
    keyReleased = Signal(QKeyEvent)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.keyReleased.emit(event)




class AddSalesReturnWidget(QWidget):


    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Sales Return Invoice", objectName="SectionTitle")
        self.invoicelist = QPushButton("Sales Returns List", objectName="TopRightButton")
        self.invoicelist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
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

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10])
        headers = ["#", "Product","Manufacturer", " Sold", "Return", "Rate", "Total"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)   

        self.table.setMinimumWidth(700)
        
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
        
        
        
        payment_method_layout = QHBoxLayout()
        
        payment_method_label = QLabel("Payment Method")
        
        self.payment_handler = PaymentMethodHandler(self)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)
        
        payment_method_layout.addWidget(payment_method_label, 1)
        payment_method_layout.addWidget(self.payment_method, 1)
        
        
        self.layout.addLayout(payment_method_layout)
        
        
        
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
        
        
        # === Action Buttons ===
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(10)

        savebutton = QPushButton("Save Return Information", objectName="SaveButton")
        savebutton.setCursor(Qt.PointingHandCursor)
        savebutton.clicked.connect(lambda: self.save_sales_return())

        clear_button = QPushButton("Clear Return", objectName="TopRightButton")
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.clicked.connect(self.confirm_clear_return)

        action_row.addWidget(savebutton, 1)
        action_row.addWidget(clear_button)

        self.layout.addLayout(action_row)
        self.layout.addStretch()
        
        
        
        # Apply stylesheet
        
        self.setStyleSheet(load_stylesheets())

        self.layout.addStretch()

    def _safe_float_text(self, value):
        try:
            return float(value) if value not in (None, "") else 0.0
        except (TypeError, ValueError):
            return 0.0

    def _count_positive_return_rows(self):
        count = 0
        for row in range(self.table.rowCount()):
            returned_widget = self.table.cellWidget(row, 4)
            if returned_widget is None:
                continue
            try:
                if int(returned_widget.text() or 0) > 0:
                    count += 1
            except ValueError:
                continue
        return count

    def _lookup_salesitem_product_id(self, salesitem_id):
        product_query = QSqlQuery()
        product_query.prepare("""
            SELECT product_id
            FROM salesitem
            WHERE id = ?
        """)
        product_query.addBindValue(salesitem_id)

        if not (product_query.exec() and product_query.next()):
            raise Exception("Product lookup failed")
        return product_query.value(0)

    def _lookup_sales_header(self, sales_id):
        query = QSqlQuery()
        query.prepare("""
            SELECT
                customer,
                salesman,
                discount,
                tax,
                creation_date
            FROM sales
            WHERE id = ?
        """)
        query.addBindValue(sales_id)
        if not (query.exec() and query.next()):
            return None
        return {
            "customer": query.value(0),
            "salesman": query.value(1),
            "discount": query.value(2),
            "tax": query.value(3),
            "creation_date": query.value(4),
        }

    def _lookup_customer_label(self, customer_id):
        if customer_id in (None, ""):
            return "Walk-in Customer"
        customer_query = QSqlQuery()
        customer_query.prepare("SELECT name FROM customer WHERE id = ?")
        customer_query.addBindValue(int(customer_id))
        if customer_query.exec() and customer_query.next():
            customer_name = customer_query.value(0)
            return f"{customer_id} - {customer_name}"
        raise Exception(customer_query.lastError().text() or "Customer lookup failed")

    def _lookup_salesman_label(self, salesman_id):
        salesman_query = QSqlQuery()
        salesman_query.prepare("SELECT firstname, lastname FROM auth WHERE id = ?")
        salesman_query.addBindValue(int(salesman_id))
        if salesman_query.exec() and salesman_query.next():
            firstname = salesman_query.value(0)
            lastname = salesman_query.value(1)
            return f"{salesman_id} - {firstname} {lastname}"
        raise Exception(salesman_query.lastError().text() or "Salesman lookup failed")

    def _lookup_product_display(self, product_id):
        query = QSqlQuery()
        query.prepare("SELECT display_name, brand FROM product WHERE id = ?")
        query.addBindValue(product_id)
        if query.exec() and query.next():
            return str(query.value(0)), str(query.value(1))
        raise Exception(query.lastError().text() or "Product lookup failed")

    def _collect_sales_return_amounts(self):
        return {
            "subtotal": self._safe_float_text(self.subtotal.text()),
            "roundoff": self._safe_float_text(self.roundoff.text()),
            "total": self._safe_float_text(self.final_amountdata.text()),
            "paid": self._safe_float_text(self.paid.text()),
            "remaining": self._safe_float_text(self.remaining.text()),
        }

    def _collect_sales_return_row(self, row):
        salesitem_id = int(self.table.item(row, 0).text())
        product_id = self._lookup_salesitem_product_id(salesitem_id)

        returned = int(self.table.cellWidget(row, 4).text() or 0)
        if returned <= 0:
            return None

        return normalize_sales_return_item_row(
            row_number=row + 1,
            salesitem_id=salesitem_id,
            product_id=product_id,
            sold_qty=self.table.item(row, 3).text(),
            return_qty=returned,
            rate=self.table.item(row, 5).text(),
            total=self.table.item(row, 6).text(),
        )

    def _insert_sales_return_item(self, return_id, normalized_row):
        return insert_sales_return_item(return_id, normalized_row)



    def on_payment_method_changed(self, method):
        
        success = self.payment_handler.handle_method_change(method)

        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)    

        
        
        
    def get_sales_order(self):
        
        order_id_text = self.salesorder.text().strip()
        if order_id_text == '':
            AppMessageBox.information(self, "Error", "Please enter the sales id")
            return
        try:
            order_id = int(order_id_text)
        except ValueError:
            AppMessageBox.information(self, "Not Found", f"No sales record found for '{order_id_text}'.")
            self.salesorder.clear()
            self.salesorder.setFocus()
            return

        self.load_sales_data(order_id)
            
            

    
    
    def load_sales_data(self, id):
        
        self.salesorder_id = id
        print("Loading Sales ID:", id)
        sales_header = self._lookup_sales_header(id)
        if sales_header:
            customer = sales_header["customer"]
            salesman = sales_header["salesman"]
            
            self.customer_id = customer
            self.salesman_id = salesman
            
            print("customer and salesman is: ", customer, salesman)
            
            invoicedate = sales_header["creation_date"]
            
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
                customerwithid = self._lookup_customer_label(customer)
                print("Customer with id ", customerwithid)
                self.customer.setText(customerwithid)
            
            else:
                
                print("customer is None")
                self.customer.setText('Walk-In Customer')  
            
            
            salesmanwithid = str(self._lookup_salesman_label(salesman))
            print("Salesman with id ", salesmanwithid)
            self.salesman.setText(salesmanwithid)
                
                
            self.load_items_into_table(id)
            
        else:
            self.salesorder.clear()
            self.salesorder.setFocus()
            AppMessageBox.information(self, "Not Found", f"No sales record found for ID {id}.")
        



    def load_items_into_table(self, id):
        
        print("Loading Sales items into table")
        
        query = QSqlQuery()
        query.prepare("""
            SELECT
                id,
                product_id,
                qty_sold,
                effective_line_total
            FROM salesitem
            WHERE sales_id = ?
        """)
        query.addBindValue(id)

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
       
        if query.exec():
            
            print("Loading items into table")
            
            while query.next():
                
                self.table.insertRow(row)
                
                item_id = str(query.value(0))
                product = int(query.value(1))
                
                quantity = int(query.value(2))
                print("Loading Sold Quantity that is: ", quantity)
                effective_total = float(query.value(3) or 0.0)
                
                rate = effective_total / quantity if quantity else 0
                
                print("Effective rate is : ", rate)
                
                returned = QLineEdit()
                returned.setText("0")
                returned.textChanged.connect(lambda _: self.update_amount(returned))
                                
                total = "0.0"
                name, maker = self._lookup_product_display(product)
                    
                
                item_id = QTableWidgetItem(item_id)
                name = QTableWidgetItem(name)
                maker = QTableWidgetItem(maker)
                quantity = QTableWidgetItem(str(quantity))
                rate = QTableWidgetItem(str(rate))
                total = QTableWidgetItem(total)
                
                item_id.setFlags(Qt.ItemIsEnabled)
                name.setFlags(Qt.ItemIsEnabled)
                maker.setFlags(Qt.ItemIsEnabled)
                quantity.setFlags(Qt.ItemIsEnabled)
                rate.setFlags(Qt.ItemIsEnabled)
                total.setFlags(Qt.ItemIsEnabled)
                
                self.table.setItem(row, 0, item_id)
                self.table.setItem(row, 1, name)
                self.table.setItem(row, 2, maker)
                self.table.setItem(row, 3, quantity)
                self.table.setCellWidget(row, 4, returned)
                self.table.setItem(row, 5, rate)
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
            
            linetotal = self.table.item(row, 6).text()
            
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
            AppMessageBox.information(None, 'Error', query.lastError().text() )
        
        self.salesman.blockSignals(False)
        
        

        
    @Permissions.require_permission('salesreturn.create')
    def save_sales_return(self):
        if not require_open_session(self):
            return

        db = QSqlDatabase.database()

        if not db.transaction():
            AppMessageBox.critical(None, "Database Error", "Could not start transaction.")
            return

        try:

            print('Starting to save sales return!')
            amounts = self._collect_sales_return_amounts()
            subtotal = amounts["subtotal"]
            roundoff = amounts["roundoff"]
            total = amounts["total"]
            paid = amounts["paid"]
            remaining = amounts["remaining"]
            return_item_count = self._count_positive_return_rows()

            if return_item_count <= 0:
                raise ValueError("Enter at least one returned item before saving the sales return.")

            settlement = compute_sales_return_settlement(
                total=total,
                paid=paid,
                writeoff_enabled=self.checkbox.isChecked(),
            )
            remaining = settlement["remaining"]
            writeoff = settlement["writeoff"]
            payable = settlement["payable"]
            receiveable = settlement["receiveable"]

            session_id = get_active_session_id(strict=True)
            if session_id is None:
                raise Exception("No active session found.")

            customer_id = self.customer_id

            print("customer id is", customer_id)
            if customer_id == '':
                customer_id = None

                if remaining != 0 and not self.checkbox.isChecked():
                    AppMessageBox.critical(self, "Error", "A Walk-In Customer has to be Paid Full Amount")
                    raise Exception("Walk-in customer must be settled fully.")

            print('Preparing Query to save salesreturn')
            header_payload = build_sales_return_header_payload(
                salesorder_id=self.salesorder_id,
                customer_id=customer_id,
                salesman_id=self.salesman_id,
                subtotal=subtotal,
                roundoff=roundoff,
                total=total,
                paid=paid,
                session_id=session_id,
                settlement=settlement,
            )
            return_id = insert_sales_return_header(header_payload)
            print("Sales return is Saved with Id", return_id)

            #####################################
            ####      SALES TRANSACTIONS     ####
            #####################################

            print("Starting Sales Return Transaction")
            print("CUSTOMER ID is", customer_id)

            payment = self.payment_handler.payment_data.copy()
            salesman = self.salesman_id
            paid_now = paid

            # ===============================
            # CUSTOMER EXISTS
            # ===============================
            if customer_id is not None:

                customer = int(customer_id)
                balances = fetch_customer_balances_for_return(customer)
                payable_before = balances["payable_before"]
                receiveable_before = balances["receiveable_before"]

            # ===============================
            # WALK-IN CUSTOMER
            # ===============================
            else:

                print("Walk-in customer")

                customer = None

                payable_before = 0.0
                receiveable_before = 0.0

            txn_payload = build_sales_return_transaction_payload(
                return_id=return_id,
                customer_id=customer_id,
                salesman_id=salesman,
                total=total,
                paid=paid_now,
                session_id=session_id,
                payment=payment,
                payable_before=payable_before,
                receiveable_before=receiveable_before,
            )
            insert_customer_return_transaction(txn_payload)

            if customer_id is not None:
                update_customer_return_balances(
                    customer,
                    payable_after=txn_payload["payable_after"],
                    receiveable_after=txn_payload["receiveable_after"],
                )

            for row in range(self.table.rowCount()):

                try:
                    normalized_row = self._collect_sales_return_row(row)
                    if normalized_row is None:
                        continue

                except Exception as e:
                    raise Exception(f"Row {row + 1}: {str(e)}")

                print("Passing salesitem_id to reverse_inventory_for_return:", normalized_row["salesitem_id"])
                self.reverse_inventory_for_return(normalized_row["salesitem_id"], normalized_row["returned"], db)

                insert_id = self._insert_sales_return_item(return_id, normalized_row)
                print("Sales Return Item inserted")
                print("last INSERTED ID IS", insert_id)

        except Exception as e:
            print("An error occurred:", str(e))
            AppMessageBox.critical(None, "Error", f"An error occurred while saving the Sales Return: {str(e)}")
            db.rollback()

        else:
            db.commit()
            customer_label = str(self.customer_id) if self.customer_id not in (None, "") else "Walk-in"
            log_activity(
                category="sales",
                action="sales_return_created",
                entity_type="sales_return",
                entity_id=int(return_id),
                note=(
                    f"Sales return #{return_id} was recorded for customer {customer_label}. "
                    f"It is linked to sale #{self.salesorder_id}, covers {return_item_count} item(s), "
                    f"and totals {total}."
                ),
                previous_value=None,
                new_value=str(total)
            )
            print("Transaction committed successfully")
            AppMessageBox.information(None, "Success", "Sales return saved successfully")
            self.clear_fields()

        finally:
            print("Database connection closed")    



    
    def reverse_inventory_for_return(self, sales_item_id: int, return_qty: int, db=None):

        print("Passing salesitem_id to reverse_inventory_for_return:", sales_item_id)

        try:
            sales_item_id = int(sales_item_id)
            return_qty = int(return_qty)

            if return_qty <= 0:
                raise Exception("Return quantity must be greater than zero")

            # --------------------------------------------------
            # 1️⃣ Validate returnable quantity
            # --------------------------------------------------
            print("Sales Item id is", sales_item_id)
            qty_sold = fetch_sales_item_qty_sold(sales_item_id)

            print("Checking if already returned or not")

            already_returned = fetch_already_returned_qty(sales_item_id)

            if already_returned + return_qty > qty_sold:
                raise Exception("Return quantity exceeds sold quantity")

            # --------------------------------------------------
            # 2️⃣ Fetch sold batches in reverse order
            # --------------------------------------------------
            batch_rows = fetch_sold_batch_rows_for_return(sales_item_id)

            plan = compute_sales_return_inventory_plan(
                qty_sold=qty_sold,
                already_returned=already_returned,
                return_qty=return_qty,
                sold_batch_rows=batch_rows,
            )

            for allocation in plan["allocations"]:
                sold_batch_id = allocation["sold_batch_id"]
                batch_id = allocation["batch_id"]
                qty_to_restore = allocation["qty_to_restore"]
                restore_batch_quantity(batch_id, qty_to_restore)
                increment_sold_batch_returned(sold_batch_id, qty_to_restore)

        except Exception as e:
            raise Exception(f"Sales return inventory reversal failed: {str(e)}")
            


        
    
        
  

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
        

        try:
            batches = fetch_product_batch_numbers(product_id)
            for batch in batches:
                print(f"Batch info is: {batch}")
                self.table.cellWidget(row, 2).addItem(batch)

            widget = self.table.cellWidget(row, 2)
            if widget.count() > 0:
                self.table.cellWidget(row, 2).setCurrentIndex(0)
                self.table.cellWidget(row, 3).setText('')
                try:
                    widget.activated.disconnect()
                except Exception:
                    pass
                widget.activated.connect(partial(self.update_amount(widget)))
            else:
                self.table.cellWidget(row, 3).setText('')

        except Exception as e:
                
            print(str(e))
        
        


    def on_item_selected(self, item):
        
        text = item.currentText()
        data = item.currentData()

        
        print("Selected text is: ",text, data)
        data = int(data)
        
        query = QSqlQuery()
        query.prepare("""
            SELECT display_name, brand
            FROM product
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
                
                AppMessageBox.information(None, "Error", "Returned Quantity cannot be greater than Sold Qty")
                self.table.cellWidget(row, 4).setText("0")
                qty_text = 0
            
            rate_text = self.table.item(row, 5).text()
            
            qty = int(qty_text) if qty_text else 0
            rate = float(rate_text) if rate_text else 0
            
            amount = qty * rate
            
            
            
            amount = float(f"{amount:.2f}")
            amount = str(amount)
            
            amount = QTableWidgetItem(amount)            
            self.table.setItem(row, 6, amount)
            print("Updating Final Amount")
            self.update_total_amount()
            
            
        except ValueError:
        
            self.table.cellWidget(row, 6).setText("0.00")



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
        
        self.payment_method.blockSignals(True); 
        self.payment_method.setCurrentIndex(0) 
        self.payment_method.blockSignals(False)
        self.salesorder.setFocus()

    def confirm_clear_return(self):
        _, accepted = AppMessageBox.confirm(
            self,
            "Clear Sales Return",
            "Clear the current sales return and reset all fields?",
            confirm_label="Clear Return",
            cancel_label="Keep Editing",
        )
        if accepted:
            self.clear_fields()
        
        
  

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
