from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout, QSizePolicy

from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from medic.features.finance.services.party_transaction_service import fetch_supplier_transaction_detail


class SupplierTransactionDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Transaction Detail", objectName="SectionTitle")
        self.transactionlist = QPushButton("Show Suppliers Transactions", objectName="TopRightButton")
        self.transactionlist.setCursor(self.transactionlist.cursor())
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
        layout.addWidget(QLabel(title, objectName="SubHeading"))
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

    def load_data(self, transaction_id):
        try:
            row = fetch_supplier_transaction_detail(transaction_id)
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))
            return
        if row is None:
            AppMessageBox.critical(self, "Error", "Transaction not found.")
            return

        transaction_type = row["transaction_type"]
        self.supplier_name.setText(str(row["supplier_name"] or "-"))
        self.supplier_contact.setText(str(row["supplier_contact"] or "-"))
        self.rep.setText(str(row["rep_name"] or "-"))
        self.creation_date.setText(str(row["creation_date"] or "-"))
        self.transaction.setText(str(transaction_type or "-"))
        self.payable_before.setText(f"{float(row['payable_before'] or 0.0):.2f}")
        self.receivable_before.setText(f"{float(row['receiveable_before'] or 0.0):.2f}")
        self.paid.setText(f"{float(row['paid'] or 0.0):.2f}")
        self.received.setText(f"{float(row['received'] or 0.0):.2f}")
        self.payable_created.setText(f"{float(row['remaining_due'] or 0.0):.2f}")
        self.receivable_created.setText(f"{float(row['receiveable_now'] or 0.0):.2f}")
        self.payable_after.setText(f"{float(row['payable_after'] or 0.0):.2f}")
        self.receivable_after.setText(f"{float(row['receiveable_after'] or 0.0):.2f}")
        if str(transaction_type) == "INTERNAL_RECONCILIATION":
            self.reconciled_amount.setText(f"{float(row['due_amount'] or 0.0):.2f}")
        else:
            self.reconciled_amount.setText("-")
        self.note.setText(str(row["note"] or "-"))
