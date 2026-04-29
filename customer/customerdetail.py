from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFrame, QLabel, QLineEdit, QVBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem, QSizePolicy, QMessageBox, QComboBox, QDialog
from PySide6.QtCore import QFile, Qt, QDate, QDateTime, Signal
from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from services.customer_service import (
    create_discount_group,
    create_tax_group,
    fetch_customer_detail,
    fetch_customer_transaction_rows,
    fetch_discount_group_options,
    fetch_tax_group_options,
    update_customer,
)





class CustomerDetailWidget(QWidget):
    
    transaction_detail_signal = Signal(int)

    def __init__(self, parent=None):

        super().__init__(parent)
        
        self.customer_id = None
        self.edit_mode = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Customer Detail", objectName="SectionTitle")
        self.customerlist = QPushButton("Customer List", objectName="TopRightButton")
        self.customerlist.setCursor(Qt.PointingHandCursor)
        
        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.customerlist)

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
        
        info_frame = QFrame()
        info_frame.setObjectName("sectionCard")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(8)

        labels = ["Customer", "Contact", "Email", "Status", "Joining Date", "Payable", "Receivable", "Credit Limit"]

        self.namedata = QLabel() ; self.nameedit = QLineEdit()
        self.contactdata = QLabel() ; self.contactedit = QLineEdit()
        self.emaildata = QLabel() ; self.emailedit = QLineEdit()    
        self.statusdata = QLabel() ; self.statusedit = QLineEdit()
        self.joiningdata = QLabel()
        self.payabledata = QLabel()
        self.receiveabledata = QLabel()
        self.creditlimitdata = QLabel() ; self.creditlimitedit = QLineEdit()
        

        self.field_pairs = [
            (self.namedata, self.nameedit),
            (self.contactdata, self.contactedit),
            (self.emaildata, self.emailedit),
            (self.statusdata, self.statusedit),
            (self.joiningdata, None),
            (self.payabledata, None),
            (self.receiveabledata, None),
            (self.creditlimitdata, self.creditlimitedit),
            
            
        ]

        for (label, (lbl_field, edit_field)) in zip(labels, self.field_pairs):

            row = QHBoxLayout()
            
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            
            lbl_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(lbl, 2)
            row.addWidget(lbl_field, 8)
            
            if edit_field:  # hidden initially
                edit_field.hide()
                row.addWidget(edit_field, 8)

            info_layout.addLayout(row)

        self.discount_group_data = QLabel()
        self.discount_group_combo = QComboBox()
        self.discount_group_add_btn = QPushButton("+")
        self.discount_group_add_btn.setFixedSize(28, 28)
        self.discount_group_add_btn.clicked.connect(self.open_discount_group_dialog)
        self.populate_discount_groups()
        info_layout.addLayout(
            self.create_group_row("Discount Group", self.discount_group_data, self.discount_group_combo, self.discount_group_add_btn)
        )

        self.tax_group_data = QLabel()
        self.tax_group_combo = QComboBox()
        self.tax_group_add_btn = QPushButton("+")
        self.tax_group_add_btn.setFixedSize(28, 28)
        self.tax_group_add_btn.clicked.connect(self.open_tax_group_dialog)
        self.populate_tax_groups()
        info_layout.addLayout(
            self.create_group_row("Tax Group", self.tax_group_data, self.tax_group_combo, self.tax_group_add_btn)
        )
        
        self.layout.addWidget(info_frame)

        history_heading = QLabel("Transaction History", objectName="SectionTitle")
        self.layout.addWidget(history_heading)
        
        
        # Create Customer History Table
        
        self.row_height = 40

        self.table = MyTable(column_ratios=[0.13, 0.17, 0.12, 0.10, 0.10, 0.10, 0.09, 0.09, 0.10, 0.10])
        headers = [
            "Date",
            "Transaction Type",
            "Payment Type",
            "Due / Credit",
            "Payable Before",
            "Receivable Before",
            "Paid",
            "Received",
            "Payable After",
            "Receivable After",
        ]
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
        
        
        

        self.setStyleSheet(load_stylesheets())
        
    def create_group_row(self, label_text, data_label, combo, add_btn):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        label.setStyleSheet("font-weight: normal; color: #444;")
        label.setMinimumWidth(200)

        combo.hide()
        add_btn.hide()

        data_label.setWordWrap(True)
        row.addWidget(label, 2)
        row.addWidget(data_label, 8)
        row.addWidget(combo, 8)
        row.addWidget(add_btn)
        return row

    def populate_discount_groups(self, selected_id=None):
        self.discount_group_combo.blockSignals(True)
        self.discount_group_combo.clear()
        self.discount_group_combo.addItem("None", None)
        for option in fetch_discount_group_options():
            self.discount_group_combo.addItem(option["label"], option["id"])
        self.sync_group_selection(self.discount_group_combo, selected_id)
        self.discount_group_combo.blockSignals(False)

    def populate_tax_groups(self, selected_id=None):
        self.tax_group_combo.blockSignals(True)
        self.tax_group_combo.clear()
        self.tax_group_combo.addItem("None", None)
        for option in fetch_tax_group_options():
            self.tax_group_combo.addItem(option["label"], option["id"])
        self.sync_group_selection(self.tax_group_combo, selected_id)
        self.tax_group_combo.blockSignals(False)

    def sync_group_selection(self, combo, selected_id):
        index = combo.findData(selected_id)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def open_discount_group_dialog(self):
        self.open_group_dialog(
            title="Add Discount Group",
            name_label="Discount Group Name",
            value_label="Discount Percent",
            table_name="discount_group",
            value_column="discount_percent",
            refresh=self.populate_discount_groups,
            combo=self.discount_group_combo,
        )

    def open_tax_group_dialog(self):
        self.open_group_dialog(
            title="Add Tax Group",
            name_label="Tax Group Name",
            value_label="Tax Percent",
            table_name="tax_group",
            value_column="tax_percent",
            refresh=self.populate_tax_groups,
            combo=self.tax_group_combo,
        )

    def open_group_dialog(self, title, name_label, value_label, table_name, value_column, refresh, combo):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(360)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        name_edit = QLineEdit()
        percent_edit = QLineEdit()
        percent_edit.setPlaceholderText("0.00")

        layout.addWidget(QLabel(name_label))
        layout.addWidget(name_edit)
        layout.addWidget(QLabel(value_label))
        layout.addWidget(percent_edit)

        button_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        button_row.addWidget(save_btn)
        button_row.addWidget(cancel_btn)
        layout.addLayout(button_row)

        def save_group():
            try:
                if table_name == "discount_group":
                    new_id = create_discount_group(name_edit.text(), percent_edit.text())
                else:
                    new_id = create_tax_group(name_edit.text(), percent_edit.text())
            except ValueError as exc:
                AppMessageBox.warning(dialog, "Validation Error", str(exc))
                return
            except Exception as exc:
                AppMessageBox.critical(dialog, "Database Error", str(exc))
                return

            refresh(int(new_id))
            combo.setCurrentIndex(combo.findData(int(new_id)))
            dialog.accept()

        save_btn.clicked.connect(save_group)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()
        
        
    def hideEvent(self, event):
        
        if self.edit_mode:
            
            self.edit_mode = not self.edit_mode
            # reset state, discard edits
            self.edit_btn.setText("Edit")
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(edit.text())
                    edit.hide()
                    lbl.show()
            self.discount_group_combo.hide()
            self.tax_group_combo.hide()
            self.discount_group_add_btn.hide()
            self.tax_group_add_btn.hide()
            self.discount_group_data.show()
            self.tax_group_data.show()

        super().hideEvent(event)
           
        
        
    
    # === Toggle Edit Mode ===
    @Permissions.require_permission('customer.update')
    def toggle_edit_mode(self):
        if not self.edit_mode:
            self.edit_mode = True
            self.edit_btn.setText("Save")
            # Switch to QLineEdit
            for lbl, edit in self.field_pairs:
                if edit:
                    edit.setText(lbl.text())
                    lbl.hide()
                    edit.show()
            self.discount_group_data.hide()
            self.tax_group_data.hide()
            self.discount_group_combo.show()
            self.tax_group_combo.show()
            self.discount_group_add_btn.show()
            self.tax_group_add_btn.show()
        else:
            if self.save_changes():
                self.edit_mode = False
                self.edit_btn.setText("Edit")
                # Switch back to QLabel
                for lbl, edit in self.field_pairs:
                    if edit:
                        lbl.setText(edit.text())
                        edit.hide()
                        lbl.show()
                self.discount_group_data.show()
                self.tax_group_data.show()
                self.discount_group_combo.hide()
                self.tax_group_combo.hide()
                self.discount_group_add_btn.hide()
                self.tax_group_add_btn.hide()
    
    

      
    # === Save Changes ===
    @Permissions.require_permission('customer.update')
    def save_changes(self):
        
        if not self.customer_id:
            print("No customer loaded.")
            return False

        try:
            update_customer(
                self.customer_id,
                name=self.nameedit.text(),
                contact=self.contactedit.text(),
                email=self.emailedit.text(),
                status=self.statusedit.text(),
                credit_limit=self.creditlimitedit.text(),
                discount_group_id=self.discount_group_combo.currentData(),
                tax_group_id=self.tax_group_combo.currentData(),
            )
        except ValueError as exc:
            AppMessageBox.warning(self, "Validation Error", str(exc))
            return False
        except Exception as exc:
            print("Error updating customer:", str(exc))
            AppMessageBox.critical(self, "Database Error", str(exc))
            return False
        else:
            self.discount_group_data.setText(self.discount_group_combo.currentText() or "None")
            self.tax_group_data.setText(self.tax_group_combo.currentText() or "None")
            print("Customer updated successfully.")
            return True
            

            

    def load_customer_transactions(self, customer_id):
        
        self.customer_id = customer_id
        print("Loading customer ID:", self.customer_id)
        self.customer_id = int(self.customer_id)
        customer = fetch_customer_detail(self.customer_id)
        if customer:
            self.namedata.setText(customer["name"])
            self.contactdata.setText(customer["contact"])
            self.emaildata.setText(customer["email"])
            self.statusdata.setText(customer["status"])
            joining_date = customer["creation_date"]

            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)
                
            self.joiningdata.setText(joining_date)
            self.payabledata.setText(f"{customer['payable']:.2f}")
            self.receiveabledata.setText(f"{customer['receiveable']:.2f}")
            self.creditlimitdata.setText(f"{customer['credit_limit']:.2f}")
            discount_group_id = customer["discount_group_id"]
            tax_group_id = customer["tax_group_id"]
            self.sync_group_selection(self.discount_group_combo, discount_group_id)
            self.sync_group_selection(self.tax_group_combo, tax_group_id)
            self.discount_group_data.setText(self.discount_group_combo.currentText() or "None")
            self.tax_group_data.setText(self.tax_group_combo.currentText() or "None")
            
            
           
        print("Loading Customer Transaction")
        try:
            rows = fetch_customer_transaction_rows(self.customer_id)
        except Exception as exc:
            print("Error executing query:", str(exc))
            return
        self.table.setRowCount(0)
        row = 0

        for tx_row in rows:
            self.table.insertRow(row)

            date_item = QTableWidgetItem(str(tx_row["creation_date"]))
            transaction_type = QTableWidgetItem(tx_row["transaction_type"])
            payment_type = QTableWidgetItem(tx_row["payment_method"])
            total_now = QTableWidgetItem(f"{tx_row['due_or_credit']:.2f}")
            payable_before = QTableWidgetItem(f"{tx_row['payable_before']:.2f}")
            receiveable_before = QTableWidgetItem(f"{tx_row['receiveable_before']:.2f}")
            paid = QTableWidgetItem(f"{tx_row['paid']:.2f}")
            received = QTableWidgetItem(f"{tx_row['received']:.2f}")
            payable_after = QTableWidgetItem(f"{tx_row['payable_after']:.2f}")
            receiveable_after = QTableWidgetItem(f"{tx_row['receiveable_after']:.2f}")

            self.table.setItem(row, 0, date_item)
            self.table.setItem(row, 1, transaction_type)
            self.table.setItem(row, 2, payment_type)
            self.table.setItem(row, 3, total_now)
            self.table.setItem(row, 4, payable_before)
            self.table.setItem(row, 5, receiveable_before)
            self.table.setItem(row, 6, paid)
            self.table.setItem(row, 7, received)
            self.table.setItem(row, 8, payable_after)
            self.table.setItem(row, 9, receiveable_after)

            row += 1
        
        
        
                
            



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



        

            
            
            
