from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QFrame, QSizePolicy, QComboBox, QMessageBox
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.services.salesrep_service import (
    create_salesrep,
    fetch_active_supplier_option_rows,
    validate_salesrep_payload,
)




class AddSalesRepWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        
    
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)


        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Sales Rep Information", objectName="SectionTitle")
        self.replist = QPushButton("Rep List", objectName="TopRightButton")
        self.replist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.replist)
        

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
        
        
        # Labels + Fields
        labels = ["Supplier", "Rep Name", "Contact"]
        self.selectsupplier = QComboBox()
        self.editname = QLineEdit()
        self.editcontact = QLineEdit()
        

        fields = [
            self.selectsupplier, self.editname, self.editcontact
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
            self.layout.setSpacing(10)  # reduce space between rows
            
            # Keep mapping
            self.indicators[field] = indicator

            # Install event filters to track focus
            field.installEventFilter(self)
        

        # === Add Button ===
        addrep = QPushButton("Add Sales Rep", objectName="SaveButton")
        addrep.setCursor(Qt.PointingHandCursor)
        addrep.clicked.connect(lambda: self.save_salesrep())
 
        self.layout.addWidget(addrep)
        self.layout.addStretch()


        self.setStyleSheet(load_stylesheets())
        

    
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #2F5D7C; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)
    
    
    
        
    def showEvent(self, event):
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.populate_suppliers()
        


    def populate_suppliers(self):
        self.selectsupplier.clear()
        try:
            rows = fetch_active_supplier_option_rows()
        except Exception as exc:
            AppMessageBox.information(None, "Error", str(exc))
            return

        for row in rows:
            self.selectsupplier.addItem(row["supplier_name"], row["supplier_id"])
        
            
            
    
    
    @Permissions.require_permission('rep.create')
    def save_salesrep(self):
        supplier_id = self.selectsupplier.currentData()
        name = self.editname.text()
        contact = self.editcontact.text()

        try:
            validate_salesrep_payload(
                supplier_id=supplier_id,
                name=name,
                contact=contact,
            )
            create_salesrep(
                supplier_id=supplier_id,
                name=name,
                contact=contact,
            )
        except ValueError as exc:
            AppMessageBox.warning(self, "Validation Error", str(exc))
            return
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))
            return

        AppMessageBox.information(None, "Success", "Rep Record Saved Successfully")
        self.editname.setText("")
        self.editcontact.setText("")
            
            
            
    

