            
from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QHeaderView, QTableWidget, QTableWidgetItem, QSpacerItem,
    QLineEdit, QSizePolicy, QApplication, QMessageBox
)
from PySide6.QtCore import QFile, Qt, QDate, QDateTime
from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.services.supplier_service import fetch_supplier_detail, update_supplier


class SupplierDetailWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.supplier_id = None
        self.edit_mode = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Supplier Detail", objectName="SectionTitle")
        self.supplierlist = QPushButton("Suppliers List", objectName="TopRightButton")
        self.supplierlist.setCursor(Qt.PointingHandCursor)

        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)

        header_layout.setContentsMargins(0, 0, 0, 10)
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
        self.layout.addSpacing(10)

        # === Labels + Fields ===
        info_frame = QFrame()
        info_frame.setObjectName("sectionCard")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(8)

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

            if lbl_field in (self.addressdata, self.websitedata):
                lbl_field.setWordWrap(True)

            info_layout.addLayout(row)

        self.layout.addWidget(info_frame)
        self.layout.addStretch()

        
        self.setStyleSheet(load_stylesheets())
        
        
        
        
        

    # === Toggle Edit Mode ===
    @Permissions.require_permission('supplier.update')
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
    @Permissions.require_permission('supplier.update')
    def save_changes(self):
        
        if not self.supplier_id:
            print("No supplier loaded.")
            return False

        try:
            update_supplier(
                self.supplier_id,
                name=self.nameedit.text(),
                contact=self.contactedit.text(),
                email=self.emailedit.text(),
                website=self.websiteedit.text(),
                address=self.addressedit.text(),
                status=self.statusedit.text(),
                registeration=self.regedit.text(),
            )
        except ValueError as exc:
            AppMessageBox.warning(self, "Validation Error", str(exc))
            return False
        except Exception as exc:
            print("Error updating supplier:", str(exc))
            AppMessageBox.critical(self, "Database Error", str(exc))
            return False
        else:
            print("Supplier updated successfully.")
            return True
        
        
            

    # === Load Data ===
    def load_supplier_data(self, id):
        self.supplier_id = id
        supplier = fetch_supplier_detail(id)
        if supplier:
            self.namedata.setText(supplier["name"])
            self.contactdata.setText(supplier["contact"])
            self.emaildata.setText(supplier["email"])
            self.websitedata.setText(supplier["website"])
            self.addressdata.setText(supplier["address"])
            self.statusdata.setText(supplier["status"])

            joining_date = supplier["creation_date"]
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)

            self.joiningdata.setText(joining_date)
            self.regdata.setText(supplier["reg_no"])
            self.payabledata.setText(f"{supplier['payable']:.2f}")
            self.receiveabledata.setText(f"{supplier['receiveable']:.2f}")
            
            
            
            

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



        

            
            
            


