from PySide6.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout, QFrame, QLabel,
    QVBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, QDateTime
from PySide6.QtSql import QSqlQuery

from utilities.stylus import load_stylesheets


class ExpenseDetailWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()

        heading = QLabel("Expense Detail", objectName="SectionTitle")

        self.expenselist = QPushButton("Expenses List", objectName="TopRightButton")
        self.expenselist.setCursor(Qt.PointingHandCursor)

        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.expenselist)

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

        labels = [
            "Category",
            "Title",
            "Amount",
            "Description",
            "Payment",
            "Date",
            "Created By"
        ]

        self.category = QLabel("-")
        self.title = QLabel("-")
        self.amount = QLabel("-")
        self.description = QLabel("-")
        self.payment = QLabel("-")
        self.creation = QLabel("-")
        self.created_by = QLabel("-")

        fields = [
            self.category,
            self.title,
            self.amount,
            self.description,
            self.payment,
            self.creation,
            self.created_by
        ]

        for label, field in zip(labels, fields):
            row = QHBoxLayout()

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            lbl.setMinimumWidth(200)

            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            field.setWordWrap(True)

            row.addWidget(lbl, 2)
            row.addWidget(field, 8)

            self.layout.addLayout(row)

        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

    def load_expense_data(self, expense_id):
        print("Loading Expense ID:", expense_id)

        query = QSqlQuery()
        query.prepare("""
            SELECT
                category,
                title,
                amount,
                note,
                creation_date,
                payment_method,
                bank_name,
                account_no,
                transaction_mode,
                wallet_provider,
                wallet_no,
                payment_reference,
                user_id
            FROM expense
            WHERE id = ?
        """)
        query.addBindValue(expense_id)

        if not query.exec():
            print("Expense query failed:", query.lastError().text())
            self.clear_labels()
            return

        if not query.next():
            print("Expense not found.")
            self.clear_labels()
            return

        category = str(query.value(0) or "-")
        title = str(query.value(1) or "-")
        amount_value = query.value(2)
        note = str(query.value(3) or "-")
        creation_date = query.value(4)

        payment_method = str(query.value(5) or "").strip()
        bank_name = str(query.value(6) or "").strip()
        account_no = str(query.value(7) or "").strip()
        transaction_mode = str(query.value(8) or "").strip()
        wallet_provider = str(query.value(9) or "").strip()
        wallet_no = str(query.value(10) or "").strip()
        payment_reference = str(query.value(11) or "").strip()

        user_id = query.value(12)

        # Format amount safely
        try:
            amount_text = f"{float(amount_value):.2f}"
        except (TypeError, ValueError):
            amount_text = "0.00"

        # Format date safely
        if isinstance(creation_date, QDateTime):
            creation_text = creation_date.toString("dd-MM-yyyy")
        elif isinstance(creation_date, QDate):
            creation_text = creation_date.toString("dd-MM-yyyy")
        else:
            creation_text = str(creation_date or "-")

        payment_text = self.build_payment_text(
            payment_method=payment_method,
            bank_name=bank_name,
            account_no=account_no,
            transaction_mode=transaction_mode,
            wallet_provider=wallet_provider,
            wallet_no=wallet_no,
            payment_reference=payment_reference
        )

        created_by_text = self.get_user_full_name(user_id)

        self.category.setText(category)
        self.title.setText(title)
        self.amount.setText(amount_text)
        self.description.setText(note)
        self.payment.setText(payment_text)
        self.creation.setText(creation_text)
        self.created_by.setText(created_by_text)

    def build_payment_text(self, payment_method, bank_name, account_no,
                           transaction_mode, wallet_provider, wallet_no,
                           payment_reference):

        payment_method = (payment_method or "").strip()
        bank_name = (bank_name or "").strip()
        account_no = (account_no or "").strip()
        transaction_mode = (transaction_mode or "").strip()
        wallet_provider = (wallet_provider or "").strip()
        wallet_no = (wallet_no or "").strip()
        payment_reference = (payment_reference or "").strip()

        if not payment_method:
            return "-"

        lines = [payment_method]

        if payment_method.lower() == "bank transfer":
            if transaction_mode:
                lines.append(f"Mode: {transaction_mode}")
            if bank_name:
                lines.append(f"Bank: {bank_name}")
            if account_no:
                lines.append(f"Account No: {account_no}")

        elif payment_method.lower() in ("easypaisa", "jazzcash"):
            if wallet_provider:
                lines.append(f"Wallet: {wallet_provider}")
            if wallet_no:
                lines.append(f"Wallet No: {wallet_no}")

        if payment_reference:
            lines.append(f"Reference: {payment_reference}")

        return "\n".join(lines)

    def get_user_full_name(self, user_id):
        if user_id in (None, "", 0):
            return "-"

        query = QSqlQuery()
        query.prepare("""
            SELECT first_name, last_name
            FROM auth
            WHERE id = ?
        """)
        query.addBindValue(user_id)

        if not query.exec():
            print("User query failed:", query.lastError().text())
            return "-"

        if not query.next():
            return "-"

        first_name = str(query.value(0) or "").strip()
        last_name = str(query.value(1) or "").strip()

        full_name = f"{first_name} {last_name}".strip()
        return full_name if full_name else "-"

    def clear_labels(self):
        self.category.setText("-")
        self.title.setText("-")
        self.amount.setText("-")
        self.description.setText("-")
        self.payment.setText("-")
        self.creation.setText("-")
        self.created_by.setText("-")
