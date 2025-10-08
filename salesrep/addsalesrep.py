from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QFrame, QSizePolicy, QComboBox, QMessageBox
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from utilities.stylus import load_stylesheets




class AddSalesRepWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        
    
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)


        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Sales Rep Information", objectName="SectionTitle")
        self.replist = QPushButton("Rep List", objectName="TopRightButton")
        self.replist.setCursor(Qt.PointingHandCursor)
        self.replist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
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
            self.layout.setSpacing(15)  # reduce space between rows
            
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
            self.indicators[obj].setStyleSheet("background-color: #47034E; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)
    
    
    
        
    def showEvent(self, event):
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.populate_suppliers()
        


    def populate_suppliers(self):
        
        self.selectsupplier.clear()
        query = QSqlQuery()
        
        if query.exec("SELECT id, name FROM supplier WHERE status = 'active';"):
            while query.next():
                supplier_id = query.value(0)
                supplier_name = query.value(1)
                
                print(supplier_id, supplier_name)
                
                self.selectsupplier.addItem(supplier_name, supplier_id)  # Text shown, ID stored as data
            
        else:
            QMessageBox.information(None, 'Error', query.lastError().text() )
        
            
            
    
    
    def save_salesrep(self):
        
        suppliername = self.selectsupplier.currentText()
        supplierid = self.selectsupplier.currentData()
        name = self.editname.text()
        contact = self.editcontact.text()

        print("DATA is: ",suppliername)
        print("Data is: ", supplierid)
 
        
        query = QSqlQuery()
        
        query.prepare("""
                    INSERT INTO rep ( supplier_id, name, contact )
                    VALUES (?, ?, ?);
                """)
            
        query.addBindValue(supplierid)
        query.addBindValue(name)
        query.addBindValue(contact)
            
        if not query.exec():
            print("Insert failed:", query.lastError().text())
            QMessageBox.critical(None, "Error", 'query.lastError().text()')
        else:
            QMessageBox.information(None, "Success", 'Rep Record Saved Successfully')
            
            self.editname.setText("")
            self.editcontact.setText("")
            
            
            
    



