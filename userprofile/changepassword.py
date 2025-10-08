from PySide6.QtWidgets import QWidget, QApplication, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QLineEdit, QLabel, QSpacerItem, QSizePolicy, QMessageBox, QFrame
from PySide6.QtGui import QColor
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
import bcrypt



def load_stylesheet(filename):
    """ Load and return the CSS stylesheet from a file. """
    file = QFile(filename)
    if not file.open(QFile.ReadOnly | QFile.Text):
        print(f"Error opening file: {filename}")
        return ""
    
    css = file.readAll().data().decode()
    file.close()
    return css



class ChangePasswordWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)
        
        
         # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Change Password", objectName="SectionTitle")
        self.profilebutton = QPushButton("Profile Page", objectName="TopRightButton")
        self.profilebutton.setCursor(Qt.PointingHandCursor)
        self.profilebutton.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.profilebutton)

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
        
        labels = ["Previous Password", "New Password", "Confirm Password"]

        previousinput = QLineEdit()
        passwordinput = QLineEdit()
        confirminput = QLineEdit()
        
        fields = [previousinput, passwordinput, confirminput]
        
        
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
        savebutton = QPushButton("Save Password Changes", objectName="SaveButton")
        savebutton.setCursor(Qt.PointingHandCursor)
        savebutton.clicked.connect(lambda: self.savechanges(previousinput, passwordinput, confirminput))

        self.layout.addWidget(savebutton)
        self.layout.addStretch()
        
        
        
        css = load_stylesheet('styles/global_style.css')
        self.setStyleSheet(css)

        
        
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #47034E; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)
        


    def savechanges(self, previous, newpass, confirmpass):
        
        
        oldpass = previous.text().strip()
        newpass = newpass.text().strip()
        confirmpass = confirmpass.text().strip()
        
        
        if oldpass == '' or newpass == '' or confirmpass == '':
            
            QMessageBox.information(None, 'Password Change', 'All the fields are required...')
            
        else:
            
            
            username = username = QApplication.instance().property("username")
            
            query = QSqlQuery()
            query.prepare("SELECT id, password_hash, salt FROM auth WHERE username = ?")
            query.addBindValue(username)
            
            if query.exec() and query.next():
                
                user_id = query.value(0)
                stored_hash = query.value(1)
                stored_salt = query.value(2)

                # Hash the input password using the stored salt
                input_hash = bcrypt.hashpw(oldpass.encode(), stored_salt.encode()).decode()

                if input_hash == stored_hash:
                    
                    print("Current password is correct... proceeding")
                    
                    if newpass == confirmpass:
                        
                        new_password = newpass  # from user input
                        new_salt = bcrypt.gensalt()
                        new_hash = bcrypt.hashpw(new_password.encode(), new_salt).decode()
                        
                        # Update the password using the ID
                        update_query = QSqlQuery()
                        update_query.prepare(""" UPDATE auth SET password_hash = ?, salt = ? WHERE id = ? """)
                        update_query.addBindValue(new_hash)
                        update_query.addBindValue(new_salt.decode())
                        update_query.addBindValue(user_id)

                        if update_query.exec():
                            print("Password updated successfully.")
                            QMessageBox.information(None, 'Password Change', 'Password Updated Succesfully...')
                        else:
                            print("Failed to update password:", update_query.lastError().text())
                    
                    
                    
                    else:
                        print("Password do not match...")
                        QMessageBox.information(None, 'Password Change', 'New Passwords do not match...')
                    
                    
                    
                    
                else:
                    QMessageBox.information(None, 'Password Change', 'Current Password is Incorrect...')
            else:
                print("User not found or query failed")
            
            
            
        






