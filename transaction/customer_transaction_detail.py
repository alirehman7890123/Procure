from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlQuery

from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox


class CustomerTransactionDetailWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Transaction Detail", objectName="SectionTitle")
        self.transactionlist = QPushButton("Transactions List", objectName="TopRightButton")
        self.transactionlist.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(heading, 1)
        header_layout.addWidget(self.transactionlist)
        self.layout.addLayout(header_layout)

        self.identity_frame, identity_layout = self._create_section_card("Customer Information")
        self.customer_name = QLabel("-")
        self.customer_contact = QLabel("-")
        self.salesman = QLabel("-")
        self.creation_date = QLabel("-")

        self._add_info_row(identity_layout, 0, "Customer", self.customer_name, "Contact", self.customer_contact)
        self._add_info_row(identity_layout, 1, "Sales Rep", self.salesman, "Date / Time", self.creation_date)
        self.layout.addWidget(self.identity_frame)

        self.summary_frame, summary_layout = self._create_section_card("Transaction Summary")
        self.transaction = QLabel("-")
        self.payable_before = QLabel("0.00")
        self.receivable_before = QLabel("0.00")
        self.paid = QLabel("0.00")
        self.received = QLabel("0.00")
        self.payable_created = QLabel("0.00")
        self.receivable_created = QLabel("0.00")
        self.reconciled_amount = QLabel("-")
        self.payable_after = QLabel("0.00")
        self.receivable_after = QLabel("0.00")

        self._add_info_row(summary_layout, 0, "Transaction Type", self.transaction, "Reconciled Amount", self.reconciled_amount)
        self._add_info_row(summary_layout, 1, "Payable Before", self.payable_before, "Receivable Before", self.receivable_before)
        self._add_info_row(summary_layout, 2, "Paid Amount", self.paid, "Received Amount", self.received)
        self._add_info_row(summary_layout, 3, "Payable Created / Remaining", self.payable_created, "Receivable Created / Remaining", self.receivable_created)
        self._add_info_row(summary_layout, 4, "Payable After", self.payable_after, "Receivable After", self.receivable_after)
        self.layout.addWidget(self.summary_frame)

        self.note_frame, note_layout = self._create_section_card("Note")
        self.note = QLabel("-")
        self.note.setWordWrap(True)
        self.note.setStyleSheet("padding-left: 0; color: #30485A;")
        note_layout.addWidget(self.note)
        self.layout.addWidget(self.note_frame)

        self.layout.addStretch(1)
        self.setStyleSheet(load_stylesheets())

    def _create_section_card(self, title):
        frame = QFrame()
        frame.setObjectName("sectionCard")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        heading = QLabel(title, objectName="SubHeading")
        layout.addWidget(heading)
        layout.addStretch()

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)
        layout.addLayout(grid)
        return frame, grid

    def _value_label(self, initial_text="-"):
        label = QLabel(initial_text)
        label.setWordWrap(True)
        label.setStyleSheet(
            """
            padding: 6px 8px;
            background-color: #F7FAFC;
            border: 1px solid #D8E3EB;
            border-radius: 4px;
            color: #203546;
            font-weight: 600;
            """
        )
        return label

    def _field_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-weight: 700; color: #35556C; padding-left: 0;")
        return label

    def _add_info_row(self, layout, row, left_label, left_value_widget, right_label, right_value_widget):
        layout.addWidget(self._field_label(left_label), row, 0)
        layout.addWidget(left_value_widget, row, 1)
        layout.addWidget(self._field_label(right_label), row, 2)
        layout.addWidget(right_value_widget, row, 3)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

    def showEvent(self, event):
        super().showEvent(event)
        print("Widget shown — refreshing data")

    def get_customer_transaction(self, id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                customer, transaction_type, ref, return_ref,
                payable_before, due_amount, paid, remaining_due, payable_after,
                receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                salesman, note, creation_date
            FROM customer_transaction
            WHERE id = ?
            """
        )
        query.addBindValue(id)

        if not query.exec():
            print("SQL Error:", query.lastError().text())
            return None

        if query.next():
            record = query.record()
            row_dict = {}
            for i in range(record.count()):
                row_dict[record.fieldName(i)] = query.value(i)
            return row_dict
        return None

    def load_data(self, id):
        row = self.get_customer_transaction(id)
        if not row:
            AppMessageBox.critical(self, "Error", "Transaction not found.")
            return

        customer_id = row["customer"]
        transaction_type = row["transaction_type"]
        payable_before = float(row["payable_before"] or 0.0)
        receivable_before = float(row["receiveable_before"] or 0.0)
        paid = row["paid"]
        received = row["received"]
        payable_after = float(row["payable_after"] or 0.0)
        receivable_after = float(row["receiveable_after"] or 0.0)
        payable_created = float(row["remaining_due"] or 0.0)
        receivable_created = float(row["receiveable_now"] or 0.0)
        salesman = row["salesman"]
        creation = row["creation_date"]
        note = row["note"]

        if customer_id is not None:
            customer_query = QSqlQuery()
            customer_query.prepare("SELECT name, contact FROM customer WHERE id = ?")
            customer_query.addBindValue(int(customer_id))
            if customer_query.exec() and customer_query.next():
                customer_name = customer_query.value(0)
                customer_contact = customer_query.value(1)
            else:
                AppMessageBox.critical(self, "Error", customer_query.lastError().text())
                return
        else:
            customer_name = "Walk-in Customer"
            customer_contact = "-"

        if salesman is not None:
            rep_query = QSqlQuery()
            rep_query.prepare("SELECT name FROM employee WHERE id = ?")
            rep_query.addBindValue(int(salesman))
            if rep_query.exec() and rep_query.next():
                salesman_name = rep_query.value(0)
            else:
                salesman_name = "-"
        else:
            salesman_name = "-"

        self.customer_name.setText(str(customer_name))
        self.customer_contact.setText(str(customer_contact or "-"))
        self.salesman.setText(str(salesman_name))
        self.creation_date.setText(str(creation or "-"))

        self.transaction.setText(str(transaction_type or "-"))
        self.payable_before.setText(f"{payable_before:.2f}")
        self.receivable_before.setText(f"{receivable_before:.2f}")
        self.paid.setText(f"{float(paid or 0.0):.2f}")
        self.received.setText(f"{float(received or 0.0):.2f}")
        self.payable_created.setText(f"{payable_created:.2f}")
        self.receivable_created.setText(f"{receivable_created:.2f}")
        self.payable_after.setText(f"{payable_after:.2f}")
        self.receivable_after.setText(f"{receivable_after:.2f}")

        if str(transaction_type) == "INTERNAL_RECONCILIATION":
            reconcile_amount = float(row["due_amount"] or 0.0)
            self.reconciled_amount.setText(f"{reconcile_amount:.2f}")
        else:
            self.reconciled_amount.setText("-")

        self.note.setText(str(note or "-"))
