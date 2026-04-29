from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFrame, QLabel, QLineEdit, QComboBox, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlDatabase
from PySide6.QtGui import QKeySequence, QShortcut

from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.session_gate import require_open_session
from medic.utilities.app_messagebox import AppMessageBox
from medic.services.party_transaction_service import (
    fetch_customer_transaction_form_context,
    prepare_customer_transaction_payload,
    save_customer_transaction_payload,
)


class CreateCustomerTransactionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from medic.utilities.payment_handler import PaymentMethodHandler

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Receive / Refund Payment by Customer", objectName="SectionTitle")
        self.transactionlist = QPushButton("All Transactions", objectName="TopRightButton")
        self.transactionlist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.transactionlist)
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
        self.layout.addSpacing(10)

        customer_heading_layout = QHBoxLayout()
        customer_heading = QLabel("Customer Information", objectName="SubHeading")
        customer_heading_layout.addWidget(customer_heading)
        self.layout.addLayout(customer_heading_layout)

        customer_row = QHBoxLayout()
        customer_label = QLabel("Customer")
        customer_label.setFixedWidth(300)
        self.customername = QLabel()
        customer_row.addWidget(customer_label, 1)
        customer_row.addWidget(self.customername, 2)
        self.layout.addLayout(customer_row)

        contact_row = QHBoxLayout()
        contact_label = QLabel("Contact")
        contact_label.setFixedWidth(300)
        self.customercontact = QLabel()
        contact_row.addWidget(contact_label, 1)
        contact_row.addWidget(self.customercontact, 2)
        self.layout.addLayout(contact_row)

        self.layout.addSpacing(20)

        payment_heading_layout = QHBoxLayout()
        payment_heading = QLabel("Process Payment", objectName="SubHeading")
        payment_heading_layout.addWidget(payment_heading)
        self.layout.addLayout(payment_heading_layout)

        salesman_row = QHBoxLayout()
        salesman_label = QLabel("Salesman")
        salesman_label.setFixedWidth(300)
        self.salesman = QComboBox()
        salesman_row.addWidget(salesman_label, 1)
        salesman_row.addWidget(self.salesman, 2)
        self.layout.addLayout(salesman_row)

        payable_row = QHBoxLayout()
        payable_label = QLabel("Payable Amount")
        payable_label.setFixedWidth(300)
        self.payable = QLabel()
        payable_row.addWidget(payable_label, 1)
        payable_row.addWidget(self.payable, 2)
        self.layout.addLayout(payable_row)

        receiveable_row = QHBoxLayout()
        receiveable_label = QLabel("Receivable Amount")
        receiveable_label.setFixedWidth(300)
        self.receiveable = QLabel()
        receiveable_row.addWidget(receiveable_label, 1)
        receiveable_row.addWidget(self.receiveable, 2)
        self.layout.addLayout(receiveable_row)

        payment_method_layout = QHBoxLayout()
        payment_method_label = QLabel("Payment Method")
        payment_method_label.setFixedWidth(300)
        self.payment_handler = PaymentMethodHandler(self)
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)
        payment_method_layout.addWidget(payment_method_label, 1)
        payment_method_layout.addWidget(self.payment_method, 2)
        self.layout.addLayout(payment_method_layout)

        paid_row = QHBoxLayout()
        paid_label = QLabel("Refund Amount (You Pay)")
        paid_label.setFixedWidth(300)
        self.paid = QLineEdit()
        self.paid.setText("0")
        paid_row.addWidget(paid_label, 1)
        paid_row.addWidget(self.paid, 2)
        self.layout.addLayout(paid_row)

        received_row = QHBoxLayout()
        received_label = QLabel("Received Amount (Customer Pays)")
        received_label.setFixedWidth(300)
        self.received = QLineEdit()
        self.received.setText("0")
        received_row.addWidget(received_label, 1)
        received_row.addWidget(self.received, 2)
        self.layout.addLayout(received_row)

        note_row = QHBoxLayout()
        note_label = QLabel("Note")
        note_label.setFixedWidth(300)
        self.note = QLineEdit()
        self.note.setPlaceholderText("Note")
        note_row.addWidget(note_label, 1)
        note_row.addWidget(self.note, 2)
        self.layout.addLayout(note_row)

        savepayment = QPushButton("Save Payment", objectName="SaveButton")
        savepayment.setCursor(Qt.PointingHandCursor)
        savepayment.clicked.connect(self.save_payment)
        self.layout.addWidget(savepayment)

        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.save_payment)

        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

    def load_data(self, customer_id):
        context = fetch_customer_transaction_form_context(int(customer_id))
        self.cust_id = int(context["customer_id"])
        self.customername.setText(f"{context['customer_id']} - {context['customer_name']}")
        self.customercontact.setText(context["customer_contact"])
        self.payable.setText(str(context["payable"]))
        self.receiveable.setText(str(context["receiveable"]))

        self.salesman.clear()
        for salesman in context["salesmen"]:
            label = f"{salesman['name']} [{salesman['contact']}]"
            self.salesman.addItem(label, salesman["id"])

    def on_payment_method_changed(self, method):
        success = self.payment_handler.handle_method_change(method)
        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)

    @Permissions.require_permission("transactions.create")
    def save_payment(self):
        if not require_open_session(self):
            return

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.critical(self, "Error", "Could not start database transaction.")
            return

        try:
            data = self._collect_customer_payment_data()
            save_customer_transaction_payload(data)

            if not db.commit():
                raise Exception("Could not commit customer transaction.")

            AppMessageBox.information(self, "Success", "Customer Transaction Saved Successfully.")
            self.load_data(self.cust_id)
            self.paid.setText("0")
            self.received.setText("0")
            self.note.clear()
        except Exception as exc:
            db.rollback()
            AppMessageBox.critical(self, "Error", str(exc))

    def _collect_customer_payment_data(self):
        salesman = self.salesman.currentData()
        customer = int(self.cust_id)
        note = self.note.text().strip()
        payment = self.payment_handler.payment_data.copy()
        data = prepare_customer_transaction_payload(
            customer_id=customer,
            salesman_id=salesman,
            paid_amount=float(self.paid.text() or 0),
            received_amount=float(self.received.text() or 0),
            note=note,
            payment_data=payment,
            allow_excess=False,
        )
        if data.get("needs_confirmation"):
            _, accepted = AppMessageBox.confirm(
                self,
                data["title"],
                data["message"],
                confirm_label="Continue",
                cancel_label="Cancel",
                kind="warning",
            )
            if not accepted:
                raise Exception("Transaction cancelled.")
            data = prepare_customer_transaction_payload(
                customer_id=customer,
                salesman_id=salesman,
                paid_amount=float(self.paid.text() or 0),
                received_amount=float(self.received.text() or 0),
                note=note,
                payment_data=payment,
                allow_excess=True,
            )
        return data

    def clear_fields(self):
        self.customername.clear()
        self.customercontact.clear()
        self.payable.clear()
        self.receiveable.clear()
        self.paid.clear()
        self.received.clear()
        self.note.clear()
        self.payment_method.blockSignals(True)
        self.payment_method.setCurrentIndex(0)
        self.payment_method.blockSignals(False)
