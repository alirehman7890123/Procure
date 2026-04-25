from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel, QFrame, QSizePolicy, QMessageBox, QHBoxLayout, QComboBox, QDialog
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
import traceback
from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox



def load_stylesheet(filename):
    """ Load and return the CSS stylesheet from a file. """
    file = QFile(filename)
    if not file.open(QFile.ReadOnly | QFile.Text):
        print(f"Error opening file: {filename}")
        return ""
    
    css = file.readAll().data().decode()
    file.close()
    return css




class AddCustomerWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Customer Information", objectName="SectionTitle")
        self.customerlist = QPushButton("Customers List", objectName="TopRightButton")
        self.customerlist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.customerlist)

        self.layout.addLayout(header_layout)
        line = self.horizontal_line()
        
        self.layout.addWidget(line)
        
        self.layout.addSpacing(8)
        
        
        
        
        
        
        
        
        
        # Labels + Fields
        labels = ["Customer *", "Contact", "Email", "Receivable", "Payable", "Credit Limit"]
        self.editname = QLineEdit()
        self.editcontact = QLineEdit()
        self.editemail = QLineEdit()
        self.editreceiveable = QLineEdit()
        self.editpayable = QLineEdit()
        self.editcreditlimit = QLineEdit()
        self.save_button = QPushButton("Save Customer", objectName="SaveButton")
        fields = [
            self.editname, self.editcontact, self.editemail,
            self.editreceiveable, self.editpayable, self.editcreditlimit
        ]
        
        self.indicators = {}

        for (label, field) in zip(labels, fields):

            row = QHBoxLayout()
            
            # Left line indicator
            indicator = QFrame()
            indicator.setFixedWidth(4)
            indicator.setStyleSheet("background-color: #ccc; border: none;")
            

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(indicator) 
            row.addWidget(lbl, 1)
            row.addWidget(field, 8)

            self.layout.addLayout(row)
            
            # Keep mapping
            self.indicators[field] = indicator

            # Install event filters to track focus
            field.installEventFilter(self)

        self.discount_group_combo = QComboBox()
        self.tax_group_combo = QComboBox()
        self.populate_discount_groups()
        self.populate_tax_groups()

        for field in (self.editreceiveable, self.editpayable, self.editcreditlimit):
            field.setText("0.00")

        self.layout.addLayout(self.create_group_assignment_row("Discount Group", self.discount_group_combo, self.open_discount_group_dialog))
        self.layout.addLayout(self.create_group_assignment_row("Tax Group", self.tax_group_combo, self.open_tax_group_dialog))
            
            
        self.layout.addSpacing(10)

        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(lambda: self.save_customer())

        self.layout.addWidget(self.save_button)
        self.layout.addStretch()

        self.configure_focus_flow()

        self.setStyleSheet(load_stylesheets())




    def insert_customer(self, name, contact, email, payable, receiveable, credit_limit):
        
        valid, message, cleaned = self.validate_customer(name, contact, email, payable, receiveable, credit_limit)

        if valid:
            
            print(f"[VALIDATION SUCCESS] {message}")
            
            name, contact, email, payable, receiveable, credit_limit = cleaned

            try:
                query = QSqlQuery()
                query.prepare("""
                    INSERT INTO customer (name, contact, email, payable, receiveable, credit_limit, discount_group_id, tax_group_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """)
                query.addBindValue(name)
                query.addBindValue(contact if contact else None)
                query.addBindValue(email)
                query.addBindValue(payable)
                query.addBindValue(receiveable)
                query.addBindValue(credit_limit)
                query.addBindValue(self.discount_group_combo.currentData())
                query.addBindValue(self.tax_group_combo.currentData())

                if not query.exec():
                    error_msg = query.lastError().text()
                    print(f"[DB ERROR] Failed to insert customer.\n"
                        f"Table: customer\n"
                        f"Values: name={name}, contact={contact}, email={email}, "
                        f"payable={payable}, receiveable={receiveable}, credit_limit={credit_limit}\n"
                        f"Reason: {error_msg}")
                    return False

                # return Id if insertion is successful
                return query.lastInsertId()
            

            except Exception as e:
                print(f"[PYTHON ERROR] Exception occurred while inserting customer.\n"
                    f"Function: insert_customer\n"
                    f"Values: name={name}, contact={contact}, email={email}, "
                    f"payable={payable}, receiveable={receiveable}, credit_limit={credit_limit}\n"
                    f"Exception Type: {type(e).__name__}\n"
                    f"Message: {e}")
                return False
            
        
        else:
            
            print(f"[VALIDATION ERROR] {message}")
            AppMessageBox.warning(self, "Validation Error", message)
            return False


    def validate_customer(self, name, contact, email, payable, receiveable, credit_limit):
        
        name = name.strip()
        contact = contact.strip()
        email = email.strip()
        payable = payable.strip()
        receiveable = receiveable.strip()
        credit_limit = credit_limit.strip()
        
        if not name or not name.strip():
            return False, "Customer name cannot be empty.", ""

        if any(char.isdigit() for char in name):
            return False, "Customer name cannot contain numbers.", ""

        if contact and not contact.isdigit():
            return False, "Contact must contain only digits.", ""

        if email and ("@" not in email or "." not in email):
            return False, "Invalid email format.", ""

        try:
            payable_val = float(payable) if payable else 0.0
            receiveable_val = float(receiveable) if receiveable else 0.0
            credit_limit_val = float(credit_limit) if credit_limit else 0.0
        except ValueError:
            return False, "Payable, Receivable, and Credit Limit must be numbers.", ""

        if payable_val < 0 or receiveable_val < 0 or credit_limit_val < 0:
            return False, "Payable, Receivable, and Credit Limit cannot be negative.", ""

        return True, "Customer details are valid.", (name, contact, email, payable_val, receiveable_val, credit_limit_val)
    
    


    def horizontal_line(self):
        
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

        return line

    def create_group_assignment_row(self, label_text, combo, add_handler):
        row = QHBoxLayout()
        indicator = QFrame()
        indicator.setFixedWidth(4)
        indicator.setStyleSheet("background-color: #ccc; border: none;")
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setMinimumWidth(200)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(add_handler)

        row.addWidget(indicator)
        row.addWidget(label, 1)
        row.addWidget(combo, 8)
        row.addWidget(add_btn)
        return row

    def configure_focus_flow(self):
        self.editname.returnPressed.connect(lambda: self.focus_field(self.editcontact))
        self.editcontact.returnPressed.connect(lambda: self.focus_field(self.editemail))
        self.editemail.returnPressed.connect(lambda: self.focus_field(self.editreceiveable))
        self.editreceiveable.returnPressed.connect(lambda: self.focus_field(self.editpayable))
        self.editpayable.returnPressed.connect(lambda: self.focus_field(self.editcreditlimit))
        self.editcreditlimit.returnPressed.connect(lambda: self.focus_field(self.save_button))

    def focus_field(self, widget):
        widget.setFocus()
        if hasattr(widget, "selectAll"):
            widget.selectAll()

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
        if selected_id is not None:
            index = self.discount_group_combo.findData(selected_id)
            if index >= 0:
                self.discount_group_combo.setCurrentIndex(index)
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
        if selected_id is not None:
            index = self.tax_group_combo.findData(selected_id)
            if index >= 0:
                self.tax_group_combo.setCurrentIndex(index)
        self.tax_group_combo.blockSignals(False)

    def open_discount_group_dialog(self):
        self.open_group_dialog(
            title="Add Discount Group",
            name_label="Discount Group Name",
            value_label="Discount Percent",
            table_name="discount_group",
            value_column="discount_percent",
            refresh=self.populate_discount_groups,
        )

    def open_tax_group_dialog(self):
        self.open_group_dialog(
            title="Add Tax Group",
            name_label="Tax Group Name",
            value_label="Tax Percent",
            table_name="tax_group",
            value_column="tax_percent",
            refresh=self.populate_tax_groups,
        )

    def open_group_dialog(self, title, name_label, value_label, table_name, value_column, refresh):
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
            dialog.accept()

        save_btn.clicked.connect(save_group)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()


    def eventFilter(self, obj, event):
    
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #2F5D7C; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)
    
    
    

    @Permissions.require_permission('customer.create')
    def save_customer(self):
        
        print("[ACTION] Save Customer button clicked.")
        
        db = QSqlDatabase.database()
        db.transaction()
        
        try:
        
            customer_id = self.insert_customer(
                self.editname.text(),
                self.editcontact.text(),
                self.editemail.text(),
                self.editpayable.text(),
                self.editreceiveable.text(),
                self.editcreditlimit.text()
            )
            
        
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Exception occurred while saving customer and related info.\n"
                f"Exception Type: {type(e).__name__}\n"
                f"Message: {e}\n"
                f"Traceback: {traceback.format_exc()}")
            AppMessageBox.critical(self, "Error", "An error occurred while saving customer information.")
            return

        else:
            if not customer_id:
                db.rollback()
                return
            db.commit()
            print("[DB] Transaction committed successfully.")
            self.clear_fields()
            AppMessageBox.success(self, "Success", "Customer saved successfully.")
            self.editname.setFocus()




    def clear_fields(self):
        
        self.editname.clear()
        self.editcontact.clear()
        self.editemail.clear()
        self.editpayable.setText("0.00")
        self.editreceiveable.setText("0.00")
        self.editcreditlimit.setText("0.00")
        self.discount_group_combo.setCurrentIndex(0)
        self.tax_group_combo.setCurrentIndex(0)
        
        print("[ACTION] All input fields cleared.")
        
        
        
        
