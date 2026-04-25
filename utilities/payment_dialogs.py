from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QLineEdit, QLabel,
    QPushButton, QHBoxLayout, QMessageBox, QRadioButton,
    QWidget, QButtonGroup
)
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from medic.utilities.app_messagebox import AppMessageBox



class BankTransferDialog(QDialog):
    def __init__(self, parent=None, existing_data=None):
        super().__init__(parent)
        self.setWindowTitle("Bank Transfer Details")
        self.setModal(True)
        self.resize(450, 220)

        self.result_data = {
            "payment_method": "Bank Transfer",
            "bank_name": "",
            "account_no": "",
            "transaction_mode": "National",
            "wallet_provider": "",
            "wallet_no": "",
            "payment_reference": ""
        }

        if existing_data:
            self.result_data.update(existing_data)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.bank_combo = QComboBox()
        self.bank_combo.setEditable(True)
        self.bank_combo.addItems([
            "Habib Bank Limited (HBL)",
            "United Bank Limited (UBL)",
            "MCB Bank Limited (MCB)",
            "National Bank of Pakistan (NBP)",
            "Meezan Bank Limited",
            "Allied Bank Limited (ABL)",
            "Bank Alfalah",
            "Askari Bank"
        ])
        self.bank_combo.setCurrentText(self.result_data["bank_name"])

        tx_widget = QWidget()
        tx_layout = QHBoxLayout(tx_widget)
        tx_layout.setContentsMargins(10, 10, 10, 10)

        self.national_radio = QRadioButton("National")
        self.international_radio = QRadioButton("International")

        self.tx_group = QButtonGroup(self)
        self.tx_group.addButton(self.national_radio)
        self.tx_group.addButton(self.international_radio)

        tx_layout.addWidget(self.national_radio)
        tx_layout.addWidget(self.international_radio)
        tx_layout.addStretch()

        if self.result_data["transaction_mode"] == "International":
            self.international_radio.setChecked(True)
        else:
            self.national_radio.setChecked(True)

        self.account_edit = QLineEdit()
        self.account_edit.setText(self.result_data["account_no"])

        self.local_regex = QRegularExpression(r"^[0-9\-]{6,24}$")
        self.iban_regex = QRegularExpression(r"^PK\d{2}[A-Z]{4}\d{16}$")

        self.national_radio.toggled.connect(self.apply_mode)
        self.international_radio.toggled.connect(self.apply_mode)
        self.account_edit.textChanged.connect(self.force_uppercase)

        self.apply_mode()

        form_layout.addRow("Bank Name:", self.bank_combo)
        form_layout.addRow("Transaction Type:", tx_widget)
        form_layout.addRow("Account No:", self.account_edit)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        ok_btn.clicked.connect(self.save_and_accept)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

    def apply_mode(self):
        if self.national_radio.isChecked():
            self.account_edit.setPlaceholderText("Enter local account number")
            self.account_edit.setValidator(
                QRegularExpressionValidator(self.local_regex, self.account_edit)
            )
        else:
            self.account_edit.setPlaceholderText("PK12ABCD1234567890123456")
            self.account_edit.setValidator(
                QRegularExpressionValidator(self.iban_regex, self.account_edit)
            )

    def force_uppercase(self, text):
        if self.international_radio.isChecked():
            cursor = self.account_edit.cursorPosition()
            upper = text.upper()
            if upper != text:
                self.account_edit.blockSignals(True)
                self.account_edit.setText(upper)
                self.account_edit.setCursorPosition(cursor)
                self.account_edit.blockSignals(False)

    def save_and_accept(self):
        bank = self.bank_combo.currentText().strip()
        account_no = self.account_edit.text().strip().replace(" ", "")
        tx_type = "International" if self.international_radio.isChecked() else "National"

        if not bank:
            AppMessageBox.warning(self, "Missing Data", "Please enter bank name.")
            return

        if tx_type == "National":
            if not self.local_regex.match(account_no).hasMatch():
                AppMessageBox.warning(self, "Invalid", "Enter a valid local account number.")
                return
        else:
            account_no = account_no.upper()
            if not self.iban_regex.match(account_no).hasMatch():
                AppMessageBox.warning(self, "Invalid", "Enter a valid Pakistani IBAN.")
                return

        self.result_data = {
            "payment_method": "Bank Transfer",
            "bank_name": bank,
            "account_no": account_no,
            "transaction_mode": tx_type,
            "wallet_provider": None,
            "wallet_no": None,
            "payment_reference": None
        }
        self.accept()
        
        
        
        
        
        
        

class MobileWalletDialog(QDialog):
    def __init__(self, method, parent=None, existing_data=None):
        super().__init__(parent)
        self.method = method
        self.setWindowTitle(f"{method} Details")
        self.setModal(True)
        self.resize(400, 150)

        self.result_data = {
            "payment_method": method,
            "bank_name": None,
            "account_no": None,
            "transaction_mode": None,
            "wallet_provider": None,
            "wallet_no": None,
            "payment_reference": None
        }

        if existing_data:
            self.result_data.update(existing_data)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.method_label = QLabel(method)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("03XXXXXXXXX")
        self.phone_edit.setMaxLength(11)
        self.phone_edit.setText(self.result_data["wallet_no"])

        self.phone_regex = QRegularExpression(r"^03\d{9}$")
        self.phone_edit.setValidator(
            QRegularExpressionValidator(self.phone_regex, self.phone_edit)
        )

        form_layout.addRow("Payment Method:", self.method_label)
        form_layout.addRow("Phone Number:", self.phone_edit)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        ok_btn.clicked.connect(self.save_and_accept)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

    def save_and_accept(self):
        phone_no = self.phone_edit.text().strip()

        if not self.phone_regex.match(phone_no).hasMatch():
            AppMessageBox.warning(self, "Invalid", "Enter a valid mobile number.")
            return

        self.result_data = {
            "payment_method": self.method,
            "bank_name": None,
            "account_no": None,
            "transaction_mode": None,
            "wallet_provider": self.method,
            "wallet_no": phone_no,
            "payment_reference": None
        }
        self.accept()
        
        
        
        
        