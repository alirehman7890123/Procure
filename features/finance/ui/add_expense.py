from PySide6.QtWidgets import QWidget, QApplication, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QFrame, QLineEdit, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QEvent

from medic.utilities.stylus import load_stylesheets
from medic.utilities.payment_handler import PaymentMethodHandler
from medic.utilities.permissions import Permissions
from medic.utilities.session_gate import require_open_session
from medic.utilities.session_service import get_active_session_id
from medic.utilities.app_messagebox import AppMessageBox
from medic.features.finance.services.expense_service import create_expense


class AddExpenseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Expense Information", objectName="SectionTitle")
        self.expenselist = QPushButton("Expense List", objectName="TopRightButton")
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

        labels = ["Category", "Title", "Payment Method", "Amount", "Description"]

        self.category = QComboBox()
        self.category.setEditable(True)
        self.category.addItems(["Office", "Pharmacist", "Utility", "Food"])

        self.title = QComboBox()
        self.title.setEditable(True)
        self.title.addItems(["Lunch", "Guest Food", "Refreshment", "Fee"])
        self.title.setStyleSheet(
            """
            QComboBox { color: #333; }
            QComboBox:editable { color: #333; }
            QComboBox QAbstractItemView {
                color: #333;
                background: #fff;
                border: 1px solid #ccc;
                outline: 0;
            }
            QComboBox QAbstractItemView::item { padding: 6px 8px; }
            QComboBox QAbstractItemView::item:hover { background: #f5f5f5; }
            QComboBox QAbstractItemView::item:selected {
                background: #e4682a;
                color: #fff;
            }
        """
        )

        self.payment_handler = PaymentMethodHandler(self)
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)

        self.amount = QLineEdit()
        self.description = QLineEdit()

        fields = [self.category, self.title, self.payment_method, self.amount, self.description]
        self.indicators = {}

        for label, field in zip(labels, fields):
            row = QHBoxLayout()
            indicator = QFrame()
            indicator.setFixedWidth(4)
            indicator.setStyleSheet("background-color: #ccc; border: none;")

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(indicator)
            row.addWidget(lbl, 1)
            row.addWidget(field, 8)

            self.layout.addLayout(row)
            self.layout.setSpacing(10)

            self.indicators[field] = indicator
            field.installEventFilter(self)

        addexpense = QPushButton("Add Expense", objectName="SaveButton")
        addexpense.setCursor(Qt.PointingHandCursor)
        addexpense.clicked.connect(self.save_expense)
        self.layout.addWidget(addexpense)
        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

    def on_payment_method_changed(self, method):
        success = self.payment_handler.handle_method_change(method)
        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #5A9EC9; border: none;")
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")
        return super().eventFilter(obj, event)

    @Permissions.require_permission("expense.create")
    def save_expense(self):
        if not require_open_session(self):
            return

        category = self.category.currentText().strip()
        title = self.title.currentText().strip()
        amount = self.amount.text().strip()
        note = self.description.text()
        payment = self.payment_handler.payment_data.copy()

        session_id = get_active_session_id(strict=True)
        if session_id is None:
            AppMessageBox.warning(self, "Validation Error", "No active session found.")
            return

        username = QApplication.instance().property("username")

        try:
            create_expense(
                category=category,
                title=title,
                amount=amount,
                note=note,
                session_id=session_id,
                username=username,
                user_id=QApplication.instance().property("user_id"),
                payment_data=payment,
            )
            AppMessageBox.information(self, "Success", "Expense added successfully")
            self.clear_fields()
        except ValueError as exc:
            AppMessageBox.warning(self, "Validation Error", str(exc))
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))

    def clear_fields(self):
        self.category.clear()
        self.title.clear()
        self.amount.clear()
        self.description.clear()
        self.payment_method.blockSignals(True)
        self.payment_method.setCurrentIndex(0)
        self.payment_method.blockSignals(False)
