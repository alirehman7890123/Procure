from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLineEdit, QLabel, QHBoxLayout, QSizePolicy, QPushButton
from PySide6.QtCore import Qt

from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from features.admin.services.user_service import fetch_user_detail


class UserDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.user_id = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("User Information", objectName="SectionTitle")

        self.userlist = QPushButton("Users List", objectName="TopRightButton")
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

        info_frame = QFrame()
        info_frame.setObjectName("sectionCard")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(8)

        labels = ["User ID", "First Name", "Last Name", "Email", "Username", "Role", "Status"]

        self.useriddata = QLabel("-")
        self.firstnamedata = QLabel()
        self.firstnameedit = QLineEdit()
        self.lastnamedata = QLabel()
        self.lastnameedit = QLineEdit()
        self.emaildata = QLabel()
        self.emailedit = QLineEdit()
        self.usernamedata = QLabel()
        self.usernameedit = QLineEdit()
        self.roledata = QLabel()
        self.statusdata = QLabel()

        self.field_pairs = [
            (self.useriddata, None),
            (self.firstnamedata, self.firstnameedit),
            (self.lastnamedata, self.lastnameedit),
            (self.emaildata, self.emailedit),
            (self.usernamedata, self.usernameedit),
            (self.roledata, None),
            (self.statusdata, None),
        ]

        for label, (lbl_field, edit_field) in zip(labels, self.field_pairs):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            lbl.setMinimumWidth(200)

            lbl_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            row.addWidget(lbl, 2)
            row.addWidget(lbl_field, 8)

            if edit_field:
                edit_field.hide()
                row.addWidget(edit_field, 8)

            info_layout.addLayout(row)

        self.layout.addWidget(info_frame)
        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

    def load_user_data(self, user_id):
        try:
            user = fetch_user_detail(user_id)
        except Exception as exc:
            AppMessageBox.critical(self, "Database Error", str(exc))
            return

        if not user:
            AppMessageBox.information(self, "User Detail", "User record was not found.")
            return

        self.user_id = user["id"]
        self.useriddata.setText(str(self.user_id))
        self.firstnamedata.setText(str(user.get("firstname") or "-"))
        self.lastnamedata.setText(str(user.get("lastname") or "-"))
        self.emaildata.setText(str(user.get("email") or "-"))
        self.usernamedata.setText(str(user.get("username") or "-"))
        self.roledata.setText(str(user.get("role") or "-"))
        self.statusdata.setText(str(user.get("status") or "-"))
