from PySide6.QtWidgets import QWidget, QFrame, QPushButton, QVBoxLayout, QLineEdit, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal

from medic.utilities.permissions import Permissions
from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from medic.features.admin.services.business_service import fetch_business_profile, update_business_profile


class BusinessWidget(QWidget):
    tax_settings_requested = Signal()
    discount_settings_requested = Signal()
    theme_settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.business_id = None
        self.edit_mode = False
        self._business_loaded_once = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Business Information", objectName="SectionTitle")

        self.tax_settings_btn = QPushButton("Tax Settings", objectName="TopRightButton")
        self.tax_settings_btn.setCursor(Qt.PointingHandCursor)
        self.tax_settings_btn.clicked.connect(self.tax_settings_requested.emit)

        self.discount_settings_btn = QPushButton("Discount Settings", objectName="TopRightButton")
        self.discount_settings_btn.setCursor(Qt.PointingHandCursor)
        self.discount_settings_btn.clicked.connect(self.discount_settings_requested.emit)

        self.theme_settings_btn = QPushButton("Theme Settings", objectName="TopRightButton")
        self.theme_settings_btn.setCursor(Qt.PointingHandCursor)
        self.theme_settings_btn.clicked.connect(self.theme_settings_requested.emit)

        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.theme_settings_btn)
        header_layout.addWidget(self.discount_settings_btn)
        header_layout.addWidget(self.tax_settings_btn)
        header_layout.addWidget(self.edit_btn)

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

        labels = ["Business Name", "Address", "Contact", "Email", "Website", "License #", "N.T.N"]

        self.businessname = QLabel()
        self.businessnameedit = QLineEdit()
        self.address = QLabel()
        self.addressedit = QLineEdit()
        self.contact = QLabel()
        self.contactedit = QLineEdit()
        self.email = QLabel()
        self.emailedit = QLineEdit()
        self.website = QLabel()
        self.websiteedit = QLineEdit()
        self.license = QLabel()
        self.licenseedit = QLineEdit()
        self.ntn = QLabel()
        self.ntnedit = QLineEdit()

        self.field_pairs = [
            (self.businessname, self.businessnameedit),
            (self.address, self.addressedit),
            (self.contact, self.contactedit),
            (self.email, self.emailedit),
            (self.website, self.websiteedit),
            (self.license, self.licenseedit),
            (self.ntn, self.ntnedit),
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

            edit_field.hide()
            row.addWidget(edit_field, 8)

            self.layout.addLayout(row)

        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

    def showEvent(self, event):
        super().showEvent(event)
        if not self._business_loaded_once:
            self.load_business_data()
            self._business_loaded_once = True

    @Permissions.require_permission('business.update')
    def toggle_edit_mode(self):
        if not self.edit_mode:
            self.edit_mode = True
            self.edit_btn.setText("Save")
            for lbl, edit in self.field_pairs:
                edit.setText(lbl.text())
                lbl.hide()
                edit.show()
            return

        if self.save_changes():
            self.edit_mode = False
            self.edit_btn.setText("Edit")
            for lbl, edit in self.field_pairs:
                lbl.setText(edit.text())
                edit.hide()
                lbl.show()

    def hideEvent(self, event):
        if self.edit_mode:
            self.edit_mode = False
            self.edit_btn.setText("Edit")
            for lbl, edit in self.field_pairs:
                lbl.setText(edit.text())
                edit.hide()
                lbl.show()

        super().hideEvent(event)

    def load_business_data(self):
        profile = fetch_business_profile()
        if not profile:
            return

        self.business_id = profile["id"]
        self.businessname.setText(str(profile.get("businessname") or ""))
        self.address.setText(str(profile.get("address") or ""))
        self.contact.setText(str(profile.get("contact") or ""))
        self.email.setText(str(profile.get("email") or ""))
        self.website.setText(str(profile.get("website") or ""))
        self.license.setText(str(profile.get("license") or ""))
        self.ntn.setText(str(profile.get("ntn") or ""))

    @Permissions.require_permission('business.update')
    def save_changes(self):
        if not self.business_id:
            return False

        businessname = self.businessnameedit.text()
        address = self.addressedit.text()
        contact = self.contactedit.text()
        email = self.emailedit.text()
        website = self.websiteedit.text()
        license_no = self.licenseedit.text()
        ntn = self.ntnedit.text()

        try:
            updated = update_business_profile(
                business_id=self.business_id,
                businessname=businessname,
                address=address,
                contact=contact,
                email=email,
                website=website,
                license_no=license_no,
                ntn=ntn,
            )
            self.businessname.setText(str(updated.get("businessname", "")))
            self.address.setText(str(updated.get("address", "")))
            self.contact.setText(str(updated.get("contact", "")))
            self.email.setText(str(updated.get("email", "")))
            self.website.setText(str(updated.get("website", "")))
            self.license.setText(str(updated.get("license", "")))
            self.ntn.setText(str(updated.get("ntn", "")))
            return True
        except ValueError as exc:
            AppMessageBox.warning(self, "Validation Error", str(exc))
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))

        self.edit_mode = True
        self.edit_btn.setText("Save")
        for lbl, edit in self.field_pairs:
            lbl.hide()
            edit.show()
        return False
