from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from medic.services.financial_closing_service import get_quarter_summary
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.stylus import load_stylesheets


class FinancialQuarterSummaryPage(QWidget):
    back_to_history = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._quarter_label = ""

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.setAlignment(0x20)

        header_layout = QHBoxLayout()
        heading = QLabel("Quarter Summary", objectName="SectionTitle")
        header_layout.addWidget(heading)
        header_layout.addStretch()
        self.back_btn = QPushButton("Back To History")
        self.back_btn.setObjectName("TopRightButton")
        self.back_btn.clicked.connect(self.back_to_history.emit)
        header_layout.addWidget(self.back_btn)
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

        self.summary_intro = QLabel("Quarter summary will appear after the third closed month in a quarter.")
        self.summary_intro.setWordWrap(True)
        self.layout.addWidget(self.summary_intro)

        self.summary_label = QLabel("No quarter summary loaded.")
        self.summary_label.setWordWrap(True)
        self.layout.addWidget(self.summary_label)

        self.months_table = QTableWidget(0, 1)
        self.months_table.setHorizontalHeaderLabels(["Included Months"])
        self.months_table.verticalHeader().setVisible(False)
        self.layout.addWidget(self.months_table)

        self.setStyleSheet(load_stylesheets())

    def reset_to_default(self):
        self._quarter_label = ""
        self.summary_intro.setText("Quarter summary will appear after the third closed month in a quarter.")
        self.summary_label.setText("No quarter summary loaded.")
        self.months_table.setRowCount(0)

    def load_quarter_summary(self, quarter_label):
        self._quarter_label = str(quarter_label or "").strip().upper()
        summary = get_quarter_summary(self._quarter_label)
        if not isinstance(summary, dict):
            self.reset_to_default()
            AppMessageBox.warning(self, "Summary Unavailable", "Quarter summary is not available for the selected quarter.")
            return False

        self.summary_intro.setText("This is a derived summary built from the three closed months in the selected quarter.")
        self.summary_label.setText(self._build_summary_text(summary))

        self.months_table.setRowCount(0)
        for row_index, month_label in enumerate(summary.get("included_months") or []):
            self.months_table.insertRow(row_index)
            self.months_table.setItem(row_index, 0, QTableWidgetItem(str(month_label or "")))

        return True

    def _build_summary_text(self, summary):
        def _money(value):
            try:
                return f"{float(value or 0):.2f}"
            except (TypeError, ValueError):
                return "0.00"

        return (
            f"Quarter: {summary.get('quarter_label') or '-'}\n"
            f"Range: {summary.get('period_start') or '-'} to {summary.get('period_end') or '-'}\n"
            f"Generated At: {summary.get('derived_at') or '-'}\n\n"
            f"Sales: {_money(summary.get('sales_total'))}\n"
            f"Purchases: {_money(summary.get('purchase_total'))}\n"
            f"Expenses: {_money(summary.get('expense_total'))}\n"
            f"Customer Due: {_money(summary.get('customer_due'))}\n"
            f"Supplier Due: {_money(summary.get('supplier_due'))}\n"
            f"Inventory Value: {_money(summary.get('inventory_value'))}"
        )
