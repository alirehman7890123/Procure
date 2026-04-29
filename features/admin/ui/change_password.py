from PySide6.QtWidgets import QWidget, QApplication, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QLineEdit, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QEvent

from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from features.admin.services.user_service import change_user_password


class ChangePasswordWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Change Password", objectName="SectionTitle")
        self.profilebutton = QPushButton("Profile Page", objectName="TopRightButton")
        self.profilebutton.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.profilebutton)

        self.layout.addLayout(header_layout)

        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(
            """
                QFrame#lineSeparator {
                    border: none;
                    border-top: 2px solid #333;
                }
            """
        )

        self.layout.addWidget(line)
        self.layout.addSpacing(20)

        labels = ["Previous Password", "New Password", "Confirm Password"]

        self.previousinput = QLineEdit()
        self.passwordinput = QLineEdit()
        self.confirminput = QLineEdit()

        self.previousinput.setEchoMode(QLineEdit.Password)
        self.passwordinput.setEchoMode(QLineEdit.Password)
        self.confirminput.setEchoMode(QLineEdit.Password)

        fields = [self.previousinput, self.passwordinput, self.confirminput]
        self.indicators = {}

        for label, field in zip(labels, fields):
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

        savebutton = QPushButton("Save Password Changes", objectName="SaveButton")
        savebutton.setCursor(Qt.PointingHandCursor)
        savebutton.clicked.connect(self.savechanges)

        self.layout.addWidget(savebutton)
        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #2F5D7C; border: none;")
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")
        return super().eventFilter(obj, event)

    def savechanges(self):
        oldpass = self.previousinput.text().strip()
        newpass = self.passwordinput.text().strip()
        confirmpass = self.confirminput.text().strip()
        username = QApplication.instance().property("username")

        try:
            change_user_password(
                username=username,
                current_password=oldpass,
                new_password=newpass,
                confirm_password=confirmpass,
            )
            self.previousinput.clear()
            self.passwordinput.clear()
            self.confirminput.clear()
            AppMessageBox.information(None, "Password Change", "Password Updated Succesfully...")
        except ValueError as exc:
            AppMessageBox.information(None, "Password Change", str(exc))
        except Exception as exc:
            AppMessageBox.critical(None, "Password Change", str(exc))
