from PySide6.QtWidgets import QWidget,QApplication, QFrame, QPushButton, QVBoxLayout, QLineEdit, QLabel,QMessageBox, QHBoxLayout, QSizePolicy, QFrame
from PySide6.QtGui import QColor
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery


import os
import sys

def resource_path(relative_path):
    """Return the absolute path to a resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS  # PyInstaller extracts files here
    except AttributeError:
        base_path = os.path.abspath(".")  # running from source
    return os.path.join(base_path, relative_path)



def load_stylesheets():
    """Load and combine all CSS files from the styles folder."""
    styles_dir = resource_path("styles")
    css_content = ""

    if os.path.exists(styles_dir):
        for file in os.listdir(styles_dir):
            if file.endswith(".css"):
                css_file = os.path.join(styles_dir, file)
                with open(css_file, "r") as f:
                    css_content += f.read() + "\n"
                    
    return css_content





class ProfileWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        
        print("Opening Profile Page")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)
        
        
         # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Profile Information", objectName="SectionTitle")
        
        self.userlist = QPushButton("Users List", objectName="TopRightButton")
        self.userlist.setCursor(Qt.PointingHandCursor)
        self.userlist.setFixedWidth(200)
        
        self.changepassword = QPushButton("Change Password", objectName="TopRightButton")
        self.changepassword.setCursor(Qt.PointingHandCursor)
        self.changepassword.setFixedWidth(200)
        
        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedWidth(100)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        header_layout.addWidget(self.edit_btn)
        self.edit_mode = False  # Track whether we are in edit mode or not
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.userlist)
        header_layout.addWidget(self.changepassword)

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
       
        

    
    def showEvent(self, event):
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_profile_data()
        
        


    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #47034E; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)

        
        
    
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
    
    
    # # === Load Data ===
    # def load_user_data(self, id):
        
    #     query = QSqlQuery()
    #     query.prepare("SELECT id, firstname, lastname, email, role, status FROM auth WHERE id = ?")
    #     query.addBindValue(id)

    #     if query.exec() and query.next():
            
    #         self.user_id = query.value(0)
    #         print("User ID:", self.user_id)

    #         self.firstnamedata.setText(query.value(1))
    #         self.lastnamedata.setText(query.value(2))
    #         self.emaildata.setText(query.value(3))
    #         self.usernamedata.setText(query.value(4))
    #         self.roledata.setText(query.value(5))
    #         self.statusdata.setText(query.value(6))
            
    #         print("User data loaded successfully.")
            
    
    
    
    
    # === Load Data ===
    def load_profile_data(self):
        
        
        username = QApplication.instance().property("username")
        print("Loading profile for user:", username)
        
        
        query = QSqlQuery()
        query.prepare("SELECT id, firstname, lastname, email, role, status FROM auth WHERE username = ?")
        query.addBindValue(username)
        

        if query.exec() and query.next():
            
            self.user_id = query.value(0)
            print("User ID:", self.user_id)
            
            self.firstnamedata.setText(query.value(1))
            self.lastnamedata.setText(query.value(2))
            self.emaildata.setText(query.value(3))
            self.usernamedata.setText(username)
            self.roledata.setText(query.value(4))
            self.statusdata.setText(query.value(5))
            
            print("Profile data loaded successfully.")
            
            

        
    # === Save Changes ===
    def save_changes(self):
        
        if not self.user_id:
            print("No user loaded.")
            return

        query = QSqlQuery()
        query.prepare("""
            UPDATE auth
            SET firstname=?, lastname=?, email=?, username=?
            WHERE id=?
        """)
        
        firstname = self.firstnameedit.text()
        lastname = self.lastnameedit.text()
        email = self.emailedit.text()
        username = self.usernameedit.text()


        query.addBindValue(firstname)
        query.addBindValue(lastname)
        query.addBindValue(email)
        query.addBindValue(username)
        query.addBindValue(self.user_id)

        if not query.exec():
            print("Error updating user:", query.lastError().text())
        else:
            print("User updated successfully.")
        

   


