from PySide6.QtWidgets import QWidget, QSizePolicy, QPushButton, QLabel, QHBoxLayout, QFrame, QHeaderView, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, QDateEdit, QCheckBox, QMessageBox
from PySide6.QtCore import QFile, Qt, QDate, QDateTime
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from utilities.stylus import load_stylesheets
from utilities.permissions import Permissions
from utilities.app_messagebox import AppMessageBox





class PurchaseDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Invoice Detail", objectName="SectionTitle")
        self.invoicelist = QPushButton("Invoice List", objectName="TopRightButton")
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
        
        
        labels = ["Invoice Id", "Supplier", "Seller Invoice", "Seller Rep", "Order Date", "Due Date"]

        
        
        self.invoice_data = QLabel()
        self.supplier_data = QLabel()
        self.sellerinvoice_data = QLabel()
        self.rep_data = QLabel("-")
        self.orderdate_data = QLabel()
        self.due_date_data = QLabel("No Due Date")
        
        
        fields = [
            self.invoice_data,
            self.supplier_data,
            self.sellerinvoice_data,
            self.rep_data,
            self.orderdate_data,
            self.due_date_data,
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

        # Due date editing controls for existing purchases
        due_date_row = QHBoxLayout()
        due_date_label = QLabel("Set Due Date")
        due_date_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        due_date_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        due_date_label.setStyleSheet("font-weight: normal; color: #444;")
        due_date_label.setMinimumWidth(200)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDisplayFormat("dd-MM-yyyy")
        self.due_date_edit.setDate(QDate.currentDate())

        self.no_due_date_check = QCheckBox("No Due Date")
        self.save_due_date_btn = QPushButton("Update Due Date")
        self.save_due_date_btn.setCursor(Qt.PointingHandCursor)

        due_date_row.addWidget(due_date_label, 2)
        due_date_row.addWidget(self.due_date_edit, 4)
        due_date_row.addWidget(self.no_due_date_check, 2)
        due_date_row.addWidget(self.save_due_date_btn, 2)
        self.layout.addLayout(due_date_row)

        self.no_due_date_check.toggled.connect(lambda checked: self.due_date_edit.setEnabled(not checked))
        self.save_due_date_btn.clicked.connect(self.update_purchase_due_date)

        self.current_purchase_id = None
        self.current_remaining = 0.0
        self.current_writeoff = 0.0
            
        
        
        
        
        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10, 0.10])
        headers = ["Product", "Brand", "Qty", "Bonus", "Rate", "Disc", "Tax", "Total"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        
        self.table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)   

        self.table.setMinimumWidth(900)
        
        # Hide vertical header (row numbers)
        self.table.verticalHeader().setVisible(False)
        
        # Alternating row colors
        self.table.setAlternatingRowColors(True)

        # Selection behaviour
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        
        self.layout.addStretch()
        

        
        
        labels = [
            "Sub Total",
            "Discount",
            "Tax 236(G)",
            "Tax 236(H)",
            "Sales Tax",
            "Net Amount",
            "CN Adjustment",
            "Grand Total",
            "Paid",
            "Remaining",
            "Write-Off",
        ]

        
        self.subtotal = QLabel()
        self.discount = QLabel()
        self.tax_236g = QLabel()
        self.tax_236h = QLabel()
        self.sales_tax = QLabel()
        self.netamount = QLabel()
        self.roundoff = QLabel()
        self.finalamount = QLabel()
        self.paid = QLabel()
        self.remaining = QLabel()
        self.writeoff = QLabel()
        
        fields = [
            self.subtotal,
            self.discount,
            self.tax_236g,
            self.tax_236h,
            self.sales_tax,
            self.netamount,
            self.roundoff,
            self.finalamount,
            self.paid,
            self.remaining,
            self.writeoff,
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
        query.prepare(
            """
            SELECT
                id,
                supplier,
                rep,
                sellerinvoice,
                creation_date,
                subtotal,
                discount,
                tax_236g,
                tax_236h,
                salestax,
                netamount,
                cn_adjustment,
                total,
                paid,
                remaining,
                writeoff,
                due_date
            FROM purchase
            WHERE id = ?
            """
        )
        query.addBindValue(id)
        
        
        
        if query.exec() and query.next():
            
            orderid = query.value(0)
            supplierid = query.value(1)
            rep_id = query.value(2)
            sellerinvoice = query.value(3)
            print("Seller invoice is: ", sellerinvoice)
            invoicedate = query.value(4)
            
            subtotal = float(query.value(5) or 0)
            discount = float(query.value(6) or 0)
            tax_236g = float(query.value(7) or 0)
            tax_236h = float(query.value(8) or 0)
            sales_tax = float(query.value(9) or 0)
            net_amount = float(query.value(10) or 0)
            cn_adjustment = float(query.value(11) or 0)
            total = float(query.value(12) or 0)
            paid = float(query.value(13) or 0)
            remaining = float(query.value(14) or 0)
            writeoff = float(query.value(15) or 0)
            due_date = query.value(16)
            
            print("Received Data is: ", orderid, supplierid, sellerinvoice, invoicedate, subtotal, discount, net_amount, cn_adjustment, total, paid, remaining, writeoff)
            
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
            
            self.subtotal.setText(f"{subtotal:.2f}")
            self.discount.setText(f"{discount:.2f}")
            self.tax_236g.setText(f"{tax_236g:.2f}")
            self.tax_236h.setText(f"{tax_236h:.2f}")
            self.sales_tax.setText(f"{sales_tax:.2f}")
            self.netamount.setText(f"{net_amount:.2f}")
            self.roundoff.setText(f"{cn_adjustment:.2f}")
            self.finalamount.setText(f"{total:.2f}")
            self.paid.setText(f"{paid:.2f}")
            self.remaining.setText(f"{remaining:.2f}")
            self.writeoff.setText(f"{writeoff:.2f}")

            self.current_purchase_id = orderid
            self.current_remaining = float(remaining or 0)
            self.current_writeoff = float(writeoff or 0)

            if isinstance(due_date, QDate):
                due_date_qdate = due_date
                due_date_text = due_date_qdate.toString("dd-MM-yyyy")
            else:
                due_date_text = str(due_date or "").strip()
                due_date_qdate = QDate.fromString(due_date_text, "yyyy-MM-dd")

            if due_date_text:
                self.due_date_data.setText(due_date_text)
            else:
                self.due_date_data.setText("No Due Date")

            if due_date_qdate.isValid():
                self.due_date_edit.setDate(due_date_qdate)
                self.no_due_date_check.setChecked(False)
            else:
                self.due_date_edit.setDate(QDate.currentDate())
                self.no_due_date_check.setChecked(True)

            self.update_due_date_editor_state()
        
            
            query2 = QSqlQuery()
            query2.prepare("SELECT name FROM supplier WHERE id = ?")
            query2.addBindValue(supplierid)
            
            if query2.exec() and query2.next():
                
                supplier = query2.value(0)
                self.supplier_data.setText(supplier)

            if rep_id not in (None, "", 0):
                rep_query = QSqlQuery()
                rep_query.prepare("SELECT name FROM rep WHERE id = ?")
                rep_query.addBindValue(int(rep_id))
                if rep_query.exec() and rep_query.next():
                    self.rep_data.setText(str(rep_query.value(0) or "-"))
                else:
                    self.rep_data.setText("-")
            else:
                self.rep_data.setText("-")
                
            
            self.load_items_into_table(orderid)
            
            
        else:
            print("Purchase not found for ID:", id)
            print("Query error:", query.lastError().text())
            self.supplier_data.setText("Purchase not found.")

    def update_due_date_editor_state(self):
        """Allow editing due date only when invoice has unpaid payable balance and is not written off."""
        can_edit_due_date = self.current_remaining > 0 and self.current_writeoff <= 0

        self.save_due_date_btn.setEnabled(can_edit_due_date)
        self.no_due_date_check.setEnabled(can_edit_due_date)
        self.due_date_edit.setEnabled(can_edit_due_date and not self.no_due_date_check.isChecked())

    @Permissions.require_permission('purchase.update')
    def update_purchase_due_date(self):
        if not self.current_purchase_id:
            AppMessageBox.warning(self, "No Purchase", "Please open a purchase invoice first.")
            return

        if not (self.current_remaining > 0 and self.current_writeoff <= 0):
            AppMessageBox.information(
                self,
                "Due Date Not Applicable",
                "Due date can be updated only when purchase has remaining payable and is not written off."
            )
            return

        due_date_value = None if self.no_due_date_check.isChecked() else self.due_date_edit.date().toString("yyyy-MM-dd")

        query = QSqlQuery()
        query.prepare("UPDATE purchase SET due_date = ? WHERE id = ?")
        query.addBindValue(due_date_value)
        query.addBindValue(self.current_purchase_id)

        if not query.exec():
            AppMessageBox.critical(self, "Database Error", f"Could not update due date: {query.lastError().text()}")
            return

        self.due_date_data.setText(due_date_value if due_date_value else "No Due Date")
        AppMessageBox.information(self, "Success", "Purchase due date updated successfully.")


        




    def load_items_into_table(self, id):
        
        print("Loading items into table")
        
        query = QSqlQuery()
        self.table.setRowCount(0)  # Clear existing rows

        row = 0

        query.prepare("""
            SELECT
                product,
                qty,
                bonus,
                rate,
                discount,
                tax,
                total
            FROM purchaseitem
            WHERE purchase = ?
        """)
        query.addBindValue(id)

        query_ok = query.exec()

        if not query_ok:
            print("Current purchase item schema query failed, trying legacy columns:", query.lastError().text())
            query = QSqlQuery()
            query.prepare("""
                SELECT
                    medicine,
                    qty,
                    bonus,
                    unitcost,
                    discount,
                    tax,
                    totalcost
                FROM purchaseitem
                WHERE purchase = ?
            """)
            query.addBindValue(id)
            query_ok = query.exec()

        if query_ok:
            
            print("Loading items into table")
            
            while query.next():
                
                self.table.insertRow(row)
                
                med_value = query.value(0)
                med = int(med_value) if med_value not in (None, "") else None
                quantity = str(query.value(1))
                bonus = str(query.value(2))
                rate = str(query.value(3))
                
                print("Product is: ", med)
                
                discount = str(query.value(4))
                tax = str(query.value(5))
                
                total = str(query.value(6))
                
                name_text = "-"
                maker_text = "-"

                if med is not None:
                    query2 = QSqlQuery()
                    query2.prepare("SELECT display_name, brand FROM product WHERE id = ?")
                    query2.addBindValue(med)
                    
                    if query2.exec() and query2.next():
                        name_text = str(query2.value(0) or "-")
                        maker_text = str(query2.value(1) or "-")

                name = QTableWidgetItem(name_text)
                maker = QTableWidgetItem(maker_text)
                quantity = QTableWidgetItem(quantity)
                bonus = QTableWidgetItem(bonus)
                rate = QTableWidgetItem(rate)
                discount = QTableWidgetItem(discount)
                tax = QTableWidgetItem(tax)
                total = QTableWidgetItem(total)
                
                self.table.setItem(row, 0, name)
                self.table.setItem(row, 1, maker)
                self.table.setItem(row, 2, quantity)
                self.table.setItem(row, 3, bonus)
                self.table.setItem(row, 4, rate)
                self.table.setItem(row, 5, discount)
                self.table.setItem(row, 6, tax)
                self.table.setItem(row, 7, total)
                

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


            
        



