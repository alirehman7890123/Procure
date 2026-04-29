from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QLabel, QLineEdit, QComboBox, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlDatabase
from PySide6.QtGui import QKeySequence, QShortcut

from medic.utilities.stylus import load_stylesheets
from medic.utilities.payment_handler import PaymentMethodHandler
from medic.utilities.permissions import Permissions
from medic.utilities.session_gate import require_open_session
from medic.utilities.app_messagebox import AppMessageBox
from features.finance.services.party_transaction_service import (
    fetch_supplier_transaction_form_context,
    prepare_supplier_transaction_payload,
    save_supplier_transaction_payload,
)


class CreateSupplierTransactionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Pay / Receive Payment by Supplier", objectName="SectionTitle")
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
        self.layout.addSpacing(20)

        supplier_heading_layout = QHBoxLayout()
        supplier_heading = QLabel("Supplier Information", objectName="SubHeading")
        supplier_heading_layout.addWidget(supplier_heading)
        self.layout.addLayout(supplier_heading_layout)

        supplier_row = QHBoxLayout()
        supplier_label = QLabel("Supplier")
        supplier_label.setFixedWidth(300)
        self.suppliername = QLabel()
        supplier_row.addWidget(supplier_label, 1)
        supplier_row.addWidget(self.suppliername, 2)
        self.layout.addLayout(supplier_row)

        address_row = QHBoxLayout()
        address_label = QLabel("Address")
        address_label.setFixedWidth(300)
        self.supplieraddress = QLabel()
        address_row.addWidget(address_label, 1)
        address_row.addWidget(self.supplieraddress, 2)
        self.layout.addLayout(address_row)

        self.layout.addSpacing(20)

        payment_heading_layout = QHBoxLayout()
        payment_heading = QLabel("Make Payment", objectName="SubHeading")
        payment_heading_layout.addWidget(payment_heading)
        self.layout.addLayout(payment_heading_layout)

        rep_row = QHBoxLayout()
        rep_label = QLabel("Sales Rep")
        rep_label.setFixedWidth(300)
        self.rep = QComboBox()
        rep_row.addWidget(rep_label, 1)
        rep_row.addWidget(self.rep, 2)
        self.layout.addLayout(rep_row)

        payable_row = QHBoxLayout()
        payable_label = QLabel("Payable Amount")
        payable_label.setFixedWidth(300)
        self.payable = QLabel()
        payable_row.addWidget(payable_label, 1)
        payable_row.addWidget(self.payable, 2)
        self.layout.addLayout(payable_row)

        receiveable_row = QHBoxLayout()
        receiveable_label = QLabel("Receiveable Amount")
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
        paid_label = QLabel("Paid Amount")
        paid_label.setFixedWidth(300)
        self.paid = QLineEdit()
        self.paid.setText("0")
        paid_row.addWidget(paid_label, 1)
        paid_row.addWidget(self.paid, 2)
        self.layout.addLayout(paid_row)

        received_row = QHBoxLayout()
        received_label = QLabel("Received Amount")
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

    def on_payment_method_changed(self, method):
        success = self.payment_handler.handle_method_change(method)
        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)

    def load_data(self, supplier_id):
        context = fetch_supplier_transaction_form_context(int(supplier_id))
        self.supp_id = int(context["supplier_id"])
        self.suppliername.setText(f"{context['supplier_id']} - {context['supplier_name']}")
        self.supplieraddress.setText(context["supplier_contact"])
        self.payable.setText(str(context["payable"]))
        self.receiveable.setText(str(context["receiveable"]))

        self.rep.clear()
        for rep in context["reps"]:
            self.rep.addItem(f"{rep['name']} [{rep['contact']}]", rep["id"])

    @Permissions.require_permission("transactions.create")
    def save_payment(self):
        if not require_open_session(self):
            return

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.critical(self, "Error", "Could not start database transaction.")
            return

        try:
            data = self._collect_supplier_payment_data()
            save_supplier_transaction_payload(data)

            if not db.commit():
                raise Exception("Could not commit supplier transaction.")

            AppMessageBox.information(self, "Success", "Transaction Saved Successfully.")
            self.load_data(self.supp_id)
            self.paid.setText("0")
            self.received.setText("0")
            self.note.clear()
        except Exception as exc:
            db.rollback()
            AppMessageBox.critical(self, "Error", str(exc))

    def _collect_supplier_payment_data(self):
        rep = self.rep.currentData()
        supplier = int(self.supp_id)
        payment = self.payment_handler.payment_data.copy()
        note = self.note.text().strip()
        data = prepare_supplier_transaction_payload(
            supplier_id=supplier,
            rep_id=rep,
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
                raise Exception("Receipt cancelled by user.")
            data = prepare_supplier_transaction_payload(
                supplier_id=supplier,
                rep_id=rep,
                paid_amount=float(self.paid.text() or 0),
                received_amount=float(self.received.text() or 0),
                note=note,
                payment_data=payment,
                allow_excess=True,
            )
        return data

    def clear_fields(self):
        self.suppliername.clear()
        self.supplieraddress.clear()
        self.payable.clear()
        self.receiveable.clear()
        self.paid.clear()
        self.received.clear()
        self.note.clear()
        self.rep.clear()
        self.payment_method.blockSignals(True)
        self.payment_method.setCurrentIndex(0)
        self.payment_method.blockSignals(False)
