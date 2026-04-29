from PySide6.QtWidgets import QWidget, QApplication, QFrame, QPushButton, QVBoxLayout, QLineEdit, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt

from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.stylus import load_stylesheets
from medic.features.admin.services.user_service import fetch_profile_by_username, update_user_profile


class ProfileWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.user_id = None
        self.edit_mode = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Profile Information", objectName="SectionTitle")

        self.userlist = QPushButton("Users List", objectName="TopRightButton")
        self.userlist.setCursor(Qt.PointingHandCursor)

        self.changepassword = QPushButton("Change Password", objectName="TopRightButton")
        self.changepassword.setCursor(Qt.PointingHandCursor)

        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        header_layout.addWidget(self.edit_btn)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.userlist)
        header_layout.addWidget(self.changepassword)

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

        labels = ["First Name", "Last Name", "Email", "Username", "Role", "Status"]

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

            self.layout.addLayout(row)

        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

    def showEvent(self, event):
        super().showEvent(event)
        self.load_profile_data()

    @Permissions.require_permission('profile.update')
    def toggle_edit_mode(self):
        if not self.edit_mode:
            self.edit_mode = True
            self.edit_btn.setText("Save")
            for lbl, edit in self.field_pairs:
                if edit:
                    edit.setText(lbl.text())
                    lbl.hide()
                    edit.show()
            return

        if self.save_changes():
            self.edit_mode = False
            self.edit_btn.setText("Edit")
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(edit.text())
                    edit.hide()
                    lbl.show()

    def hideEvent(self, event):
        if self.edit_mode:
            self.edit_mode = False
            self.edit_btn.setText("Edit")
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(edit.text())
                    edit.hide()
                    lbl.show()

        super().hideEvent(event)

    def load_profile_data(self):
        username = QApplication.instance().property("username")

        profile = fetch_profile_by_username(username)
        if not profile:
            return

        self.user_id = profile["id"]
        self.firstnamedata.setText(str(profile.get("firstname") or ""))
        self.lastnamedata.setText(str(profile.get("lastname") or ""))
        self.emaildata.setText(str(profile.get("email") or ""))
        self.usernamedata.setText(str(profile.get("username") or username))
        self.roledata.setText(str(profile.get("role") or ""))
        self.statusdata.setText(str(profile.get("status") or ""))

    @Permissions.require_permission('profile.update')
    def save_changes(self):
        if not self.user_id:
            return False

        firstname = self.firstnameedit.text()
        lastname = self.lastnameedit.text()
        email = self.emailedit.text()
        username = self.usernameedit.text()

        try:
            updated = update_user_profile(
                user_id=self.user_id,
                firstname=firstname,
                lastname=lastname,
                email=email,
                username=username,
            )
            self.firstnamedata.setText(str(updated.get("firstname", "")))
            self.lastnamedata.setText(str(updated.get("lastname", "")))
            self.emaildata.setText(str(updated.get("email", "")))
            self.usernamedata.setText(str(updated.get("username", "")))
            app = QApplication.instance()
            if app:
                app.setProperty("username", str(updated.get("username", "")))
            return True
        except ValueError as exc:
            AppMessageBox.warning(self, "Validation Error", str(exc))
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))

        self.edit_mode = True
        self.edit_btn.setText("Save")
        for lbl, edit in self.field_pairs:
            if edit:
                lbl.hide()
                edit.show()
        return False
