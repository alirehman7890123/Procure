from PySide6.QtWidgets import QWidget, QSizePolicy, QPushButton, QLabel, QHBoxLayout, QFrame, QHeaderView, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, QDateEdit, QCheckBox, QMessageBox
from PySide6.QtCore import QFile, Qt, QDate, QDateTime

from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.services.purchase_transaction_service import (
    fetch_purchase_detail,
    fetch_purchase_item_rows,
    update_purchase_due_date,
)





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

        self.table.setMinimumWidth(700)
        
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
        purchase_data = fetch_purchase_detail(id)
        if purchase_data is None:
            self.supplier_data.setText("Purchase not found.")
            return

        orderid = purchase_data["purchase_id"]
        sellerinvoice = purchase_data["sellerinvoice"]
        invoicedate = purchase_data["creation_date"]
        subtotal = purchase_data["subtotal"]
        discount = purchase_data["discount"]
        tax_236g = purchase_data["tax_236g"]
        tax_236h = purchase_data["tax_236h"]
        sales_tax = purchase_data["sales_tax"]
        net_amount = purchase_data["netamount"]
        cn_adjustment = purchase_data["cn_adjustment"]
        total = purchase_data["total"]
        paid = purchase_data["paid"]
        remaining = purchase_data["remaining"]
        writeoff = purchase_data["writeoff"]
        due_date = purchase_data["due_date"]

        joining_date = invoicedate
        if isinstance(joining_date, QDateTime):
            joining_date = joining_date.date().toString("dd-MM-yyyy")
        elif isinstance(joining_date, QDate):
            joining_date = joining_date.toString("dd-MM-yyyy")
        else:
            joining_date = str(joining_date)

        self.invoice_data.setText(str(orderid))
        self.sellerinvoice_data.setText(str(sellerinvoice))
        self.orderdate_data.setText(str(joining_date))
        self.supplier_data.setText(str(purchase_data["supplier_name"] or "-"))
        self.rep_data.setText(str(purchase_data["rep_name"] or "-"))

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
        self.load_items_into_table(orderid)

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

        try:
            update_purchase_due_date(self.current_purchase_id, due_date_value)
        except Exception as exc:
            AppMessageBox.critical(self, "Database Error", str(exc))
            return

        self.due_date_data.setText(due_date_value if due_date_value else "No Due Date")
        AppMessageBox.information(self, "Success", "Purchase due date updated successfully.")


        




    def load_items_into_table(self, id):
        self.table.setRowCount(0)  # Clear existing rows
        rows = fetch_purchase_item_rows(id)
        for row, row_data in enumerate(rows):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(row_data["product_name"]))
            self.table.setItem(row, 1, QTableWidgetItem(row_data["brand_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(row_data["qty"]))
            self.table.setItem(row, 3, QTableWidgetItem(row_data["bonus"]))
            self.table.setItem(row, 4, QTableWidgetItem(row_data["rate"]))
            self.table.setItem(row, 5, QTableWidgetItem(row_data["discount"]))
            self.table.setItem(row, 6, QTableWidgetItem(row_data["tax"]))
            self.table.setItem(row, 7, QTableWidgetItem(row_data["total"]))
            
            





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


            
        
