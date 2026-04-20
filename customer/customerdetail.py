from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFrame, QLabel, QLineEdit, QVBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem, QSizePolicy, QMessageBox, QComboBox, QDialog
from PySide6.QtCore import QFile, Qt, QDate, QDateTime, Signal
from PySide6.QtSql import  QSqlQuery
from utilities.stylus import load_stylesheets
from utilities.permissions import Permissions
from utilities.app_messagebox import AppMessageBox





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
        query = QSqlQuery()
        if query.exec("SELECT id, name, discount_percent, COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1) FROM discount_group WHERE status = 'active' ORDER BY name ASC"):
            while query.next():
                group_id = query.value(0)
                name = str(query.value(1) or "")
                percent = float(query.value(2) or 0.0)
                fixed_amount = float(query.value(3) or 0.0)
                apply_on_sale = bool(int(query.value(4) or 0))
                self.discount_group_combo.addItem(
                    f"{name} ({percent:.2f}% + {fixed_amount:.2f}, {'Sale On' if apply_on_sale else 'Sale Off'})",
                    group_id,
                )
        self.sync_group_selection(self.discount_group_combo, selected_id)
        self.discount_group_combo.blockSignals(False)

    def populate_tax_groups(self, selected_id=None):
        self.tax_group_combo.blockSignals(True)
        self.tax_group_combo.clear()
        self.tax_group_combo.addItem("None", None)
        query = QSqlQuery()
        if query.exec("SELECT id, name, tax_percent, COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1) FROM tax_group WHERE status = 'active' ORDER BY name ASC"):
            while query.next():
                group_id = query.value(0)
                name = str(query.value(1) or "")
                percent = float(query.value(2) or 0.0)
                fixed_amount = float(query.value(3) or 0.0)
                apply_on_sale = bool(int(query.value(4) or 0))
                self.tax_group_combo.addItem(
                    f"{name} ({percent:.2f}% + {fixed_amount:.2f}, {'Sale On' if apply_on_sale else 'Sale Off'})",
                    group_id,
                )
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
            group_name = name_edit.text().strip()
            if not group_name:
                AppMessageBox.warning(dialog, "Validation Error", "Group name is required.")
                return
            try:
                percent_value = float(percent_edit.text() or 0.0)
            except ValueError:
                AppMessageBox.warning(dialog, "Validation Error", "Percent must be a valid number.")
                return
            if percent_value < 0:
                AppMessageBox.warning(dialog, "Validation Error", "Percent cannot be negative.")
                return

            query = QSqlQuery()
            query.prepare(f"""
                INSERT INTO {table_name} (name, {value_column}, status)
                VALUES (?, ?, 'active')
            """)
            query.addBindValue(group_name)
            query.addBindValue(percent_value)
            if not query.exec():
                AppMessageBox.critical(dialog, "Database Error", query.lastError().text())
                return

            new_id = query.lastInsertId()
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
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
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
            self.save_changes()
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
            return

        try:
            credit_limit = float(self.creditlimitedit.text() or 0.0)
        except ValueError:
            AppMessageBox.warning(self, "Validation Error", "Credit Limit must be a valid number.")
            return

        if credit_limit < 0:
            AppMessageBox.warning(self, "Validation Error", "Credit Limit cannot be negative.")
            return

        query = QSqlQuery()
        query.prepare("""
            UPDATE customer
            SET name=?, contact=?, email=?, status=?, credit_limit=?, discount_group_id=?, tax_group_id=?
            WHERE id=?
        """)
        
        query.addBindValue(self.nameedit.text())
        query.addBindValue(self.contactedit.text())
        query.addBindValue(self.emailedit.text())
        query.addBindValue(self.statusedit.text())
        query.addBindValue(credit_limit)
        query.addBindValue(self.discount_group_combo.currentData())
        query.addBindValue(self.tax_group_combo.currentData())
        query.addBindValue(self.customer_id)

        if not query.exec():
            print("Error updating customer:", query.lastError().text())
        else:
            self.discount_group_data.setText(self.discount_group_combo.currentText() or "None")
            self.tax_group_data.setText(self.tax_group_combo.currentText() or "None")
            print("Customer updated successfully.")
            

            

    def load_customer_transactions(self, customer_id):
        
        self.customer_id = customer_id
        print("Loading customer ID:", self.customer_id)
        self.customer_id = int(self.customer_id)
        customer_query = QSqlQuery()
        customer_query.prepare(
            """
            SELECT
                name,
                contact,
                email,
                status,
                creation_date,
                payable,
                receiveable,
                credit_limit,
                discount_group_id,
                tax_group_id
            FROM customer
            WHERE id = ?
            """
        )
        customer_query.addBindValue(self.customer_id)
        
        if customer_query.exec() and customer_query.next():
            
            self.namedata.setText(str(customer_query.value(0) or "-"))
            self.contactdata.setText(str(customer_query.value(1) or "-"))
            self.emaildata.setText(str(customer_query.value(2) or "-"))
            self.statusdata.setText(str(customer_query.value(3) or "-"))
            joining_date = customer_query.value(4)
            
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)
                
            self.joiningdata.setText(joining_date)
            self.payabledata.setText(f"{float(customer_query.value(5) or 0):.2f}")
            self.receiveabledata.setText(f"{float(customer_query.value(6) or 0):.2f}")
            self.creditlimitdata.setText(f"{float(customer_query.value(7) or 0):.2f}")
            discount_group_id = customer_query.value(8)
            tax_group_id = customer_query.value(9)
            self.sync_group_selection(self.discount_group_combo, discount_group_id)
            self.sync_group_selection(self.tax_group_combo, tax_group_id)
            self.discount_group_data.setText(self.discount_group_combo.currentText() or "None")
            self.tax_group_data.setText(self.tax_group_combo.currentText() or "None")
            
            
           
        print("Loading Customer Transaction")
        query = QSqlQuery()
        query.prepare("""SELECT 
                                creation_date,                                
                                transaction_type, 
                                receiveable_now,
                                payable_before,
                                receiveable_before,
                                paid,
                                received,
                                payable_after,
                                receiveable_after,
                                payment_method,
                                id
                                FROM customer_transaction 
                                WHERE customer = ?
                                ORDER BY creation_date DESC
                      
                      """)
        query.addBindValue(self.customer_id)
        
        
        if not query.exec():
            
            print("Error executing query:", query.lastError().text())
            return
        
        else:
            self.table.setRowCount(0)  # Clear existing rows
            row = 0
            
            while query.next():
                
                self.table.insertRow(row)
                
                
                creation_date = query.value(0)
                transaction_type = str(query.value(1))
                payment_type = str(query.value(9) or "-")
                total_now = float(query.value(2) or 0)
                payable_before = float(query.value(3) or 0)
                receiveable_before = float(query.value(4) or 0)
                paid = float(query.value(5) or 0)
                received = float(query.value(6) or 0)
                payable_after = float(query.value(7) or 0)
                receiveable_after = float(query.value(8) or 0)
                transaction_id = int(query.value(10))

               
                
                date_item = QTableWidgetItem(str(creation_date))
                transaction_type = QTableWidgetItem(transaction_type)
                payment_type = QTableWidgetItem(payment_type)
                total_now = QTableWidgetItem(f"{total_now:.2f}")
                payable_before = QTableWidgetItem(f"{payable_before:.2f}")
                receiveable_before = QTableWidgetItem(f"{receiveable_before:.2f}")
                
                paid = QTableWidgetItem(f"{paid:.2f}")
                received = QTableWidgetItem(f"{received:.2f}")
                payable_after = QTableWidgetItem(f"{payable_after:.2f}")
                receiveable_after = QTableWidgetItem(f"{receiveable_after:.2f}")
                

                # Add items to table
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



        

            
            
            
