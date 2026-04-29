from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QFrame, QSizePolicy, QComboBox, QMessageBox
from PySide6.QtCore import QSize, Qt, QEvent

from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.services.user_service import create_user


class AddUserWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Add New User", objectName="SectionTitle")
        self.userlist = QPushButton("User List", objectName="TopRightButton")
        self.userlist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
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

        labels = ["First Name", "Last Name", "Email", "Username", "Password", "Role"]

        self.editfirstname = QLineEdit()
        self.editlastname = QLineEdit()
        self.editemail = QLineEdit()
        self.editusername = QLineEdit()
        self.editpassword = QLineEdit()
        self.editpassword.setEchoMode(QLineEdit.Password)
        self.selectrole = QComboBox()
        self.selectrole.addItems(Permissions.assignable_roles())

        fields = [
            self.editfirstname,
            self.editlastname,
            self.editemail,
            self.editusername,
            self.editpassword,
            self.selectrole,
        ]

        self.indicators = {}

        for (label, field) in zip(labels, fields):
            row = QHBoxLayout()

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
            self.layout.setSpacing(10)

            self.indicators[field] = indicator
            field.installEventFilter(self)

        adduser = QPushButton("Add User", objectName="SaveButton")
        adduser.setCursor(Qt.PointingHandCursor)
        adduser.clicked.connect(lambda: self.save_user())

        self.layout.addWidget(adduser)
        self.layout.addStretch()

        self.setStyleSheet(load_stylesheets())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #2F5D7C; border: none;")
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")
        return super().eventFilter(obj, event)

    @Permissions.require_permission('users.create')
    def save_user(self):

        firstname = self.editfirstname.text()
        lastname = self.editlastname.text()
        email = self.editemail.text()
        username = self.editusername.text()
        password = self.editpassword.text()
        role = self.selectrole.currentText()

        try:
            create_user(
                firstname=firstname,
                lastname=lastname,
                email=email,
                username=username,
                password=password,
                role=role,
            )
            AppMessageBox.information(None, "Success", "New User Record Saved Successfully")
            self.editfirstname.clear()
            self.editlastname.clear()
            self.editemail.clear()
            self.editusername.clear()
            self.editpassword.clear()
            if self.selectrole.count() > 0:
                self.selectrole.setCurrentIndex(0)
        except ValueError as exc:
            title = "Weak Password" if "Password" in str(exc) else "Warning"
            AppMessageBox.warning(None, title, str(exc))
        except Exception as exc:
            AppMessageBox.critical(None, "Error", str(exc))
