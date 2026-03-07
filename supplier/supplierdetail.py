            
from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QHeaderView, QTableWidget, QTableWidgetItem, QSpacerItem,
    QLineEdit, QSizePolicy, QApplication, QMessageBox
)
from PySide6.QtCore import QFile, Qt, QDate, QDateTime
from PySide6.QtSql import QSqlQuery
from utilities.stylus import load_stylesheets


class SupplierDetailWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.supplier_id = None
        self.edit_mode = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Supplier Detail", objectName="SectionTitle")
        self.supplierlist = QPushButton("Suppliers List", objectName="TopRightButton")
        self.supplierlist.setCursor(Qt.PointingHandCursor)
        self.supplierlist.setFixedWidth(200)

        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedWidth(100)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)

        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.supplierlist)

        self.layout.addLayout(header_layout)

        # === Separator ===
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

        # === Labels + Fields ===
        labels = [
            "Supplier", "Contact", "Email", "Website", "Address",
            "Registration No.", "Status", "Joining Date",
            "Payable", "Receivable",
            
                  
        ]

        # Use QLabel for display, QLineEdit for editing
        self.namedata = QLabel(); self.nameedit = QLineEdit()
        self.contactdata = QLabel(); self.contactedit = QLineEdit()
        self.emaildata = QLabel(); self.emailedit = QLineEdit()
        self.websitedata = QLabel(); self.websiteedit = QLineEdit()
        self.addressdata = QLabel(); self.addressedit = QLineEdit()
        self.regdata = QLabel(); self.regedit = QLineEdit()
        self.statusdata = QLabel(); self.statusedit = QLineEdit()
        self.joiningdata = QLabel(); # keep readonly
        self.payabledata = QLabel()   # keep readonly
        self.receiveabledata = QLabel()  # keep readonly
        

        self.field_pairs = [
            
            (self.namedata, self.nameedit),
            (self.contactdata, self.contactedit),
            (self.emaildata, self.emailedit),
            (self.websitedata, self.websiteedit),
            (self.addressdata, self.addressedit),
            (self.regdata, self.regedit),
            (self.statusdata, self.statusedit),
            (self.joiningdata, None),
            (self.payabledata, None),
            (self.receiveabledata, None),
            
        ]

        for (label, (lbl_field, edit_field)) in zip(labels, self.field_pairs):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            lbl.setMinimumWidth(200)

            lbl_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            row.addWidget(lbl, 2)
            row.addWidget(lbl_field, 8)

            if edit_field:  # hidden initially
                edit_field.hide()
                row.addWidget(edit_field, 8)

            self.layout.addLayout(row)

        self.layout.addStretch()

        
        self.setStyleSheet(load_stylesheets())
        
        
        
        
        

    # === Toggle Edit Mode ===
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
        else:
            self.save_changes()
            self.edit_btn.setText("Edit")
            # Switch back to QLabel
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(edit.text())
                    edit.hide()
                    lbl.show()


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

        super().hideEvent(event)


    # === Save Changes ===
    def save_changes(self):
        
        if not self.supplier_id:
            print("No supplier loaded.")
            return

        query = QSqlQuery()
        query.prepare("""
            UPDATE supplier
            SET name=?, contact=?, email=?, website=?, address=?, status=?, reg_no=?
            WHERE id=?
        """)
        
        registeration = self.regedit.text()

        registeration = registeration if registeration.strip() else None
        
        
        
        
        query.addBindValue(self.nameedit.text())
        query.addBindValue(self.contactedit.text())
        query.addBindValue(self.emailedit.text())
        query.addBindValue(self.websiteedit.text())
        query.addBindValue(self.addressedit.text())
        query.addBindValue(self.statusedit.text())
        query.addBindValue(registeration)
        query.addBindValue(self.supplier_id)

        if not query.exec():
            print("Error updating supplier:", query.lastError().text())
        else:
            print("Supplier updated successfully.")
        
        
            

    # === Load Data ===
    def load_supplier_data(self, id):
        self.supplier_id = id
        query = QSqlQuery()
        query.prepare("SELECT * FROM supplier WHERE id = ?")
        query.addBindValue(id)

        if query.exec() and query.next():
            self.namedata.setText(query.value(1))
            self.contactdata.setText(query.value(2))
            self.emaildata.setText(query.value(3))
            self.websitedata.setText(query.value(4))
            self.addressdata.setText(query.value(5))
            self.statusdata.setText(query.value(6))

            joining_date = query.value(7)
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)

            self.joiningdata.setText(joining_date)
            self.regdata.setText(query.value(8))
            self.payabledata.setText(str(query.value(9)))
            self.receiveabledata.setText(str(query.value(10)))
            
            
            
            

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



        

            
            
            






