from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QGridLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlQuery

from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox


class SupplierTransactionDetailWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Transaction Detail", objectName="SectionTitle")
        self.transactionlist = QPushButton("Show Suppliers Transactions", objectName="TopRightButton")
        self.transactionlist.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(heading, 1)
        header_layout.addWidget(self.transactionlist)
        self.layout.addLayout(header_layout)

        self.identity_frame, identity_layout = self._create_section_card("Supplier Information")
        self.supplier_name = QLabel("-")
        self.supplier_contact = QLabel("-")
        self.rep = QLabel("-")
        self.creation_date = QLabel("-")

        self._add_info_row(identity_layout, 0, "Supplier", self.supplier_name, "Contact", self.supplier_contact)
        self._add_info_row(identity_layout, 1, "Sales Rep", self.rep, "Date / Time", self.creation_date)
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

    def get_supplier_transaction(self, id):
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                supplier, transaction_type, ref, return_ref,
                payable_before, due_amount, paid, remaining_due, payable_after,
                receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                rep, note, creation_date, due_amount
            FROM supplier_transaction
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
        row = self.get_supplier_transaction(id)
        if not row:
            AppMessageBox.critical(self, "Error", "Transaction not found.")
            return

        supplier_id = int(row["supplier"])
        transaction_type = row["transaction_type"]
        payable_before = float(row["payable_before"] or 0.0)
        receivable_before = float(row["receiveable_before"] or 0.0)
        paid = row["paid"]
        received = row["received"]
        payable_after = float(row["payable_after"] or 0.0)
        receivable_after = float(row["receiveable_after"] or 0.0)
        payable_created = float(row["remaining_due"] or 0.0)
        receivable_created = float(row["receiveable_now"] or 0.0)
        rep = row["rep"]
        creation = row["creation_date"]
        note = row["note"]
        due_amount = float(row["due_amount"] or 0.0)

        supplier_query = QSqlQuery()
        supplier_query.prepare("SELECT name, contact FROM supplier WHERE id = ?")
        supplier_query.addBindValue(supplier_id)
        if supplier_query.exec() and supplier_query.next():
            supplier_name = supplier_query.value(0)
            supplier_contact = supplier_query.value(1)
        else:
            AppMessageBox.critical(self, "Error", supplier_query.lastError().text())
            return

        if rep not in (None, "", 0):
            rep_query = QSqlQuery()
            rep_query.prepare("SELECT name FROM rep WHERE id = ?")
            rep_query.addBindValue(int(rep))
            if rep_query.exec() and rep_query.next():
                rep_name = rep_query.value(0)
            else:
                rep_name = "-"
        else:
            rep_name = "-"

        self.supplier_name.setText(str(supplier_name))
        self.supplier_contact.setText(str(supplier_contact or "-"))
        self.rep.setText(str(rep_name))
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
            self.reconciled_amount.setText(f"{due_amount:.2f}")
        else:
            self.reconciled_amount.setText("-")

        self.note.setText(str(note or "-"))
