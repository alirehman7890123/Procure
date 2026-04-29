from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel, QFrame, QSizePolicy, QMessageBox, QHBoxLayout, QComboBox, QDialog
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from PySide6.QtSql import QSqlDatabase
import traceback
from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from services.customer_service import (
    create_customer,
    create_discount_group,
    create_tax_group,
    fetch_discount_group_options,
    fetch_tax_group_options,
    validate_customer_payload,
)



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
        for option in fetch_discount_group_options():
            self.discount_group_combo.addItem(option["label"], option["id"])
        if selected_id is not None:
            index = self.discount_group_combo.findData(selected_id)
            if index >= 0:
                self.discount_group_combo.setCurrentIndex(index)
        self.discount_group_combo.blockSignals(False)

    def populate_tax_groups(self, selected_id=None):
        self.tax_group_combo.blockSignals(True)
        self.tax_group_combo.clear()
        self.tax_group_combo.addItem("None", None)
        for option in fetch_tax_group_options():
            self.tax_group_combo.addItem(option["label"], option["id"])
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
            validate_customer_payload(
                name=self.editname.text(),
                contact=self.editcontact.text(),
                email=self.editemail.text(),
                payable=self.editpayable.text(),
                receiveable=self.editreceiveable.text(),
                credit_limit=self.editcreditlimit.text(),
            )
            customer_id = create_customer(
                name=self.editname.text(),
                contact=self.editcontact.text(),
                email=self.editemail.text(),
                payable=self.editpayable.text(),
                receiveable=self.editreceiveable.text(),
                credit_limit=self.editcreditlimit.text(),
                discount_group_id=self.discount_group_combo.currentData(),
                tax_group_id=self.tax_group_combo.currentData(),
            )
        except ValueError as e:
            db.rollback()
            AppMessageBox.warning(self, "Validation Error", str(e))
            return
        
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
        
        
        
        
