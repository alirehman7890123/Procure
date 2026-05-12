
from PySide6.QtWidgets import (
    QWidget, QPushButton, QMessageBox, QGridLayout, QLabel, 
    QSpacerItem, QSizePolicy, QLineEdit, QVBoxLayout, QHBoxLayout, QFrame
)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import QFile, Qt, QEvent
from PySide6.QtGui import QFocusEvent
import traceback


from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions

from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from medic.services.supplier_service import save_supplier_record, validate_supplier_payload




class AddSupplierWidget(BasePage):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Supplier Information", objectName="SectionTitle")
        self.supplierlist = QPushButton("Suppliers List", objectName="TopRightButton")
        self.supplierlist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.supplierlist)

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
        self.layout.addSpacing(10)

        # Labels + Fields
        labels = ["Supplier", "Contact", "Email", "Website", "Address", "Registration No.", "Payable", "Receivable"]
        self.editname = QLineEdit()
        self.editcontact = QLineEdit()
        self.editemail = QLineEdit()
        self.editwebsite = QLineEdit()
        self.editaddress = QLineEdit()
        self.editreg_no = QLineEdit()
        self.editpayable = QLineEdit()
        self.editreceiveable = QLineEdit()
        self.save_button = QPushButton("Add Supplier", objectName="SaveButton")

        fields = [
            self.editname, self.editcontact, self.editemail, self.editwebsite,
            self.editaddress, self.editreg_no, self.editpayable, self.editreceiveable
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
            
        for field in (self.editpayable, self.editreceiveable):
            field.setText("0.00")

        self.layout.addSpacing(8)
        
        
          
                
        

        # === Add Button ===
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(lambda: self.save_supplier())
        
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.save_supplier)

        self.layout.addWidget(self.save_button)
        self.layout.addStretch()

        self.configure_focus_flow()
        

        # Apply external stylesheet if present
        
        self.setStyleSheet(load_stylesheets())

    def configure_focus_flow(self):
        self.editname.returnPressed.connect(lambda: self.focus_field(self.editcontact))
        self.editcontact.returnPressed.connect(lambda: self.focus_field(self.editemail))
        self.editemail.returnPressed.connect(lambda: self.focus_field(self.editwebsite))
        self.editwebsite.returnPressed.connect(lambda: self.focus_field(self.editaddress))
        self.editaddress.returnPressed.connect(lambda: self.focus_field(self.editreg_no))
        self.editreg_no.returnPressed.connect(lambda: self.focus_field(self.editpayable))
        self.editpayable.returnPressed.connect(lambda: self.focus_field(self.editreceiveable))
        self.editreceiveable.returnPressed.connect(lambda: self.focus_field(self.save_button))

    def focus_field(self, widget):
        widget.setFocus()
        if hasattr(widget, "selectAll"):
            widget.selectAll()
        
        
        
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

        
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #5A9EC9; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)


    
    
    @Permissions.require_permission('supplier.create')
    def save_supplier(self):

        print("[ACTION] Save Supplier button clicked.")
        
        try:
            validate_supplier_payload(
                name=self.editname.text(),
                contact=self.editcontact.text(),
                email=self.editemail.text(),
                website=self.editwebsite.text(),
                address=self.editaddress.text(),
                registeration=self.editreg_no.text(),
                payable=self.editpayable.text(),
                receiveable=self.editreceiveable.text(),
            )
            supplier_id = save_supplier_record(
                name=self.editname.text(),
                contact=self.editcontact.text(),
                email=self.editemail.text(),
                website=self.editwebsite.text(),
                address=self.editaddress.text(),
                registeration=self.editreg_no.text(),
                payable=self.editpayable.text(),
                receiveable=self.editreceiveable.text(),
            )
        except ValueError as e:
            AppMessageBox.warning(self, "Validation Error", str(e))
            return

        
        except Exception as e:
            print(f"[ERROR] Exception occurred while saving supplier and related info.\n"
                f"Exception Type: {type(e).__name__}\n"
                f"Message: {e}\n"
                f"Traceback: {traceback.format_exc()}")
            AppMessageBox.critical(self, "Error", "An error occurred while saving supplier information.")
            return

        else:
            if not supplier_id:
                return
            print("[DB] Transaction committed successfully.")
            self.clear_fields()
            AppMessageBox.success(self, "Success", "Supplier saved successfully.")
            self.editname.setFocus()


    
    
    

    def clear_fields(self):
        for field in [
            self.editname, self.editcontact, self.editemail,
            self.editwebsite, self.editaddress, self.editreg_no
        ]:
            field.clear()
        self.editpayable.setText("0.00")
        self.editreceiveable.setText("0.00")
