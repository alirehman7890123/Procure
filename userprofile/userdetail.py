from PySide6.QtWidgets import QWidget,QApplication, QFrame, QPushButton, QVBoxLayout, QLineEdit, QLabel,QMessageBox, QHBoxLayout, QSizePolicy, QFrame
from PySide6.QtGui import QColor
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from utilities.stylus import load_stylesheets




class UserDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        
        print("Opening User Detail Page")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)
        
        
         # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("User Information", objectName="SectionTitle")
        
        self.userlist = QPushButton("Users List", objectName="TopRightButton")
        self.userlist.setCursor(Qt.PointingHandCursor)
        self.userlist.setFixedWidth(200)
        
        # self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        # self.edit_btn.setCursor(Qt.PointingHandCursor)
        # self.edit_btn.setFixedWidth(100)
        # self.edit_btn.clicked.connect(self.toggle_edit_mode)
        # header_layout.addWidget(self.edit_btn)
        # self.edit_mode = False  # Track whether we are in edit mode or not
        
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.userlist)

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
        labels = ["First Name", "Last Name", "Email", "Username", "Role", "Status"]
        
        
        self.firstnamedata = QLabel(); self.firstnameedit = QLineEdit()
        self.lastnamedata = QLabel(); self.lastnameedit = QLineEdit()
        self.emaildata = QLabel(); self.emailedit = QLineEdit()
        self.usernamedata = QLabel(); self.usernameedit = QLineEdit()
        self.roledata = QLabel(); 
        self.statusdata = QLabel(); 
        
        self.field_pairs = [
            
            (self.firstnamedata, self.firstnameedit),
            (self.lastnamedata, self.lastnameedit),
            (self.emaildata, self.emailedit),
            (self.usernamedata, self.usernameedit),
            (self.roledata, None),
            (self.statusdata, None)
            
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
    
    # def showEvent(self, event):
    #     super().showEvent(event)
    #     self.load_user_data(id=self.user_id)  # Load data when the widget is shown
        
        


    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #47034E; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)

        
        
    
    # # === Toggle Edit Mode ===
    # def toggle_edit_mode(self):
    #     self.edit_mode = not self.edit_mode
    #     if self.edit_mode:
    #         self.edit_btn.setText("Save")
    #         # Switch to QLineEdit
    #         for lbl, edit in self.field_pairs:
    #             if edit:
    #                 edit.setText(lbl.text())
    #                 lbl.hide()
    #                 edit.show()
    #     else:
    #         self.save_changes()
    #         self.edit_btn.setText("Edit")
    #         # Switch back to QLabel
    #         for lbl, edit in self.field_pairs:
    #             if edit:
    #                 lbl.setText(edit.text())
    #                 edit.hide()
    #                 lbl.show()
    
    
    
    
    # === Load Data ===
    def load_user_data(self, id):
        
        query = QSqlQuery()
        query.prepare("SELECT id, firstname, lastname, email, username, role, status FROM auth WHERE id = ?")
        query.addBindValue(id)

        if query.exec() and query.next():
            
            self.user_id = query.value(0)
            print("User ID:", self.user_id)

            self.firstnamedata.setText(query.value(1))
            self.lastnamedata.setText(query.value(2))
            self.emaildata.setText(query.value(3))
            self.usernamedata.setText(query.value(4))
            self.roledata.setText(query.value(5))
            self.statusdata.setText(query.value(6))
            
            print("User data loaded successfully.")
            
    

        
    # === Save Changes ===
    # def save_changes(self):
        
    #     if not self.user_id:
    #         print("No user loaded.")
    #         return

    #     query = QSqlQuery()
    #     query.prepare("""
    #         UPDATE auth
    #         SET firstname=?, lastname=?, email=?, username=?
    #         WHERE id=?
    #     """)
        
    #     firstname = self.firstnameedit.text()
    #     lastname = self.lastnameedit.text()
    #     email = self.emailedit.text()
    #     username = self.usernameedit.text()


    #     query.addBindValue(firstname)
    #     query.addBindValue(lastname)
    #     query.addBindValue(email)
    #     query.addBindValue(username)
    #     query.addBindValue(self.user_id)

    #     if not query.exec():
    #         print("Error updating user:", query.lastError().text())
    #     else:
    #         print("User updated successfully.")
        

   


