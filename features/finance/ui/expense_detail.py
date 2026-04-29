from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFrame, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt

from medic.utilities.stylus import load_stylesheets
from medic.services.expense_service import fetch_expense_detail


class ExpenseDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

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

        labels = ["Category", "Title", "Amount", "Description", "Payment", "Date", "Created By"]
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
            self.created_by,
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
        try:
            expense = fetch_expense_detail(expense_id)
        except Exception:
            self.clear_labels()
            return

        if not expense:
            self.clear_labels()
            return

        self.category.setText(str(expense.get("category", "-")))
        self.title.setText(str(expense.get("title", "-")))
        self.amount.setText(str(expense.get("amount_text", "0.00")))
        self.description.setText(str(expense.get("note", "-")))
        self.payment.setText(str(expense.get("payment_text", "-")))
        self.creation.setText(str(expense.get("creation_text", "-")))
        self.created_by.setText(str(expense.get("created_by_text", "-")))

    def clear_labels(self):
        self.category.setText("-")
        self.title.setText("-")
        self.amount.setText("-")
        self.description.setText("-")
        self.payment.setText("-")
        self.creation.setText("-")
        self.created_by.setText("-")
