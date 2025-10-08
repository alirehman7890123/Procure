from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QLineEdit, QComboBox, QMessageBox, QSizePolicy
)
from PySide6.QtCore import QFile, Qt, QDate, QDateTime
from PySide6.QtSql import QSqlQuery
from utilities.stylus import load_stylesheets



class SalesRepDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_id = None
        self.edit_mode = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        heading = QLabel("Sales Rep Detail", objectName="SectionTitle")
        self.salesreplist = QPushButton("Sales Reps List", objectName="TopRightButton")
        self.salesreplist.setCursor(Qt.PointingHandCursor)
        self.salesreplist.setFixedWidth(200)

        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedWidth(100)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)

        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.salesreplist)
        self.layout.addLayout(header_layout)

        # Separator
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

        # Labels -> display QLabel + edit widgets (supplier stays read-only)
        labels = ["Rep Name", "Supplier", "Contact", "Status", "Joining Date"]

        # display labels (keep original names for compatibility)
        self.salesrep = QLabel()
        self.supplier = QLabel()          # must remain non-editable per request
        self.contact = QLabel()
        self.status = QLabel()
        self.joining = QLabel()

        # edit widgets
        self.salesrep_edit = QLineEdit()
        self.contact_edit = QLineEdit()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive"])
        # joining is read-only label (no edit widget)
        # supplier is read-only label (no edit widget)

        # pairs: (display_label, edit_widget_or_None)
        self.field_pairs = [
            (self.salesrep, self.salesrep_edit),
            (self.supplier, None),            # supplier readonly
            (self.contact, self.contact_edit),
            (self.status, self.status_combo),
            (self.joining, None)              # joining readonly
        ]

        # build rows
        for (label_text, (display_widget, edit_widget)) in zip(labels, self.field_pairs):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            lbl.setMinimumWidth(200)

            display_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            row.addWidget(lbl, 2)
            row.addWidget(display_widget, 8)

            if edit_widget:
                edit_widget.hide()
                edit_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                row.addWidget(edit_widget, 8)

            self.layout.addLayout(row)



        self.layout.addStretch()

       
        self.setStyleSheet(load_stylesheets())
        
        
        
        
        

    # Toggle between edit/read modes
    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            # Enter edit mode
            self.edit_btn.setText("Save")
            for display, edit in self.field_pairs:
                if edit:
                    # populate editor from display
                    if isinstance(edit, QComboBox):
                        idx = edit.findText(display.text(), Qt.MatchFixedString)
                        edit.setCurrentIndex(idx if idx >= 0 else 0)
                    else:
                        edit.setText(display.text())
                    display.hide()
                    edit.show()
        else:
            # Exit edit mode: save and show labels again
            self._save_and_exit_edit_mode()
            
            
    
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
            
        
    

    def _save_and_exit_edit_mode(self):
        # Save then revert UI
        saved = self.save_changes()
        if not saved:
            # if saving failed, remain in edit mode so user can correct
            return

        self.edit_mode = False
        self.edit_btn.setText("Edit")
        for display, edit in self.field_pairs:
            if edit:
                # update display from editor
                if isinstance(edit, QComboBox):
                    display.setText(edit.currentText())
                else:
                    display.setText(edit.text())
                edit.hide()
                display.show()

    # Persist changes to DB
    def save_changes(self) -> bool:
        if not self.current_id:
            QMessageBox.warning(self, "Error", "No Sales Rep loaded to save.")
            return False

        name = self.salesrep_edit.text().strip()
        contact = self.contact_edit.text().strip()
        status = self.status_combo.currentText()

        if not name or not contact:
            QMessageBox.warning(self, "Missing Data", "Rep name and contact are required.")
            return False

        try:
            query = QSqlQuery()
            query.prepare("""
                UPDATE rep
                SET name = ?, contact = ?, status = ?
                WHERE id = ?
            """)
            query.addBindValue(name)
            query.addBindValue(contact)
            query.addBindValue(status)
            query.addBindValue(self.current_id)

            if not query.exec():
                QMessageBox.critical(self, "Error", f"Failed to update: {query.lastError().text()}")
                return False

            QMessageBox.information(self, "Success", "Sales Rep updated successfully.")
            return True

        except Exception as e:
            QMessageBox.critical(self, "Unexpected Error", str(e))
            return False

    # Load DB values into both display and edit widgets
    def load_salesrep_data(self, rep_id):
        self.current_id = rep_id
        query = QSqlQuery()
        query.prepare("SELECT * FROM rep WHERE id = ?")
        query.addBindValue(rep_id)

        if query.exec() and query.next():
            supplier = query.value(2)
            try:
                supplier = int(supplier)
            except Exception:
                supplier = None
            supplier_name = self.get_supplier_name(supplier) if supplier else "Unknown"

            # populate label & edit widgets
            name_val = str(query.value(1) or "")
            self.salesrep.setText(name_val)
            self.salesrep_edit.setText(name_val)

            self.supplier.setText(supplier_name)  # readonly label only

            contact_val = str(query.value(3) or "")
            self.contact.setText(contact_val)
            self.contact_edit.setText(contact_val)

            status_value = str(query.value(4) or "")
            self.status.setText(status_value)
            idx = self.status_combo.findText(status_value, Qt.MatchFixedString)
            self.status_combo.setCurrentIndex(idx if idx >= 0 else 0)

            joining_date = query.value(5)
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)
            self.joining.setText(joining_date)

    def get_supplier_name(self, supplier_id):
        query = QSqlQuery()
        query.prepare("SELECT name FROM supplier WHERE id = :id")
        query.bindValue(":id", supplier_id)
        if query.exec() and query.next():
            return query.value(0)
        return "Unknown"
