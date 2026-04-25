from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QLineEdit, QLabel,
    QPushButton, QHBoxLayout, QMessageBox, QRadioButton,
    QWidget, QButtonGroup
)

from medic.utilities.payment_dialogs import BankTransferDialog, MobileWalletDialog

class PaymentMethodHandler:
    def __init__(self, parent=None):
        self.parent = parent
        self.payment_data = {
            "payment_method": "Cash",
            "bank_name": None,
            "account_no": None,
            "transaction_mode": None,
            "wallet_provider": None,
            "wallet_no": None,
            "payment_reference": None
        }

    def handle_method_change(self, method: str):
        
        if method == "Cash":
            self.payment_data = {
                "payment_method": "Cash",
                "bank_name": None,
                "account_no": None,
                "transaction_mode": None,
                "wallet_provider": None,
                "wallet_no": None,
                "payment_reference": None
            }
            return True

        if method == "Bank Transfer":
            dialog = BankTransferDialog(self.parent, self.payment_data)
            if dialog.exec():
                self.payment_data = dialog.result_data
                print("payment_data after Bank dialog:", self.payment_data)
                return True
            return False

        if method in ["EasyPaisa", "JazzCash"]:
            dialog = MobileWalletDialog(method, self.parent, self.payment_data)
            if dialog.exec():
                self.payment_data = dialog.result_data
                print("payment_data after Wallet dialog:", self.payment_data)
                return True
            return False

        return False