
from PySide6.QtWidgets import QWidget, QPushButton, QComboBox, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy, QToolButton, QDialog, QLineEdit
from PySide6.QtCore import QFile, Qt,QDate
from PySide6.QtGui import QCursor, QColor
from datetime import date
from datetime import datetime
from functools import partial
import pyqtgraph as pg
import sys
import html
from utilities.stylus import load_stylesheets
from reports import report_service
from utilities.app_messagebox import AppMessageBox
from utilities.license_core import get_current_license_payload, is_demo_license


class MainReportsPage(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        self.license_payload = get_current_license_payload()
        self.demo_mode = is_demo_license(self.license_payload)
        
        
        # main vertical layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignTop)
        self.catalog_sections = []

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Reports", objectName="SectionTitle")
        
        duration_combo = QComboBox()
        duration_combo.addItems(['Today', 'Past Week', 'Past Month', 'Past Year', 'All'])
        self.current_duration_key = "today"
        
        duration_combo.currentIndexChanged.connect(self.on_duration_changed)
        
        
        duration_combo.setCursor(Qt.PointingHandCursor)
        duration_combo.setFixedWidth(200)
        
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(duration_combo)
        
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
        self.layout.addSpacing(6)

        if self.demo_mode:
            demo_banner = QFrame()
            demo_banner.setStyleSheet("""
                QFrame {
                    background-color: #FFF7E6;
                    border: 1px solid #E7B65C;
                    border-radius: 10px;
                }
            """)
            demo_banner_layout = QHBoxLayout(demo_banner)
            demo_banner_layout.setContentsMargins(12, 8, 12, 8)
            demo_banner_layout.setSpacing(8)

            demo_label = QLabel(
                "Demo Mode: Reports can be explored fully, but export and print actions are disabled until a full license is installed."
            )
            demo_label.setWordWrap(True)
            demo_label.setStyleSheet("color: #8A5A12; font-size: 11px; font-weight: 600; padding-left: 0;")
            demo_banner_layout.addWidget(demo_label)
            self.layout.addWidget(demo_banner)
            self.layout.addSpacing(4)

        report_catalog = self.create_report_category_cards()
        self.layout.addWidget(report_catalog)
        
        
        
        
        
        self.setStyleSheet(load_stylesheets())
        
       


    def create_reports_section(self, title, content_widget, subtitle="", expanded=True):
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(6)

        header_widget = QFrame()
        header_widget.setCursor(Qt.PointingHandCursor)
        header_widget.setStyleSheet("QFrame:hover { background-color: #F2F6FA; border-radius: 4px; }")

        header_row = QHBoxLayout(header_widget)
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #223746; padding-left: 0;")
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        header_row.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("font-size: 11px; font-weight: 500; color: #5A7183; padding-left: 0;")
            subtitle_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            header_row.addWidget(subtitle_label)

        header_row.addStretch()

        toggle_btn = QToolButton()
        toggle_btn.setCursor(Qt.PointingHandCursor)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(expanded)
        toggle_btn.setAutoRaise(True)
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setStyleSheet("color: #2F5D7C; border: none;")

        def set_section_state(is_expanded):
            content_widget.setVisible(is_expanded)
            toggle_btn.setArrowType(Qt.DownArrow if is_expanded else Qt.RightArrow)
            toggle_btn.setToolTip("Collapse section" if is_expanded else "Expand section")

        def on_header_click(event):
            if event.button() == Qt.LeftButton:
                toggle_btn.toggle()
            event.accept()

        toggle_btn.toggled.connect(set_section_state)
        set_section_state(expanded)
        header_row.addWidget(toggle_btn)
        header_widget.mousePressEvent = on_header_click

        section_layout.addWidget(header_widget)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("border: none; border-top: 1px solid #D3DDE6;")
        section_layout.addWidget(divider)

        section_layout.addWidget(content_widget)

        return section

    def bind_catalog_section_toggle(self, header, toggle_btn, details, expanded=False):
        details.setVisible(expanded)
        toggle_btn.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.catalog_sections.append((toggle_btn, details))

        if expanded:
            self.collapse_other_catalog_sections(details)

        def toggle_details(*_):
            will_expand = not details.isVisible()
            if will_expand:
                self.collapse_other_catalog_sections(details)
            details.setVisible(will_expand)
            toggle_btn.setArrowType(Qt.DownArrow if will_expand else Qt.RightArrow)

        def on_header_click(event):
            if event.button() == Qt.LeftButton:
                toggle_details()
            event.accept()

        header.mousePressEvent = on_header_click
        toggle_btn.clicked.connect(toggle_details)

    def collapse_other_catalog_sections(self, active_details):
        for other_toggle, other_details in self.catalog_sections:
            if other_details is active_details:
                continue
            other_details.setVisible(False)
            other_toggle.setArrowType(Qt.RightArrow)

    def create_report_category_cards(self):
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        outer_layout = QVBoxLayout(container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(10)

        outer_layout.addWidget(self.create_overview_report_catalog_card())

        columns_row = QHBoxLayout()
        columns_row.setContentsMargins(0, 0, 0, 0)
        columns_row.setSpacing(10)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(10)
        left_col.addWidget(self.create_financial_report_catalog_card())
        left_col.addWidget(self.create_inventory_report_catalog_card())
        left_col.addStretch()

        mid_col = QVBoxLayout()
        mid_col.setContentsMargins(0, 0, 0, 0)
        mid_col.setSpacing(10)
        mid_col.addWidget(self.create_sales_report_catalog_card())
        mid_col.addWidget(self.create_dues_report_catalog_card())
        mid_col.addStretch()

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(10)
        right_col.addWidget(self.create_purchase_report_catalog_card())
        right_col.addWidget(self.create_audit_report_catalog_card())
        right_col.addStretch()

        columns_row.addLayout(left_col, 1)
        columns_row.addLayout(mid_col, 1)
        columns_row.addLayout(right_col, 1)

        outer_layout.addLayout(columns_row)

        return container

    def create_overview_report_catalog_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        header = QFrame()
        header.setStyleSheet("QFrame { background-color: #325D7B; border: 1px solid #284B63; border-radius: 6px; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(8)

        title = QLabel("Overview Reports")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; padding-left: 0;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        metrics_row = QHBoxLayout()
        metrics_row.setContentsMargins(0, 2, 0, 0)
        metrics_row.setSpacing(6)

        metrics_row.addWidget(self.create_embedded_overview_metric_card("Total Sales", "catalog_sales_card_data"), 1)

        vdiv1 = QFrame()
        vdiv1.setFrameShape(QFrame.VLine)
        vdiv1.setFixedWidth(1)
        vdiv1.setStyleSheet("border: none; border-left: 1px solid #C4D1DC;")
        metrics_row.addWidget(vdiv1)

        metrics_row.addWidget(self.create_embedded_overview_metric_card("Purchase Info", "catalog_purchase_card_data"), 1)

        vdiv2 = QFrame()
        vdiv2.setFrameShape(QFrame.VLine)
        vdiv2.setFixedWidth(1)
        vdiv2.setStyleSheet("border: none; border-left: 1px solid #C4D1DC;")
        metrics_row.addWidget(vdiv2)

        metrics_row.addWidget(self.create_embedded_overview_metric_card("Expenses", "catalog_expense_card_data"), 1)

        layout.addLayout(metrics_row)

        return card

    def create_embedded_overview_metric_card(self, title_text, value_attr_name):
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 3, 10, 3)
        layout.setSpacing(4)

        title = QLabel(title_text)
        title.setStyleSheet(self.summary_card_title_style())

        value_label = QLabel("0.00")
        value_label.setStyleSheet(self.summary_card_value_style())
        setattr(self, value_attr_name, value_label)

        layout.addWidget(title)
        layout.addWidget(value_label)

        return widget

    def create_financial_report_catalog_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        card.setMinimumHeight(96)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        rows = [
            "Profit & Loss",
            "Balance Sheet",
            "Trial Balance",
            "Cash Flow",
        ]

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header = QFrame()
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet("QFrame { background-color: #325D7B; border: 1px solid #284B63; border-radius: 6px; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(6)

        title = QLabel("Financial Reports")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; padding-left: 0;")
        title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(title)
        header_layout.addStretch()

        toggle_btn = QToolButton()
        toggle_btn.setArrowType(Qt.DownArrow)
        toggle_btn.setStyleSheet("QToolButton { border: none; padding: 0; color: #FFFFFF; background: transparent; }")
        toggle_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(toggle_btn)

        layout.addWidget(header)

        subtitle = QLabel("Profitability, statements, ledger, and cash movement reports.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #5A7183; font-size: 11px; font-weight: 500; padding-left: 0;")
        layout.addWidget(subtitle)

        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        for report_name in rows:
            details_layout.addLayout(
                self.create_financial_report_row(
                    report_name,
                    self.get_financial_report_handler(report_name),
                )
            )

        layout.addWidget(details)
        self.bind_catalog_section_toggle(header, toggle_btn, details, expanded=False)

        return card

    def get_financial_report_handler(self, report_name):
        handler_map = {
            "Profit & Loss": self.show_profit_and_loss_dialog,
            "Balance Sheet": self.show_balance_sheet_dialog,
            "Trial Balance": self.show_trial_balance_dialog,
            "Cash Flow": self.show_cash_flow_dialog,
        }
        return handler_map.get(report_name)

    def get_sales_report_handler(self, report_name):
        handler_map = {
            "Sales Summary": self.show_sales_summary_report_dialog,
            "Sales by Product": self.show_sales_by_product_report_dialog,
            "Sales by Customer": self.show_sales_by_customer_report_dialog,
            "Sales by Sales Rep": self.show_sales_by_sales_rep_report_dialog,
            "Sales Return Report": self.show_sales_return_report_dialog,
            "Receipt List": self.show_receipt_list_report_dialog,
            "Profit by Sale": self.show_profit_by_sale_report_dialog,
            "Daily Sales Register": self.show_daily_sales_register_dialog,
        }
        return handler_map.get(report_name)

    def get_purchase_report_handler(self, report_name):
        handler_map = {
            "Purchase Summary": self.show_purchase_summary_report_dialog,
            "Purchase by Supplier": self.show_purchase_by_supplier_report_dialog,
            "Purchase by Product": self.show_purchase_by_product_report_dialog,
            "PO Status Report": self.show_po_status_report_dialog,
            "Partial Receipt Analytics": self.show_partial_receipt_analytics_report_dialog,
            "GRN Status Report": self.show_grn_status_report_dialog,
            "Purchase Return Report": self.show_purchase_return_report_dialog,
            "Supplier Payment Summary": self.show_supplier_payment_summary_report_dialog,
            "Purchase vs Sales Comparison": self.show_purchase_vs_sales_comparison_report_dialog,
        }
        return handler_map.get(report_name)

    def get_inventory_report_handler(self, report_name):
        handler_map = {
            "Stock Valuation Report": self.show_stock_valuation_report_dialog,
            "Stock Movement Report": self.show_stock_movement_dialog,
            "Near Expiry Report": self.show_near_expiry_dialog,
            "Expired Stock Report": self.show_expired_stock_report_dialog,
            "Low Stock / Reorder Report": self.show_low_stock_dialog,
            "Non-Moving / Dead Stock": self.show_dead_nonmoving_stock_dialog,
            "Batch Traceability Report": self.show_batch_traceability_report_dialog,
            "Inventory Adjustment Log": self.show_inventory_adjustment_log_dialog,
            "Opening Stock Cost Review": self.show_opening_stock_cost_review_dialog,
        }
        return handler_map.get(report_name)

    def get_dues_report_handler(self, report_name):
        handler_map = {
            "Customer Outstanding": self.show_customer_outstanding_report_dialog,
            "Supplier Outstanding": self.show_supplier_outstanding_report_dialog,
            "Customer Aging Report": self.show_receivable_aging_dialog,
            "Supplier Aging Report": self.show_supplier_payable_aging_dialog,
            "Collection Forecast": self.show_receivable_forecast_dialog,
            "Payment Forecast": self.show_supplier_payable_forecast_dialog,
            "Overdue Recovery List": self.show_overdue_recovery_report_dialog,
            "Credit Limit Utilization": self.show_credit_limit_utilization_dialog,
        }
        return handler_map.get(report_name)

    def get_audit_report_handler(self, report_name):
        handler_map = {
            "User Activity Log": self.show_activity_log_dialog,
            "Price Change History": self.show_price_change_history_dialog,
            "Stock Adjustment Log": self.show_inventory_adjustment_log_dialog,
            "Discount & Override Report": self.show_discount_override_report_dialog,
            "Deleted Transactions Log": self.show_deleted_transactions_log_dialog,
            "Login / Session Log": self.show_login_session_log_dialog,
            "Shift Closing Summary": self.show_shift_closing_summary_dialog,
            "System Change Audit": self.show_system_change_audit_dialog,
        }
        return handler_map.get(report_name)

    def create_financial_report_row(self, report_name, open_handler=None):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        label = QLabel(report_name)
        label.setStyleSheet("color: #223746; font-size: 13px; font-weight: 600; padding-left: 0;")

        open_btn = QPushButton("Open")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setStyleSheet(self.report_action_btn_style())
        if open_handler is not None:
            open_btn.clicked.connect(open_handler)
        else:
            open_btn.setEnabled(False)
            open_btn.setToolTip("This report is planned and will be added next.")

        row.addWidget(label, 1)
        row.addWidget(open_btn, 0)

        return row

    def show_sales_table_report_dialog(self, title, description, columns, fetch_rows, summary_builder=None, note_text="", row_double_click_handler=None):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(980, 620)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        header_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        header_row.addWidget(title_label)
        header_row.addStretch()
        header_row.addWidget(QLabel("Period:"))
        period_combo = self.build_report_period_combo(self.current_duration_key)
        header_row.addWidget(period_combo)
        header_layout.addLayout(header_row)

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        header_layout.addWidget(desc)

        if note_text:
            note = QLabel(note_text)
            note.setWordWrap(True)
            note.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
            header_layout.addWidget(note)

        table = QTableWidget()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([col[0] for col in columns])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        if row_double_click_handler is not None:
            table.setCursor(Qt.PointingHandCursor)
        for idx in range(len(columns)):
            mode = QHeaderView.ResizeToContents if idx > 0 else QHeaderView.Stretch
            if idx == 0:
                mode = QHeaderView.Stretch
            table.horizontalHeader().setSectionResizeMode(idx, mode)
        content_layout.addWidget(table)

        hint_label = None
        if row_double_click_handler is not None:
            hint_label = QLabel("Double-click a row to open related detail.")
            hint_label.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
            content_layout.addWidget(hint_label)

        summary_label = QLabel("")
        summary_label.setStyleSheet("font-weight: 600; color: #223746;")
        content_layout.addWidget(summary_label)

        export_btn = QPushButton("Export TXT")
        export_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_btn.setStyleSheet(self.report_action_btn_style())
        export_btn.setMinimumHeight(34)
        footer_layout.addWidget(export_btn)

        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_pdf_btn.setStyleSheet(self.report_action_btn_style())
        export_pdf_btn.setMinimumHeight(34)
        footer_layout.addWidget(export_pdf_btn)

        print_btn = QPushButton("Print")
        print_btn.setCursor(QCursor(Qt.PointingHandCursor))
        print_btn.setStyleSheet(self.report_action_btn_style())
        print_btn.setMinimumHeight(34)
        footer_layout.addWidget(print_btn)

        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)

        state = {"export_text": "", "rows": []}

        def as_display(value):
            if isinstance(value, float):
                return f"{value:,.2f}"
            return str(value)

        def rebuild():
            duration_key = period_combo.currentData()
            rows = fetch_rows(duration_key) or []
            state["rows"] = rows
            table.setSortingEnabled(False)
            table.setRowCount(len(rows))

            for r, row in enumerate(rows):
                for c, (_header, key) in enumerate(columns):
                    item = QTableWidgetItem(as_display(row.get(key, "")))
                    if isinstance(row.get(key), (int, float)) and c > 0:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if c == 0:
                        item.setData(Qt.UserRole, row)
                    table.setItem(r, c, item)

            table.setSortingEnabled(True)
            if rows:
                table.sortItems(0, Qt.AscendingOrder)

            if summary_builder is not None:
                summary_label.setText(summary_builder(rows))
            else:
                summary_label.setText(f"Rows: {len(rows)}")

            sections = [
                {
                    "title": "Rows",
                    "lines": [
                        " | ".join(f"{header}: {as_display(row.get(key, ''))}" for header, key in columns)
                        for row in rows
                    ] or ["No rows found for selected period."],
                }
            ]
            state["export_text"] = self.build_report_text(
                title,
                meta_lines=[f"Period: {self.get_duration_label(duration_key)}"],
                sections=sections,
            )

        def on_row_double_click(row_index, _col):
            if row_double_click_handler is None:
                return
            first_item = table.item(row_index, 0)
            if first_item is None:
                return
            row_data = first_item.data(Qt.UserRole)
            if not isinstance(row_data, dict):
                return
            row_double_click_handler(row_data)

        period_combo.currentIndexChanged.connect(lambda _: rebuild())
        export_btn.clicked.connect(lambda: self.export_report_text(title.lower().replace(" ", "_"), title, state["export_text"]))
        export_pdf_btn.clicked.connect(lambda: self.export_report_pdf(title.lower().replace(" ", "_"), title, state["export_text"]))
        print_btn.clicked.connect(lambda: self.print_report_text(title, state["export_text"]))
        if row_double_click_handler is not None:
            table.cellDoubleClicked.connect(on_row_double_click)
        rebuild()
        dialog.exec()

    def show_profit_and_loss_dialog(self):
        from PySide6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QFrame,
            QGridLayout,
            QPushButton,
            QWidget,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Profit & Loss")
        dialog.setMinimumSize(860, 520)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        header_row = QHBoxLayout()
        title = QLabel("Profit & Loss")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        header_row.addWidget(title)
        header_row.addStretch()

        header_row.addWidget(QLabel("Period:"))
        period_combo = self.build_report_period_combo(self.current_duration_key)
        header_row.addWidget(period_combo)

        period_label = QLabel("")
        period_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #5A7183;")
        header_row.addWidget(period_label)
        header_layout.addLayout(header_row)

        subtitle = QLabel(
            "Known-cost sales contribute to profit. Revenue from items with unknown cost is shown separately until cost is assigned."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        header_layout.addWidget(subtitle)

        summary_card = QFrame()
        summary_card.setStyleSheet(self.report_card_style())
        summary_layout = QGridLayout(summary_card)
        summary_layout.setContentsMargins(14, 12, 14, 12)
        summary_layout.setHorizontalSpacing(22)
        summary_layout.setVerticalSpacing(10)

        def add_summary_metric(row, col, label_text):
            label = QLabel(label_text)
            label.setStyleSheet(self.compact_metric_label_style())
            value = QLabel("0.00")
            value.setStyleSheet(self.compact_metric_value_style())
            block = QVBoxLayout()
            block.setContentsMargins(0, 0, 0, 0)
            block.setSpacing(2)
            block.addWidget(label)
            block.addWidget(value)
            summary_layout.addLayout(block, row, col)
            return value

        positive_style = "color: #2e7d32; font-size: 18px; font-weight: 700; padding-left: 0;"
        negative_style = "color: #c62828; font-size: 18px; font-weight: 700; padding-left: 0;"

        total_revenue_value = add_summary_metric(0, 0, "Total Revenue")
        known_revenue_value = add_summary_metric(0, 1, "Known Revenue")
        unknown_revenue_value = add_summary_metric(0, 2, "Revenue With Unknown Cost")
        known_profit_value = add_summary_metric(1, 0, "Known Gross Profit")
        net_profit_value = add_summary_metric(1, 1, "Net Known Profit")
        coverage_value = add_summary_metric(1, 2, "Known Cost Coverage %")
        content_layout.addWidget(summary_card)

        statement_card = QFrame()
        statement_card.setStyleSheet(self.report_card_style())
        statement_layout = QVBoxLayout(statement_card)
        statement_layout.setContentsMargins(14, 12, 14, 12)
        statement_layout.setSpacing(8)

        statement_title = QLabel("Statement View")
        statement_title.setStyleSheet(self.stock_card_subtitle_style())
        statement_layout.addWidget(statement_title)

        statement_grid = QGridLayout()
        statement_grid.setHorizontalSpacing(18)
        statement_grid.setVerticalSpacing(8)
        statement_grid.setColumnStretch(0, 1)
        statement_grid.setColumnStretch(1, 0)

        statement_values = {}

        def add_statement_line(row, label_text, emphasize=False, positive_negative=False):
            label = QLabel(label_text)
            label.setMinimumHeight(30)
            label.setContentsMargins(10, 4, 10, 4)
            label.setStyleSheet(
                "QLabel {"
                " color: #223746; font-size: 13px; font-weight: 600; padding-left: 0;"
                " background-color: #EEF4F8; border: 1px solid #D3DDE6; border-radius: 8px;"
                "}"
            )
            value_label = QLabel("0.00")
            value_label.setMinimumHeight(30)
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setContentsMargins(10, 4, 10, 4)
            value_label.setStyleSheet(
                "QLabel {"
                " color: #223746; font-size: 14px; font-weight: 700; padding-left: 0;"
                " background-color: #EEF4F8; border: 1px solid #D3DDE6; border-radius: 8px;"
                "}"
            )
            statement_grid.addWidget(label, row, 0)
            statement_grid.addWidget(value_label, row, 1)
            statement_values[label_text] = (value_label, emphasize, positive_negative)

        add_statement_line(0, "Known Revenue")
        add_statement_line(1, "Less: Known COGS")
        add_statement_line(2, "Known Gross Profit", emphasize=True, positive_negative=True)
        add_statement_line(3, "Less: Operating Expenses")
        add_statement_line(4, "Net Known Profit", emphasize=True, positive_negative=True)
        add_statement_line(5, "Revenue With Unknown Cost")
        add_statement_line(6, "Gross Margin %")
        add_statement_line(7, "Net Margin %")

        statement_layout.addLayout(statement_grid)
        content_layout.addWidget(statement_card)

        note_card = QFrame()
        note_card.setStyleSheet(self.report_card_style())
        note_layout = QVBoxLayout(note_card)
        note_layout.setContentsMargins(14, 12, 14, 12)
        note_layout.setSpacing(6)

        note_title = QLabel("Interpretation")
        note_title.setStyleSheet(self.stock_card_subtitle_style())
        note_layout.addWidget(note_title)

        note_labels = []
        for _ in range(3):
            label = QLabel("")
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
            note_layout.addWidget(label)
            note_labels.append(label)

        content_layout.addWidget(note_card)

        export_btn = QPushButton("Export TXT")
        export_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_btn.setStyleSheet(self.report_action_btn_style())
        export_btn.setMinimumHeight(34)
        footer_layout.addWidget(export_btn)

        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_pdf_btn.setStyleSheet(self.report_action_btn_style())
        export_pdf_btn.setMinimumHeight(34)
        footer_layout.addWidget(export_pdf_btn)

        print_btn = QPushButton("Print")
        print_btn.setCursor(QCursor(Qt.PointingHandCursor))
        print_btn.setStyleSheet(self.report_action_btn_style())
        print_btn.setMinimumHeight(34)
        footer_layout.addWidget(print_btn)

        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)

        state = {"duration_key": period_combo.currentData(), "export_text": ""}

        def set_statement_value(label_text, value_text):
            value_label, emphasize, positive_negative = statement_values[label_text]
            if positive_negative:
                tone = "#c62828" if value_text.startswith("-") else "#2e7d32"
                value_style = (
                    "QLabel {"
                    f" color: {tone}; font-size: 18px; font-weight: 700; padding-left: 0;"
                    " background-color: #EEF4F8; border: 1px solid #D3DDE6; border-radius: 8px;"
                    "}"
                )
            elif emphasize:
                value_style = (
                    "QLabel {"
                    " color: #223746; font-size: 18px; font-weight: 700; padding-left: 0;"
                    " background-color: #EEF4F8; border: 1px solid #D3DDE6; border-radius: 8px;"
                    "}"
                )
            else:
                value_style = (
                    "QLabel {"
                    " color: #223746; font-size: 14px; font-weight: 700; padding-left: 0;"
                    " background-color: #EEF4F8; border: 1px solid #D3DDE6; border-radius: 8px;"
                    "}"
                )
            value_label.setStyleSheet(value_style)
            value_label.setText(value_text)

        def rebuild():
            duration_key = period_combo.currentData()
            state["duration_key"] = duration_key
            period_label.setText(f"Selected: {self.get_duration_label(duration_key)}")

            snapshot = report_service.ReportService().get_profit_loss_snapshot(duration_key)
            revenue_known = snapshot["revenue_known"]
            total_cogs = snapshot["total_cogs"]
            gross_profit = snapshot["gross_profit"]
            revenue_unknown = snapshot["revenue_unknown"]
            gross_margin_pct = snapshot["gross_margin_pct"]
            coverage_pct = snapshot["coverage_pct"]
            total_expenses = snapshot["total_expenses"]
            expense_count = snapshot["expense_count"]
            total_revenue = snapshot["total_revenue"]
            net_profit = snapshot["net_profit"]
            net_margin_pct = snapshot["net_margin_pct"]

            total_revenue_value.setText(f"{total_revenue:,.2f}")
            known_revenue_value.setText(f"{revenue_known:,.2f}")
            unknown_revenue_value.setText(f"{revenue_unknown:,.2f}")
            known_profit_value.setText(f"{gross_profit:,.2f}")
            net_profit_value.setText(f"{net_profit:,.2f}")
            coverage_value.setText(f"{coverage_pct:.2f}%")
            known_profit_value.setStyleSheet(negative_style if gross_profit < 0 else positive_style)
            net_profit_value.setStyleSheet(negative_style if net_profit < 0 else positive_style)

            set_statement_value("Known Revenue", f"{revenue_known:,.2f}")
            set_statement_value("Less: Known COGS", f"{total_cogs:,.2f}")
            set_statement_value("Known Gross Profit", f"{gross_profit:,.2f}")
            set_statement_value("Less: Operating Expenses", f"{total_expenses:,.2f}")
            set_statement_value("Net Known Profit", f"{net_profit:,.2f}")
            set_statement_value("Revenue With Unknown Cost", f"{revenue_unknown:,.2f}")
            set_statement_value("Gross Margin %", f"{gross_margin_pct:.2f}%")
            set_statement_value("Net Margin %", f"{net_margin_pct:.2f}%")

            for label_widget, note_text in zip(note_labels, snapshot["notes"]):
                label_widget.setText(note_text)

            state["export_text"] = self.build_report_text(
                "Profit & Loss",
                meta_lines=[f"Period: {self.get_duration_label(duration_key)}"],
                sections=[
                    {
                        "title": "Summary",
                        "lines": [
                            ("Total Revenue", f"{total_revenue:,.2f}"),
                            ("Known Revenue", f"{revenue_known:,.2f}"),
                            ("Revenue With Unknown Cost", f"{revenue_unknown:,.2f}"),
                            ("Known Gross Profit", f"{gross_profit:,.2f}"),
                            ("Operating Expenses", f"{total_expenses:,.2f}"),
                            ("Net Known Profit", f"{net_profit:,.2f}"),
                            ("Gross Margin %", f"{gross_margin_pct:.2f}%"),
                            ("Net Margin %", f"{net_margin_pct:.2f}%"),
                            ("Known Cost Coverage %", f"{coverage_pct:.2f}%"),
                        ],
                    },
                    {
                        "title": "Notes",
                        "lines": [
                            "Known Gross Profit uses only sale lines where all consumed stock had a known cost.",
                            "Revenue With Unknown Cost is excluded from profit until opening stock or batch cost is assigned.",
                            f"Expense records in period: {expense_count}",
                        ],
                    },
                ],
            )

        period_combo.currentIndexChanged.connect(lambda _: rebuild())
        export_btn.clicked.connect(lambda: self.export_report_text("profit_and_loss", "Profit & Loss", state["export_text"]))
        export_pdf_btn.clicked.connect(lambda: self.export_report_pdf("profit_and_loss", "Profit & Loss", state["export_text"]))
        print_btn.clicked.connect(lambda: self.print_report_text("Profit & Loss", state["export_text"]))
        rebuild()

        dialog.exec()

    def show_balance_sheet_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QPushButton

        service = report_service.ReportService()
        snapshot = service.get_balance_sheet_snapshot()
        inventory = snapshot["inventory"]
        session_cash = snapshot["session_cash"]
        opening_estimate = snapshot["opening_estimate_amount"]
        supplier_payable = snapshot["supplier_payable"]
        supplier_receiveable = snapshot["supplier_receiveable"]
        customer_receivable = snapshot["customer_receivable"]
        customer_payable = snapshot["customer_payable"]
        known_current_assets = snapshot["known_current_assets"]
        current_liabilities = snapshot["current_liabilities"]
        working_capital = snapshot["working_capital"]

        dialog = QDialog(self)
        dialog.setWindowTitle("Balance Sheet")
        dialog.setMinimumSize(920, 560)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        header_row = QHBoxLayout()
        title = QLabel("Balance Sheet")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        header_row.addWidget(title)
        header_row.addStretch()

        period_label = QLabel("As of now")
        period_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #5A7183;")
        header_row.addWidget(period_label)
        header_layout.addLayout(header_row)

        subtitle = QLabel(
            "Management snapshot based on current stock, dues, and session cash. Unknown-cost inventory is shown separately until cost is assigned."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        header_layout.addWidget(subtitle)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        assets_card = QFrame()
        assets_card.setStyleSheet(self.report_card_style())
        assets_layout = QVBoxLayout(assets_card)
        assets_layout.setContentsMargins(14, 12, 14, 12)
        assets_layout.setSpacing(8)

        assets_title = QLabel("Current Assets")
        assets_title.setStyleSheet(self.stock_card_subtitle_style())
        assets_layout.addWidget(assets_title)

        assets_grid = QGridLayout()
        assets_grid.setHorizontalSpacing(18)
        assets_grid.setVerticalSpacing(8)
        assets_grid.setColumnStretch(0, 1)
        assets_grid.setColumnStretch(1, 0)

        def add_line(grid, row, label_text, value_text, emphasize=False, positive_negative=False):
            label = QLabel(label_text)
            label.setStyleSheet("color: #223746; font-size: 13px; font-weight: 600; padding-left: 0;")
            value = QLabel(value_text)
            if positive_negative:
                value.setStyleSheet(
                    "color: #c62828; font-size: 18px; font-weight: 700; padding-left: 0;"
                    if value_text.startswith("-")
                    else "color: #2e7d32; font-size: 18px; font-weight: 700; padding-left: 0;"
                )
            elif emphasize:
                value.setStyleSheet("color: #223746; font-size: 18px; font-weight: 700; padding-left: 0;")
            else:
                value.setStyleSheet("color: #223746; font-size: 14px; font-weight: 700; padding-left: 0;")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(label, row, 0)
            grid.addWidget(value, row, 1)

        cash_label = session_cash.get("label", "Cash on Hand")
        session_date = session_cash.get("session_date") or "N/A"
        add_line(assets_grid, 0, f"{cash_label} ({session_date})", f"{float(session_cash.get('cash_value', 0.0) or 0.0):,.2f}")
        add_line(assets_grid, 1, "Customer Receivables", f"{float(customer_receivable or 0.0):,.2f}")
        add_line(assets_grid, 2, "Supplier Receivables / Advances", f"{float(supplier_receiveable or 0.0):,.2f}")
        add_line(assets_grid, 3, "Inventory at Known Cost", f"{float(inventory.get('known_inventory_value', 0.0) or 0.0):,.2f}")
        add_line(assets_grid, 4, "Known Current Assets", f"{known_current_assets:,.2f}", emphasize=True)
        assets_layout.addLayout(assets_grid)

        liabilities_card = QFrame()
        liabilities_card.setStyleSheet(self.report_card_style())
        liabilities_layout = QVBoxLayout(liabilities_card)
        liabilities_layout.setContentsMargins(14, 12, 14, 12)
        liabilities_layout.setSpacing(8)

        liabilities_title = QLabel("Current Liabilities")
        liabilities_title.setStyleSheet(self.stock_card_subtitle_style())
        liabilities_layout.addWidget(liabilities_title)

        liabilities_grid = QGridLayout()
        liabilities_grid.setHorizontalSpacing(18)
        liabilities_grid.setVerticalSpacing(8)
        liabilities_grid.setColumnStretch(0, 1)
        liabilities_grid.setColumnStretch(1, 0)

        add_line(liabilities_grid, 0, "Supplier Payables", f"{float(supplier_payable or 0.0):,.2f}")
        add_line(liabilities_grid, 1, "Customer Payables / Advances", f"{float(customer_payable or 0.0):,.2f}")
        add_line(liabilities_grid, 2, "Current Liabilities", f"{current_liabilities:,.2f}", emphasize=True)
        add_line(liabilities_grid, 3, "Working Capital", f"{working_capital:,.2f}", emphasize=True, positive_negative=True)
        liabilities_layout.addLayout(liabilities_grid)

        top_row.addWidget(assets_card, 1)
        top_row.addWidget(liabilities_card, 1)
        content_layout.addLayout(top_row)

        note_card = QFrame()
        note_card.setStyleSheet(self.report_card_style())
        note_layout = QVBoxLayout(note_card)
        note_layout.setContentsMargins(14, 12, 14, 12)
        note_layout.setSpacing(8)

        note_title = QLabel("Known vs Unknown Inventory")
        note_title.setStyleSheet(self.stock_card_subtitle_style())
        note_layout.addWidget(note_title)

        note_grid = QGridLayout()
        note_grid.setHorizontalSpacing(18)
        note_grid.setVerticalSpacing(8)
        note_grid.setColumnStretch(0, 1)
        note_grid.setColumnStretch(1, 0)

        add_line(note_grid, 0, "Inventory Units on Hand", f"{float(inventory.get('total_units', 0.0) or 0.0):,.2f}")
        add_line(note_grid, 1, "Units With Unknown Cost", f"{float(inventory.get('unknown_cost_units', 0.0) or 0.0):,.2f}")
        add_line(note_grid, 2, "Batches With Unknown Cost", f"{int(inventory.get('unknown_cost_batches', 0) or 0)}")
        add_line(note_grid, 3, "Estimated Opening Inventory Cost", f"{float(opening_estimate or 0.0):,.2f}")
        note_layout.addLayout(note_grid)

        notes = [
            "Known current assets include only inventory and sales balances with supportable cost/value.",
            "Estimated Opening Inventory Cost is shown as reference only and is not forced into the balance total.",
            "If opening or batch costs are assigned later, inventory value and profitability become more complete.",
        ]
        for note in notes:
            label = QLabel(note)
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
            note_layout.addWidget(label)

        content_layout.addWidget(note_card)

        balance_text = self.build_report_text(
            "Balance Sheet",
            meta_lines=["As of now"],
            sections=[
                {
                    "title": "Current Assets",
                    "lines": [
                        (f"{cash_label} ({session_date})", f"{float(session_cash.get('cash_value', 0.0) or 0.0):,.2f}"),
                        ("Customer Receivables", f"{float(customer_receivable or 0.0):,.2f}"),
                        ("Supplier Receivables / Advances", f"{float(supplier_receiveable or 0.0):,.2f}"),
                        ("Inventory at Known Cost", f"{float(inventory.get('known_inventory_value', 0.0) or 0.0):,.2f}"),
                        ("Known Current Assets", f"{known_current_assets:,.2f}"),
                    ],
                },
                {
                    "title": "Current Liabilities",
                    "lines": [
                        ("Supplier Payables", f"{float(supplier_payable or 0.0):,.2f}"),
                        ("Customer Payables / Advances", f"{float(customer_payable or 0.0):,.2f}"),
                        ("Current Liabilities", f"{current_liabilities:,.2f}"),
                        ("Working Capital", f"{working_capital:,.2f}"),
                    ],
                },
                {
                    "title": "Known vs Unknown Inventory",
                    "lines": [
                        ("Inventory Units on Hand", f"{float(inventory.get('total_units', 0.0) or 0.0):,.2f}"),
                        ("Units With Unknown Cost", f"{float(inventory.get('unknown_cost_units', 0.0) or 0.0):,.2f}"),
                        ("Batches With Unknown Cost", f"{int(inventory.get('unknown_cost_batches', 0) or 0)}"),
                        ("Estimated Opening Inventory Cost", f"{float(opening_estimate or 0.0):,.2f}"),
                    ],
                },
            ],
        )

        export_btn = QPushButton("Export TXT")
        export_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_btn.setStyleSheet(self.report_action_btn_style())
        export_btn.clicked.connect(lambda: self.export_report_text("balance_sheet", "Balance Sheet", balance_text))
        export_btn.setMinimumHeight(34)
        footer_layout.addWidget(export_btn)

        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_pdf_btn.setStyleSheet(self.report_action_btn_style())
        export_pdf_btn.clicked.connect(lambda: self.export_report_pdf("balance_sheet", "Balance Sheet", balance_text))
        export_pdf_btn.setMinimumHeight(34)
        footer_layout.addWidget(export_pdf_btn)

        print_btn = QPushButton("Print")
        print_btn.setCursor(QCursor(Qt.PointingHandCursor))
        print_btn.setStyleSheet(self.report_action_btn_style())
        print_btn.clicked.connect(lambda: self.print_report_text("Balance Sheet", balance_text))
        print_btn.setMinimumHeight(34)
        footer_layout.addWidget(print_btn)

        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)

        dialog.exec()

    def show_trial_balance_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
        from PySide6.QtGui import QColor

        service = report_service.ReportService()
        snapshot = service.get_trial_balance_snapshot()
        inventory = snapshot["inventory"]
        rows = snapshot["rows"]
        total_debit = snapshot["total_debit"]
        total_credit = snapshot["total_credit"]

        dialog = QDialog(self)
        dialog.setWindowTitle("Trial Balance")
        dialog.setMinimumSize(920, 560)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        header_row = QHBoxLayout()
        title = QLabel("Trial Balance")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        header_row.addWidget(title)
        header_row.addStretch()
        tag = QLabel("Control-account view")
        tag.setStyleSheet("font-size: 12px; font-weight: 600; color: #5A7183;")
        header_row.addWidget(tag)
        header_layout.addLayout(header_row)

        subtitle = QLabel(
            "This is a practical ERP trial balance using tracked operational balances. A balancing figure is added because the app does not yet maintain a full general ledger."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        header_layout.addWidget(subtitle)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Account", "Debit", "Credit", "Note"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.setRowCount(len(rows) + 1)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        for r, row in enumerate(rows):
            values = [
                row["account"],
                f"{row['debit']:,.2f}" if row["debit"] else "",
                f"{row['credit']:,.2f}" if row["credit"] else "",
                row["note"],
            ]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                if c in (1, 2):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(r, c, item)

        totals_row = len(rows)
        totals = ["TOTAL", f"{total_debit:,.2f}", f"{total_credit:,.2f}", ""]
        for c, value in enumerate(totals):
            item = QTableWidgetItem(value)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setBackground(QColor("#E8EEF3"))
            if c in (1, 2):
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(totals_row, c, item)

        content_layout.addWidget(table)

        memo = QLabel(
            f"Unknown-cost inventory currently sits outside the debit total: {float(inventory.get('unknown_cost_units', 0.0) or 0.0):,.2f} unit(s) across {int(inventory.get('unknown_cost_batches', 0) or 0)} batch(es)."
        )
        memo.setWordWrap(True)
        memo.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        content_layout.addWidget(memo)

        trial_balance_text = self.build_report_text(
            "Trial Balance",
            meta_lines=["Control-account view"],
            sections=[
                {
                    "title": "Accounts",
                    "lines": [
                        f"{row['account']} | Debit: {row['debit']:,.2f} | Credit: {row['credit']:,.2f} | {row['note']}"
                        for row in rows
                    ],
                },
                {
                    "title": "Totals",
                    "lines": [
                        ("Total Debit", f"{total_debit:,.2f}"),
                        ("Total Credit", f"{total_credit:,.2f}"),
                        (
                            "Unknown-cost inventory outside debit total",
                            f"{float(inventory.get('unknown_cost_units', 0.0) or 0.0):,.2f} unit(s) across {int(inventory.get('unknown_cost_batches', 0) or 0)} batch(es)",
                        ),
                    ],
                },
            ],
        )

        export_btn = QPushButton("Export TXT")
        export_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_btn.setStyleSheet(self.report_action_btn_style())
        export_btn.clicked.connect(lambda: self.export_report_text("trial_balance", "Trial Balance", trial_balance_text))
        export_btn.setMinimumHeight(34)
        footer_layout.addWidget(export_btn)

        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_pdf_btn.setStyleSheet(self.report_action_btn_style())
        export_pdf_btn.clicked.connect(lambda: self.export_report_pdf("trial_balance", "Trial Balance", trial_balance_text))
        export_pdf_btn.setMinimumHeight(34)
        footer_layout.addWidget(export_pdf_btn)

        print_btn = QPushButton("Print")
        print_btn.setCursor(QCursor(Qt.PointingHandCursor))
        print_btn.setStyleSheet(self.report_action_btn_style())
        print_btn.clicked.connect(lambda: self.print_report_text("Trial Balance", trial_balance_text))
        print_btn.setMinimumHeight(34)
        footer_layout.addWidget(print_btn)

        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)

        dialog.exec()

    def show_cash_flow_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QPushButton
        service = report_service.ReportService()

        dialog = QDialog(self)
        dialog.setWindowTitle("Cash Flow")
        dialog.setMinimumSize(900, 560)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        header_row = QHBoxLayout()
        title = QLabel("Cash Flow")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(QLabel("Period:"))
        period_combo = self.build_report_period_combo(self.current_duration_key)
        header_row.addWidget(period_combo)
        period_label = QLabel("")
        period_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #5A7183;")
        header_row.addWidget(period_label)
        header_layout.addLayout(header_row)

        subtitle = QLabel(
            "Operational cash movement based on cash receipts, cash payments, and cash expenses for the selected period."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        header_layout.addWidget(subtitle)

        row = QHBoxLayout()
        row.setSpacing(10)

        inflow_card = QFrame()
        inflow_card.setStyleSheet(self.report_card_style())
        inflow_layout = QVBoxLayout(inflow_card)
        inflow_layout.setContentsMargins(14, 12, 14, 12)
        inflow_layout.setSpacing(8)
        inflow_title = QLabel("Cash Inflows")
        inflow_title.setStyleSheet(self.stock_card_subtitle_style())
        inflow_layout.addWidget(inflow_title)

        inflow_grid = QGridLayout()
        inflow_grid.setHorizontalSpacing(18)
        inflow_grid.setVerticalSpacing(8)
        inflow_grid.setColumnStretch(0, 1)
        inflow_grid.setColumnStretch(1, 0)

        def add_line(grid, row_index, label_text, emphasize=False, positive_negative=False):
            label = QLabel(label_text)
            label.setStyleSheet("color: #223746; font-size: 13px; font-weight: 600; padding-left: 0;")
            value = QLabel("0.00")
            value.setStyleSheet("color: #223746; font-size: 14px; font-weight: 700; padding-left: 0;")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(label, row_index, 0)
            grid.addWidget(value, row_index, 1)
            return value, emphasize, positive_negative

        inflow_customer_value, _, _ = add_line(inflow_grid, 0, "Cash Received From Customers")
        inflow_supplier_value, _, _ = add_line(inflow_grid, 1, "Cash Received From Suppliers")
        inflow_total_value, _, _ = add_line(inflow_grid, 2, "Total Cash Inflows", emphasize=True)
        inflow_layout.addLayout(inflow_grid)

        outflow_card = QFrame()
        outflow_card.setStyleSheet(self.report_card_style())
        outflow_layout = QVBoxLayout(outflow_card)
        outflow_layout.setContentsMargins(14, 12, 14, 12)
        outflow_layout.setSpacing(8)
        outflow_title = QLabel("Cash Outflows")
        outflow_title.setStyleSheet(self.stock_card_subtitle_style())
        outflow_layout.addWidget(outflow_title)

        outflow_grid = QGridLayout()
        outflow_grid.setHorizontalSpacing(18)
        outflow_grid.setVerticalSpacing(8)
        outflow_grid.setColumnStretch(0, 1)
        outflow_grid.setColumnStretch(1, 0)

        outflow_supplier_value, _, _ = add_line(outflow_grid, 0, "Cash Paid To Suppliers")
        outflow_customer_value, _, _ = add_line(outflow_grid, 1, "Cash Paid To Customers")
        outflow_expense_value, _, _ = add_line(outflow_grid, 2, "Cash Expenses")
        outflow_total_value, _, _ = add_line(outflow_grid, 3, "Total Cash Outflows", emphasize=True)
        outflow_layout.addLayout(outflow_grid)

        row.addWidget(inflow_card, 1)
        row.addWidget(outflow_card, 1)
        content_layout.addLayout(row)

        summary_card = QFrame()
        summary_card.setStyleSheet(self.report_card_style())
        summary_layout = QGridLayout(summary_card)
        summary_layout.setContentsMargins(14, 12, 14, 12)
        summary_layout.setHorizontalSpacing(18)
        summary_layout.setVerticalSpacing(8)
        summary_layout.setColumnStretch(0, 1)
        summary_layout.setColumnStretch(1, 0)

        net_cash_value, _, _ = add_line(summary_layout, 0, "Net Cash Movement", emphasize=True, positive_negative=True)
        session_cash_label_widget = QLabel("Latest Session Cash")
        session_cash_label_widget.setStyleSheet("color: #223746; font-size: 13px; font-weight: 600; padding-left: 0;")
        session_cash_value = QLabel("0.00")
        session_cash_value.setStyleSheet("color: #223746; font-size: 14px; font-weight: 700; padding-left: 0;")
        session_cash_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        summary_layout.addWidget(session_cash_label_widget, 1, 0)
        summary_layout.addWidget(session_cash_value, 1, 1)
        content_layout.addWidget(summary_card)

        note_card = QFrame()
        note_card.setStyleSheet(self.report_card_style())
        note_layout = QVBoxLayout(note_card)
        note_layout.setContentsMargins(14, 12, 14, 12)
        note_layout.setSpacing(6)

        note_title = QLabel("Interpretation")
        note_title.setStyleSheet(self.stock_card_subtitle_style())
        note_layout.addWidget(note_title)

        note_labels = []
        for _ in range(3):
            label = QLabel("")
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
            note_layout.addWidget(label)
            note_labels.append(label)

        content_layout.addWidget(note_card)

        export_btn = QPushButton("Export TXT")
        export_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_btn.setStyleSheet(self.report_action_btn_style())
        export_btn.setMinimumHeight(34)
        footer_layout.addWidget(export_btn)

        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_pdf_btn.setStyleSheet(self.report_action_btn_style())
        export_pdf_btn.setMinimumHeight(34)
        footer_layout.addWidget(export_pdf_btn)

        print_btn = QPushButton("Print")
        print_btn.setCursor(QCursor(Qt.PointingHandCursor))
        print_btn.setStyleSheet(self.report_action_btn_style())
        print_btn.setMinimumHeight(34)
        footer_layout.addWidget(print_btn)

        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)

        state = {"duration_key": period_combo.currentData(), "export_text": ""}

        def set_value_style(label_widget, value_text, emphasize=False, positive_negative=False):
            if positive_negative:
                style = (
                    "color: #c62828; font-size: 18px; font-weight: 700; padding-left: 0;"
                    if value_text.startswith("-")
                    else "color: #2e7d32; font-size: 18px; font-weight: 700; padding-left: 0;"
                )
            elif emphasize:
                style = "color: #223746; font-size: 18px; font-weight: 700; padding-left: 0;"
            else:
                style = "color: #223746; font-size: 14px; font-weight: 700; padding-left: 0;"
            label_widget.setStyleSheet(style)
            label_widget.setText(value_text)

        def rebuild():
            duration_key = period_combo.currentData()
            state["duration_key"] = duration_key
            period_label.setText(f"Selected: {self.get_duration_label(duration_key)}")

            snapshot = service.get_cash_flow_snapshot(duration_key)
            cash_flow = snapshot["cash_flow"]
            session_cash = snapshot["session_cash"]
            session_label = snapshot["session_label"]

            inflow_customer_value.setText(f"{float(cash_flow.get('customer_received', 0.0) or 0.0):,.2f}")
            inflow_supplier_value.setText(f"{float(cash_flow.get('supplier_received', 0.0) or 0.0):,.2f}")
            set_value_style(inflow_total_value, f"{float(cash_flow.get('total_inflows', 0.0) or 0.0):,.2f}", emphasize=True)

            outflow_supplier_value.setText(f"{float(cash_flow.get('supplier_paid', 0.0) or 0.0):,.2f}")
            outflow_customer_value.setText(f"{float(cash_flow.get('customer_paid', 0.0) or 0.0):,.2f}")
            outflow_expense_value.setText(f"{float(cash_flow.get('cash_expenses', 0.0) or 0.0):,.2f}")
            set_value_style(outflow_total_value, f"{float(cash_flow.get('total_outflows', 0.0) or 0.0):,.2f}", emphasize=True)

            set_value_style(net_cash_value, f"{float(cash_flow.get('net_cash_movement', 0.0) or 0.0):,.2f}", emphasize=True, positive_negative=True)
            session_cash_value.setText(f"{float(session_cash.get('cash_value', 0.0) or 0.0):,.2f}")
            session_cash_label_widget.setText(session_label)

            for label_widget, note_text in zip(note_labels, snapshot["notes"]):
                label_widget.setText(note_text)

            state["export_text"] = self.build_report_text(
                "Cash Flow",
                meta_lines=[f"Period: {self.get_duration_label(duration_key)}"],
                sections=[
                    {
                        "title": "Cash Inflows",
                        "lines": [
                            ("Cash Received From Customers", f"{float(cash_flow.get('customer_received', 0.0) or 0.0):,.2f}"),
                            ("Cash Received From Suppliers", f"{float(cash_flow.get('supplier_received', 0.0) or 0.0):,.2f}"),
                            ("Total Cash Inflows", f"{float(cash_flow.get('total_inflows', 0.0) or 0.0):,.2f}"),
                        ],
                    },
                    {
                        "title": "Cash Outflows",
                        "lines": [
                            ("Cash Paid To Suppliers", f"{float(cash_flow.get('supplier_paid', 0.0) or 0.0):,.2f}"),
                            ("Cash Paid To Customers", f"{float(cash_flow.get('customer_paid', 0.0) or 0.0):,.2f}"),
                            ("Cash Expenses", f"{float(cash_flow.get('cash_expenses', 0.0) or 0.0):,.2f}"),
                            ("Total Cash Outflows", f"{float(cash_flow.get('total_outflows', 0.0) or 0.0):,.2f}"),
                        ],
                    },
                    {
                        "title": "Summary",
                        "lines": [
                            ("Net Cash Movement", f"{float(cash_flow.get('net_cash_movement', 0.0) or 0.0):,.2f}"),
                            (session_label, f"{float(session_cash.get('cash_value', 0.0) or 0.0):,.2f}"),
                            (
                                "Cash Row Counts",
                                f"Customers {int(cash_flow.get('customer_rows', 0) or 0)} | Suppliers {int(cash_flow.get('supplier_rows', 0) or 0)} | Expenses {int(cash_flow.get('expense_rows', 0) or 0)}",
                            ),
                        ],
                    },
                ],
            )

        period_combo.currentIndexChanged.connect(lambda _: rebuild())
        export_btn.clicked.connect(lambda: self.export_report_text("cash_flow", "Cash Flow", state["export_text"]))
        export_pdf_btn.clicked.connect(lambda: self.export_report_pdf("cash_flow", "Cash Flow", state["export_text"]))
        print_btn.clicked.connect(lambda: self.print_report_text("Cash Flow", state["export_text"]))
        rebuild()

        dialog.exec()

    def show_sales_summary_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Sales Summary",
            "Invoice-level sales view for the selected period.",
            [
                ("Sales ID", "sales_id"),
                ("Date", "sales_date"),
                ("Customer", "customer_name"),
                ("Salesman", "salesman_name"),
                ("Total", "total"),
                ("Received", "received"),
                ("Remaining", "remaining"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_sales_summary_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Total Sales: {sum(float(r.get('total', 0) or 0) for r in rows):,.2f} | "
                f"Received: {sum(float(r.get('received', 0) or 0) for r in rows):,.2f} | "
                f"Remaining: {sum(float(r.get('remaining', 0) or 0) for r in rows):,.2f}"
            ),
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Sales Detail (SALE#{int(row.get('sales_id', 0) or 0)})",
                self.fetch_sales_reference_details(f"SALE#{int(row.get('sales_id', 0) or 0)}"),
            ),
        )

    def show_sales_by_product_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Sales by Product",
            "Product-wise sales performance for the selected period.",
            [
                ("Product", "product_name"),
                ("Qty Sold", "qty_sold"),
                ("Sales Value", "sales_value"),
                ("Avg Unit Price", "avg_unit_price"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_sales_by_product_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Qty Sold: {sum(float(r.get('qty_sold', 0) or 0) for r in rows):,.2f} | "
                f"Sales Value: {sum(float(r.get('sales_value', 0) or 0) for r in rows):,.2f}"
            ),
        )

    def show_sales_by_customer_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Sales by Customer",
            "Customer-wise sales totals and collection status.",
            [
                ("Customer", "customer_name"),
                ("Invoices", "invoice_count"),
                ("Total Sales", "total_sales"),
                ("Total Received", "total_received"),
                ("Total Remaining", "total_remaining"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_sales_by_customer_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Total Sales: {sum(float(r.get('total_sales', 0) or 0) for r in rows):,.2f} | "
                f"Received: {sum(float(r.get('total_received', 0) or 0) for r in rows):,.2f}"
            ),
        )

    def show_sales_by_sales_rep_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Sales by Sales Rep",
            "User-wise sales performance for the selected period.",
            [
                ("Sales Rep", "rep_name"),
                ("Invoices", "invoice_count"),
                ("Total Sales", "total_sales"),
                ("Total Received", "total_received"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_sales_by_rep_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Total Sales: {sum(float(r.get('total_sales', 0) or 0) for r in rows):,.2f}"
            ),
        )

    def show_sales_return_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Sales Return Report",
            "Sales return invoices for the selected period.",
            [
                ("Return ID", "return_id"),
                ("Date", "return_date"),
                ("Customer", "customer_name"),
                ("Sales ID", "sales_id"),
                ("Total", "total"),
                ("Paid", "paid"),
                ("Remaining", "remaining"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_sales_return_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Return Total: {sum(float(r.get('total', 0) or 0) for r in rows):,.2f}"
            ),
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Sales Return Detail (SR#{int(row.get('return_id', 0) or 0)})",
                self.fetch_sales_return_reference_details(f"SR#{int(row.get('return_id', 0) or 0)}"),
            ),
        )

    def show_receipt_list_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Receipt List",
            "Customer receipt entries with received amounts greater than zero.",
            [
                ("Receipt ID", "receipt_id"),
                ("Date", "receipt_date"),
                ("Customer", "customer_name"),
                ("Type", "transaction_type"),
                ("Ref ID", "ref_id"),
                ("Amount Received", "amount_received"),
                ("Payment Method", "payment_method"),
                ("Reference", "payment_reference"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_receipt_list_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Total Received: {sum(float(r.get('amount_received', 0) or 0) for r in rows):,.2f}"
            ),
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Receipt Detail ({int(row.get('receipt_id', 0) or 0)})",
                self.fetch_customer_transaction_reference_details(int(row.get('receipt_id', 0) or 0)),
            ),
        )

    def show_profit_by_sale_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Profit by Sale",
            "Sale-level profitability using known-cost lines, with unknown-cost revenue shown separately.",
            [
                ("Sales ID", "sales_id"),
                ("Date", "sales_date"),
                ("Customer", "customer_name"),
                ("Salesman", "salesman_name"),
                ("Known Revenue", "known_revenue"),
                ("Known COGS", "known_cogs"),
                ("Known Profit", "known_profit"),
                ("Unknown Revenue", "unknown_revenue"),
                ("Coverage %", "coverage_pct"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_profit_by_sale_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Known Profit: {sum(float(r.get('known_profit', 0) or 0) for r in rows):,.2f} | "
                f"Unknown Revenue: {sum(float(r.get('unknown_revenue', 0) or 0) for r in rows):,.2f}"
            ),
            note_text="Known profit excludes sale lines whose consumed stock has unknown cost.",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Sales Detail (SALE#{int(row.get('sales_id', 0) or 0)})",
                self.fetch_sales_reference_details(f"SALE#{int(row.get('sales_id', 0) or 0)}"),
            ),
        )

    def show_daily_sales_register_dialog(self):
        self.show_sales_table_report_dialog(
            "Daily Sales Register",
            "Day-wise invoice totals for the selected period.",
            [
                ("Date", "sales_date"),
                ("Invoices", "invoice_count"),
                ("Total Sales", "total_sales"),
                ("Total Received", "total_received"),
                ("Total Remaining", "total_remaining"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_daily_sales_register_rows(duration),
            summary_builder=lambda rows: (
                f"Days: {len(rows)} | Total Sales: {sum(float(r.get('total_sales', 0) or 0) for r in rows):,.2f}"
            ),
        )

    def show_purchase_summary_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Purchase Summary",
            "Purchase invoice level summary for the selected period.",
            [
                ("Purchase ID", "purchase_id"),
                ("Date", "purchase_date"),
                ("Supplier", "supplier_name"),
                ("Rep", "rep_name"),
                ("Seller Invoice", "seller_invoice"),
                ("Total", "total"),
                ("Paid", "paid"),
                ("Remaining", "remaining"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_purchase_summary_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Total Purchase: {sum(float(r.get('total', 0) or 0) for r in rows):,.2f} | "
                f"Paid: {sum(float(r.get('paid', 0) or 0) for r in rows):,.2f} | "
                f"Remaining: {sum(float(r.get('remaining', 0) or 0) for r in rows):,.2f}"
            ),
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Purchase Detail ({int(row.get('purchase_id', 0) or 0)})",
                self.fetch_purchase_reference_details(int(row.get('purchase_id', 0) or 0)),
            ),
        )

    def show_purchase_by_supplier_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Purchase by Supplier",
            "Supplier-wise purchase totals and outstanding balances.",
            [
                ("Supplier", "supplier_name"),
                ("Invoices", "invoice_count"),
                ("Total Purchase", "total_purchase"),
                ("Total Paid", "total_paid"),
                ("Total Remaining", "total_remaining"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_purchase_by_supplier_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Total Purchase: {sum(float(r.get('total_purchase', 0) or 0) for r in rows):,.2f}"
            ),
        )

    def show_purchase_by_product_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Purchase by Product",
            "Product-wise purchase quantities and values.",
            [
                ("Product", "product_name"),
                ("Qty Received", "qty_received"),
                ("Purchase Value", "purchase_value"),
                ("Avg Rate", "avg_rate"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_purchase_by_product_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Qty Received: {sum(float(r.get('qty_received', 0) or 0) for r in rows):,.2f} | "
                f"Purchase Value: {sum(float(r.get('purchase_value', 0) or 0) for r in rows):,.2f}"
            ),
        )

    def show_po_status_report_dialog(self):
        self.show_sales_table_report_dialog(
            "PO Status Report",
            "Purchase order status with linked GRN activity.",
            [
                ("PO Number", "po_number"),
                ("PO Date", "po_date"),
                ("Supplier", "supplier_name"),
                ("Status", "status"),
                ("Ordered Qty", "ordered_qty"),
                ("Received Qty", "received_qty"),
                ("Remaining Qty", "remaining_qty"),
                ("Total Value", "total_value"),
                ("GRN Count", "grn_count"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_po_status_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Ordered: {sum(float(r.get('ordered_qty', 0) or 0) for r in rows):,.2f} | "
                f"Received: {sum(float(r.get('received_qty', 0) or 0) for r in rows):,.2f} | "
                f"Remaining: {sum(float(r.get('remaining_qty', 0) or 0) for r in rows):,.2f}"
            ),
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"PO Detail ({int(row.get('po_id', 0) or 0)})",
                self.fetch_po_reference_details(int(row.get('po_id', 0) or 0)),
            ),
        )

    def show_grn_status_report_dialog(self):
        self.show_sales_table_report_dialog(
            "GRN Status Report",
            "Goods receipt status with PO reference and supplier context.",
            [
                ("GRN Number", "grn_number"),
                ("GRN Date", "grn_date"),
                ("PO Number", "po_number"),
                ("Supplier", "supplier_name"),
                ("Status", "status"),
                ("Total Value", "total_value"),
                ("Line Count", "line_count"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_grn_status_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | GRN Value: {sum(float(r.get('total_value', 0) or 0) for r in rows):,.2f}"
            ),
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"GRN Detail ({int(row.get('grn_id', 0) or 0)})",
                self.fetch_grn_reference_details(int(row.get('grn_id', 0) or 0)),
            ),
        )

    def show_partial_receipt_analytics_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Partial Receipt Analytics",
            "Purchase orders that have started receiving but still have remaining quantity open.",
            [
                ("PO Number", "po_number"),
                ("PO Date", "po_date"),
                ("Supplier", "supplier_name"),
                ("Status", "status"),
                ("Ordered Qty", "ordered_qty"),
                ("Received Qty", "received_qty"),
                ("Remaining Qty", "remaining_qty"),
                ("Completion %", "completion_pct"),
                ("GRN Count", "grn_count"),
                ("Days Open", "days_open"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_partial_po_receipt_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Ordered: {sum(float(r.get('ordered_qty', 0) or 0) for r in rows):,.2f} | "
                f"Received: {sum(float(r.get('received_qty', 0) or 0) for r in rows):,.2f} | "
                f"Remaining: {sum(float(r.get('remaining_qty', 0) or 0) for r in rows):,.2f}"
            ),
            note_text="This report focuses only on partially received POs and helps track incomplete procurement against cumulative GRNs.",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"PO Detail ({int(row.get('po_id', 0) or 0)})",
                self.fetch_po_reference_details(int(row.get('po_id', 0) or 0)),
            ),
        )

    def show_purchase_return_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Purchase Return Report",
            "Purchase return documents for the selected period.",
            [
                ("Return ID", "return_id"),
                ("Date", "return_date"),
                ("Supplier", "supplier_name"),
                ("Rep", "rep_name"),
                ("Total", "total"),
                ("Received", "received"),
                ("Remaining", "remaining"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_purchase_return_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Return Total: {sum(float(r.get('total', 0) or 0) for r in rows):,.2f}"
            ),
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Purchase Return Detail (PR#{int(row.get('return_id', 0) or 0)})",
                self.fetch_purchase_return_reference_details(f"PR#{int(row.get('return_id', 0) or 0)}"),
            ),
        )

    def show_supplier_payment_summary_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Supplier Payment Summary",
            "Supplier transaction rollup for payments and receipts.",
            [
                ("Supplier", "supplier_name"),
                ("Transactions", "txn_count"),
                ("Total Paid", "total_paid"),
                ("Total Received", "total_received"),
                ("Payable After", "payable_after"),
                ("Receivable After", "receivable_after"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_supplier_payment_summary_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Total Paid: {sum(float(r.get('total_paid', 0) or 0) for r in rows):,.2f} | "
                f"Total Received: {sum(float(r.get('total_received', 0) or 0) for r in rows):,.2f}"
            ),
        )

    def show_purchase_vs_sales_comparison_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Purchase vs Sales Comparison",
            "Period-wise comparison of purchase and sales totals.",
            [
                ("Period", "period"),
                ("Purchase Total", "purchase_total"),
                ("Sales Total", "sales_total"),
                ("Variance", "variance"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_purchase_vs_sales_comparison_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Purchase Total: {sum(float(r.get('purchase_total', 0) or 0) for r in rows):,.2f} | "
                f"Sales Total: {sum(float(r.get('sales_total', 0) or 0) for r in rows):,.2f}"
            ),
        )

    def show_stock_valuation_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Stock Valuation Report",
            "Current on-hand stock value using known unit cost, with unknown-cost units shown separately.",
            [
                ("Product", "product_name"),
                ("Stock Qty", "stock_qty"),
                ("Known Stock Value", "known_stock_value"),
                ("Unknown Cost Units", "unknown_cost_units"),
            ],
            fetch_rows=lambda _duration: report_service.ReportService().get_stock_valuation_rows(),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Stock Qty: {sum(float(r.get('stock_qty', 0) or 0) for r in rows):,.2f} | "
                f"Known Stock Value: {sum(float(r.get('known_stock_value', 0) or 0) for r in rows):,.2f}"
            ),
            note_text="This view is current-state and not period-filtered. Unknown-cost units are excluded from known stock value.",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Product Stock Summary ({row.get('product_name', '')})",
                [
                    ("Product", row.get("product_name", "")),
                    ("Stock Qty", f"{float(row.get('stock_qty', 0) or 0):.2f}"),
                    ("Known Stock Value", f"{float(row.get('known_stock_value', 0) or 0):.2f}"),
                    ("Unknown Cost Units", f"{float(row.get('unknown_cost_units', 0) or 0):.2f}"),
                ],
            ),
        )

    def show_expired_stock_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Expired Stock Report",
            "Batches that are already expired and still have quantity remaining.",
            [
                ("Product", "product_name"),
                ("Batch No", "batch_no"),
                ("Expiry Date", "expiry_date"),
                ("Qty Remaining", "qty_remaining"),
                ("Unit Cost", "unit_cost"),
                ("Stock Value", "stock_value"),
                ("Source", "source"),
            ],
            fetch_rows=lambda _duration: report_service.ReportService().get_expired_stock_rows(),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Qty Remaining: {sum(float(r.get('qty_remaining', 0) or 0) for r in rows):,.2f} | "
                f"Stock Value: {sum(float(r.get('stock_value', 0) or 0) for r in rows):,.2f}"
            ),
            note_text="This view is current-state and not period-filtered.",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Batch Detail (BATCH#{int(row.get('batch_id', 0) or 0)})",
                self.fetch_batch_reference_details(f"BATCH#{int(row.get('batch_id', 0) or 0)}") if row.get("batch_id") else [
                    ("Product", row.get("product_name", "")),
                    ("Batch No", row.get("batch_no", "")),
                    ("Expiry Date", row.get("expiry_date", "")),
                    ("Qty Remaining", row.get("qty_remaining", "")),
                    ("Stock Value", row.get("stock_value", "")),
                ],
            ),
        )

    def show_batch_traceability_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Batch Traceability Report",
            "Batch-level traceability across received stock, remaining stock, cost, and source.",
            [
                ("Batch ID", "batch_id"),
                ("Product", "product_name"),
                ("Batch No", "batch_no"),
                ("Expiry Date", "expiry_date"),
                ("Total Received", "total_received"),
                ("Qty Remaining", "quantity_remaining"),
                ("Unit Cost", "unit_cost"),
                ("Source", "source"),
                ("Received At", "received_at"),
            ],
            fetch_rows=lambda _duration: report_service.ReportService().get_batch_traceability_rows(),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Total Received: {sum(float(r.get('total_received', 0) or 0) for r in rows):,.2f} | "
                f"Qty Remaining: {sum(float(r.get('quantity_remaining', 0) or 0) for r in rows):,.2f}"
            ),
            note_text="This view is current-state and not period-filtered.",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Batch Detail (BATCH#{int(row.get('batch_id', 0) or 0)})",
                self.fetch_batch_reference_details(f"BATCH#{int(row.get('batch_id', 0) or 0)}"),
            ),
        )

    def show_inventory_adjustment_log_dialog(self):
        self.show_sales_table_report_dialog(
            "Inventory Adjustment Log",
            "Inventory additions and deductions recorded for the selected period.",
            [
                ("Adjustment ID", "adjustment_id"),
                ("Date", "adjustment_date"),
                ("Product", "product_name"),
                ("Batch No", "batch_no"),
                ("Type", "adjustment_type"),
                ("Qty", "qty"),
                ("Old Qty", "old_qty"),
                ("New Qty", "new_qty"),
                ("Reason", "reason"),
                ("Adjusted By", "adjusted_by"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_inventory_adjustment_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Total Qty Changed: {sum(float(r.get('qty', 0) or 0) for r in rows):,.2f}"
            ),
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Inventory Adjustment Detail (ADJ#{int(row.get('adjustment_id', 0) or 0)})",
                self.fetch_adjustment_reference_details(f"ADJ#{int(row.get('adjustment_id', 0) or 0)}"),
            ),
        )

    def show_customer_outstanding_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Customer Outstanding",
            "Customer balances with receivable and payable exposure.",
            [
                ("Customer", "customer_name"),
                ("Receivable", "receivable"),
                ("Payable", "payable"),
                ("Net Exposure", "net_exposure"),
            ],
            fetch_rows=lambda _duration: report_service.ReportService().get_customer_outstanding_rows(),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Receivable: {sum(float(r.get('receivable', 0) or 0) for r in rows):,.2f} | "
                f"Payable: {sum(float(r.get('payable', 0) or 0) for r in rows):,.2f}"
            ),
            note_text="This is a current balance view and is not period-filtered.",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Customer Outstanding ({row.get('customer_name', '')})",
                [
                    ("Customer", row.get("customer_name", "")),
                    ("Receivable", f"{float(row.get('receivable', 0) or 0):.2f}"),
                    ("Payable", f"{float(row.get('payable', 0) or 0):.2f}"),
                    ("Net Exposure", f"{float(row.get('net_exposure', 0) or 0):.2f}"),
                ],
            ),
        )

    def show_supplier_outstanding_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Supplier Outstanding",
            "Supplier balances with payable and receivable exposure.",
            [
                ("Supplier", "supplier_name"),
                ("Payable", "payable"),
                ("Receivable", "receivable"),
                ("Net Exposure", "net_exposure"),
            ],
            fetch_rows=lambda _duration: report_service.ReportService().get_supplier_outstanding_rows(),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Payable: {sum(float(r.get('payable', 0) or 0) for r in rows):,.2f} | "
                f"Receivable: {sum(float(r.get('receivable', 0) or 0) for r in rows):,.2f}"
            ),
            note_text="This is a current balance view and is not period-filtered.",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Supplier Outstanding ({row.get('supplier_name', '')})",
                [
                    ("Supplier", row.get("supplier_name", "")),
                    ("Payable", f"{float(row.get('payable', 0) or 0):.2f}"),
                    ("Receivable", f"{float(row.get('receivable', 0) or 0):.2f}"),
                    ("Net Exposure", f"{float(row.get('net_exposure', 0) or 0):.2f}"),
                ],
            ),
        )

    def show_overdue_recovery_report_dialog(self):
        self.show_sales_table_report_dialog(
            "Overdue Recovery List",
            "Customers with overdue receivables prioritized for recovery follow-up.",
            [
                ("Customer", "customer_name"),
                ("Total Due", "total_due"),
                ("31-60 Days", "days_31_60"),
                ("61-90 Days", "days_61_90"),
                ("90+ Days", "days_90plus"),
                ("Overdue Total", "overdue_total"),
            ],
            fetch_rows=lambda _duration: self.get_overdue_recovery_rows(),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Overdue Total: {sum(float(r.get('overdue_total', 0) or 0) for r in rows):,.2f}"
            ),
            note_text="Derived from customer aging buckets. This is a current receivable recovery view.",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Overdue Recovery ({row.get('customer_name', '')})",
                [
                    ("Customer", row.get("customer_name", "")),
                    ("Total Due", f"{float(row.get('total_due', 0) or 0):.2f}"),
                    ("31-60 Days", f"{float(row.get('days_31_60', 0) or 0):.2f}"),
                    ("61-90 Days", f"{float(row.get('days_61_90', 0) or 0):.2f}"),
                    ("90+ Days", f"{float(row.get('days_90plus', 0) or 0):.2f}"),
                    ("Overdue Total", f"{float(row.get('overdue_total', 0) or 0):.2f}"),
                ],
            ),
        )

    def show_credit_limit_utilization_dialog(self):
        self.show_sales_table_report_dialog(
            "Credit Limit Utilization",
            "Customer receivable exposure against configured credit limits.",
            columns=[
                ("Customer", "customer_name"),
                ("Credit Limit", "credit_limit"),
                ("Receivable", "receivable"),
                ("Available Credit", "available_credit"),
                ("Utilization %", "utilization_pct"),
                ("Status", "status"),
            ],
            fetch_rows=lambda _duration: report_service.ReportService().get_credit_limit_utilization_rows(),
            summarize_rows=lambda rows: (
                f"Rows: {len(rows)} | Total Limit: {sum(float(r.get('credit_limit', 0) or 0) for r in rows):,.2f} | "
                f"Total Receivable: {sum(float(r.get('receivable', 0) or 0) for r in rows):,.2f}"
            ),
            note_text="Customer-only view. Utilization is based on current receivable against configured credit limit.",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Credit Limit ({row.get('customer_name', '')})",
                [
                    ("Customer", row.get("customer_name", "")),
                    ("Credit Limit", f"{float(row.get('credit_limit', 0) or 0):.2f}"),
                    ("Current Receivable", f"{float(row.get('receivable', 0) or 0):.2f}"),
                    ("Current Payable", f"{float(row.get('payable', 0) or 0):.2f}"),
                    ("Available Credit", f"{float(row.get('available_credit', 0) or 0):.2f}"),
                    ("Utilization %", f"{float(row.get('utilization_pct', 0) or 0):.2f}%"),
                    ("Status", row.get("status", "")),
                ],
            ),
        )

    def get_overdue_recovery_rows(self):
        rows = report_service.ReportService().get_receivable_aging()
        overdue_rows = []
        for row in rows:
            overdue_total = (
                float(row.get("days_1_30", 0) or 0)
                + float(row.get("days_31_60", 0) or 0)
                + float(row.get("days_61_90", 0) or 0)
                + float(row.get("days_90plus", 0) or 0)
            )
            if overdue_total <= 0:
                continue
            overdue_rows.append({
                "customer_name": row.get("customer_name", ""),
                "total_due": float(row.get("total_due", 0) or 0),
                "days_31_60": float(row.get("days_31_60", 0) or 0),
                "days_61_90": float(row.get("days_61_90", 0) or 0),
                "days_90plus": float(row.get("days_90plus", 0) or 0),
                "overdue_total": overdue_total,
            })

        overdue_rows.sort(
            key=lambda item: (
                -float(item.get("days_90plus", 0) or 0),
                -float(item.get("days_61_90", 0) or 0),
                -float(item.get("overdue_total", 0) or 0),
            )
        )
        return overdue_rows

    def show_price_change_history_dialog(self):
        self.show_sales_table_report_dialog(
            "Price Change History",
            "Historical product price changes logged during purchase price updates.",
            [
                ("Change ID", "change_id"),
                ("Date", "change_date"),
                ("Product", "product_name"),
                ("Previous Price", "previous_price"),
                ("New Price", "new_price"),
                ("Variance", "variance"),
                ("Source", "source"),
                ("User", "username"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_price_change_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Price Changes Logged: {len(rows)}"
            ),
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Price Change Detail ({int(row.get('change_id', 0) or 0)})",
                self.fetch_price_change_reference_details(int(row.get('change_id', 0) or 0)),
            ),
        )

    def show_login_session_log_dialog(self):
        self.show_sales_table_report_dialog(
            "Login / Session Log",
            "Login-category activity log entries for the selected period.",
            [
                ("Log ID", "log_id"),
                ("Timestamp", "timestamp"),
                ("Username", "username"),
                ("Action", "action"),
                ("Note", "note"),
                ("Login Session", "login_session_id"),
                ("Daily Session", "daily_session_id"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_login_activity_rows(duration),
            summary_builder=lambda rows: f"Rows: {len(rows)}",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Login Activity Detail ({int(row.get('log_id', 0) or 0)})",
                [
                    ("Log ID", row.get("log_id", "")),
                    ("Timestamp", row.get("timestamp", "")),
                    ("Username", row.get("username", "")),
                    ("Action", row.get("action", "")),
                    ("Note", row.get("note", "")),
                    ("Login Session", row.get("login_session_id", "")),
                    ("Daily Session", row.get("daily_session_id", "")),
                ],
            ),
        )

    def show_shift_closing_summary_dialog(self):
        self.show_sales_table_report_dialog(
            "Shift Closing Summary",
            "Closed daily sessions with cash closing values for the selected period.",
            [
                ("Session ID", "session_id"),
                ("Session Date", "session_date"),
                ("Opening Cash", "opening_cash"),
                ("System Cash", "system_cash"),
                ("Actual Cash", "actual_cash"),
                ("Withdrawal", "withdrawal"),
                ("Cash Difference", "cash_difference"),
                ("Opened At", "opened_at"),
                ("Closed At", "closed_at"),
            ],
            fetch_rows=lambda duration: report_service.ReportService().get_shift_closing_summary_rows(duration),
            summary_builder=lambda rows: (
                f"Rows: {len(rows)} | Opening Cash: {sum(float(r.get('opening_cash', 0) or 0) for r in rows):,.2f} | "
                f"Actual Cash: {sum(float(r.get('actual_cash', 0) or 0) for r in rows):,.2f}"
            ),
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"Daily Session Detail ({int(row.get('session_id', 0) or 0)})",
                self.fetch_daily_session_reference_details(int(row.get('session_id', 0) or 0)),
            ),
        )

    def show_system_change_audit_dialog(self):
        self.show_sales_table_report_dialog(
            "System Change Audit",
            "Operational activity log excluding login events, useful for reviewing stock, sales, purchase, and price changes.",
            [
                ("Timestamp", "timestamp"),
                ("Username", "username"),
                ("Category", "category"),
                ("Action", "action"),
                ("Entity", "entity_type"),
                ("Entity ID", "entity_id"),
                ("Note", "note"),
            ],
            fetch_rows=lambda duration: self.get_system_change_audit_rows(duration),
            summary_builder=lambda rows: f"Rows: {len(rows)}",
            row_double_click_handler=lambda row: self.show_reference_detail_dialog(
                f"System Change Detail ({row.get('timestamp', '')})",
                [
                    ("Timestamp", row.get("timestamp", "")),
                    ("Username", row.get("username", "")),
                    ("Category", row.get("category", "")),
                    ("Action", row.get("action", "")),
                    ("Entity", row.get("entity_type", "")),
                    ("Entity ID", row.get("entity_id", "")),
                    ("Note", row.get("note", "")),
                ],
            ),
        )

    def show_discount_override_report_dialog(self):
        self.show_unavailable_audit_dialog(
            "Discount & Override Report",
            [
                "Discount values exist on sales and purchase documents, but discount override events are not being logged as a separate audit trail yet.",
                "If you want this report to become real, we should log manual override actions into `activity_log` with old/new values and user context.",
            ],
        )

    def show_deleted_transactions_log_dialog(self):
        self.show_unavailable_audit_dialog(
            "Deleted Transactions Log",
            [
                "Deleted transaction history is not being captured in the current schema.",
                "Right now the system uses restrictive foreign keys in many places, but it does not maintain a dedicated deletion audit table.",
            ],
        )

    def show_unavailable_audit_dialog(self, title, lines):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(620, 300)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        heading = QLabel(title)
        heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        header_layout.addWidget(heading)

        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        for text in lines:
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 12px; color: #5A7183; padding-left: 0;")
            card_layout.addWidget(label)

        content_layout.addWidget(card)

        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)

        dialog.exec()

    def get_system_change_audit_rows(self, duration):
        rows = report_service.ReportService().get_activity_log(duration=duration, category=None, username=None, limit=1000)
        filtered = []
        for row in rows:
            category = str(row.get("category", "") or "").strip().lower()
            if category == "login":
                continue
            filtered.append({
                "timestamp": row.get("timestamp", ""),
                "username": row.get("username", ""),
                "category": row.get("category", ""),
                "action": row.get("action", ""),
                "entity_type": row.get("entity_type", ""),
                "entity_id": row.get("entity_id", ""),
                "note": row.get("note", ""),
            })
        return filtered

    def create_sales_report_catalog_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        card.setMinimumHeight(96)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        reports = [
            "Sales Summary",
            "Sales by Product",
            "Sales by Customer",
            "Sales by Sales Rep",
            "Sales Return Report",
            "Receipt List",
            "Profit by Sale",
            "Daily Sales Register",
        ]

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header = QFrame()
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet("QFrame { background-color: #325D7B; border: 1px solid #284B63; border-radius: 6px; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(6)

        title = QLabel("Sales Reports")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; padding-left: 0;")
        title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(title)
        header_layout.addStretch()

        toggle_btn = QToolButton()
        toggle_btn.setArrowType(Qt.DownArrow)
        toggle_btn.setStyleSheet("QToolButton { border: none; padding: 0; color: #FFFFFF; background: transparent; }")
        toggle_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(toggle_btn)

        layout.addWidget(header)

        subtitle = QLabel("Sales performance, customer trends, item-wise analysis, and daily registers.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #5A7183; font-size: 11px; font-weight: 500; padding-left: 0;")
        layout.addWidget(subtitle)

        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        for report_name in reports:
            details_layout.addLayout(
                self.create_financial_report_row(
                    report_name,
                    self.get_sales_report_handler(report_name),
                )
            )

        layout.addWidget(details)
        self.bind_catalog_section_toggle(header, toggle_btn, details, expanded=False)

        return card

    def create_purchase_report_catalog_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        card.setMinimumHeight(96)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        reports = [
            "Purchase Summary",
            "Purchase by Supplier",
            "Purchase by Product",
            "PO Status Report",
            "Partial Receipt Analytics",
            "GRN Status Report",
            "Purchase Return Report",
            "Supplier Payment Summary",
            "Purchase vs Sales Comparison",
        ]

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header = QFrame()
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet("QFrame { background-color: #325D7B; border: 1px solid #284B63; border-radius: 6px; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(6)

        title = QLabel("Purchase Reports")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; padding-left: 0;")
        title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(title)
        header_layout.addStretch()

        toggle_btn = QToolButton()
        toggle_btn.setArrowType(Qt.DownArrow)
        toggle_btn.setStyleSheet("QToolButton { border: none; padding: 0; color: #FFFFFF; background: transparent; }")
        toggle_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(toggle_btn)

        layout.addWidget(header)

        subtitle = QLabel("Purchases, PO and GRN status, supplier trends, and return tracking.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #5A7183; font-size: 11px; font-weight: 500; padding-left: 0;")
        layout.addWidget(subtitle)

        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        for report_name in reports:
            details_layout.addLayout(
                self.create_financial_report_row(
                    report_name,
                    self.get_purchase_report_handler(report_name),
                )
            )

        layout.addWidget(details)
        self.bind_catalog_section_toggle(header, toggle_btn, details, expanded=False)

        return card

    def create_inventory_report_catalog_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        card.setMinimumHeight(96)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        reports = [
            "Stock Valuation Report",
            "Stock Movement Report",
            "Near Expiry Report",
            "Expired Stock Report",
            "Low Stock / Reorder Report",
            "Non-Moving / Dead Stock",
            "Batch Traceability Report",
            "Inventory Adjustment Log",
            "Opening Stock Cost Review",
        ]

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header = QFrame()
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet("QFrame { background-color: #325D7B; border: 1px solid #284B63; border-radius: 6px; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(6)

        title = QLabel("Inventory Reports")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; padding-left: 0;")
        title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(title)
        header_layout.addStretch()

        toggle_btn = QToolButton()
        toggle_btn.setArrowType(Qt.DownArrow)
        toggle_btn.setStyleSheet("QToolButton { border: none; padding: 0; color: #FFFFFF; background: transparent; }")
        toggle_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(toggle_btn)

        layout.addWidget(header)

        subtitle = QLabel("Stock valuation, movement, expiry, non-moving, and batch-level tracking.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #5A7183; font-size: 11px; font-weight: 500; padding-left: 0;")
        layout.addWidget(subtitle)

        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        for report_name in reports:
            details_layout.addLayout(
                self.create_financial_report_row(
                    report_name,
                    self.get_inventory_report_handler(report_name),
                )
            )

        layout.addWidget(details)
        self.bind_catalog_section_toggle(header, toggle_btn, details, expanded=False)

        return card

    def create_dues_report_catalog_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        card.setMinimumHeight(96)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        reports = [
            "Customer Outstanding",
            "Supplier Outstanding",
            "Customer Aging Report",
            "Supplier Aging Report",
            "Collection Forecast",
            "Payment Forecast",
            "Overdue Recovery List",
            "Credit Limit Utilization",
        ]

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header = QFrame()
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet("QFrame { background-color: #325D7B; border: 1px solid #284B63; border-radius: 6px; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(6)

        title = QLabel("Dues & Aging")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; padding-left: 0;")
        title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(title)
        header_layout.addStretch()

        toggle_btn = QToolButton()
        toggle_btn.setArrowType(Qt.DownArrow)
        toggle_btn.setStyleSheet("QToolButton { border: none; padding: 0; color: #FFFFFF; background: transparent; }")
        toggle_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(toggle_btn)

        layout.addWidget(header)

        subtitle = QLabel("Receivables, payables, aging buckets, forecasts, and overdue recovery.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #5A7183; font-size: 11px; font-weight: 500; padding-left: 0;")
        layout.addWidget(subtitle)

        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        for report_name in reports:
            details_layout.addLayout(
                self.create_financial_report_row(
                    report_name,
                    self.get_dues_report_handler(report_name),
                )
            )

        layout.addWidget(details)
        self.bind_catalog_section_toggle(header, toggle_btn, details, expanded=False)

        return card

    def create_audit_report_catalog_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        card.setMinimumHeight(96)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        reports = [
            "User Activity Log",
            "Price Change History",
            "Stock Adjustment Log",
            "Discount & Override Report",
            "Deleted Transactions Log",
            "Login / Session Log",
            "Shift Closing Summary",
            "System Change Audit",
        ]

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header = QFrame()
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet("QFrame { background-color: #325D7B; border: 1px solid #284B63; border-radius: 6px; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(6)

        title = QLabel("Audit & Admin")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; padding-left: 0;")
        title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(title)
        header_layout.addStretch()

        toggle_btn = QToolButton()
        toggle_btn.setArrowType(Qt.DownArrow)
        toggle_btn.setStyleSheet("QToolButton { border: none; padding: 0; color: #FFFFFF; background: transparent; }")
        toggle_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(toggle_btn)

        layout.addWidget(header)

        subtitle = QLabel("User activity, price changes, adjustments, and operational audit logs.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #5A7183; font-size: 11px; font-weight: 500; padding-left: 0;")
        layout.addWidget(subtitle)

        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        for report_name in reports:
            details_layout.addLayout(
                self.create_financial_report_row(
                    report_name,
                    self.get_audit_report_handler(report_name),
                )
            )

        layout.addWidget(details)
        self.bind_catalog_section_toggle(header, toggle_btn, details, expanded=False)

        return card

    def create_report_catalog_card(self, title_text, info_line):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        card.setMinimumHeight(96)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel(title_text)
        title.setStyleSheet(self.summary_card_title_style())

        info = QLabel(info_line)
        info.setWordWrap(True)
        info.setStyleSheet("color: #5A7183; font-size: 11px; font-weight: 500; padding-left: 0;")

        layout.addWidget(title)
        layout.addWidget(info)
        return card

    def set_overview_totals(self, sales_value, purchase_value, expense_value):
        self.catalog_sales_card_data.setText(str(sales_value))
        self.catalog_purchase_card_data.setText(str(purchase_value))
        self.catalog_expense_card_data.setText(str(expense_value))


    def create_stock_cost_card(self):
        
        # Create the card container
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        
        
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)
        
        
        first_line_layout = QHBoxLayout()
        
        estimate_label = QLabel("Estimated Opening Stock Cost")
        self.estimate_cost = QLabel()
        
        first_line_layout.addWidget(estimate_label, 3)
        first_line_layout.addWidget(self.estimate_cost, 1)
        
        card_layout.addLayout(first_line_layout)
        
        
        second_line_layout = QHBoxLayout()
        
        known_stock_cost = QLabel("Known Stock Cost")
        self.known_stock_cost_data = QLabel()
        
        second_line_layout.addWidget(known_stock_cost, 3)
        second_line_layout.addWidget(self.known_stock_cost_data, 1)
        
        card_layout.addLayout(second_line_layout)
        
        snapshot = report_service.ReportService().get_inventory_overview_snapshot()
        self.estimate_cost.setText(f"{float(snapshot.get('opening_estimate_amount', 0.0) or 0.0):,.2f}")
        self.known_stock_cost_data.setText(f"{float(snapshot.get('known_stock_cost_amount', 0.0) or 0.0):.2f}")

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 4, 0, 0)
        action_row.addStretch()

        review_opening_costs_btn = QPushButton("Review Opening Costs")
        review_opening_costs_btn.setCursor(QCursor(Qt.PointingHandCursor))
        review_opening_costs_btn.setStyleSheet(self.report_action_btn_style())
        review_opening_costs_btn.clicked.connect(self.show_opening_stock_cost_review_dialog)
        action_row.addWidget(review_opening_costs_btn)
        card_layout.addLayout(action_row)
        
        
        return card
    
    
    
    
    def create_stock_count_card(self):
        # Create the card container
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)
        
        
        first_line_layout = QHBoxLayout()
        
        expiry_count_label = QLabel("Near Expiry Count")
        self.expiry_count = QPushButton()
        self.expiry_count.setStyleSheet(self.report_action_btn_style())
        
        self.expiry_count.clicked.connect(self.show_near_expiry_dialog)
        
        
        first_line_layout.addWidget(expiry_count_label, 3)
        first_line_layout.addWidget(self.expiry_count, 1)
        
        card_layout.addLayout(first_line_layout)
        
        
        second_line_layout = QHBoxLayout()
        
        low_stock_count_label = QLabel("Low Stock Count")
        self.low_stock_count = QPushButton()
        self.low_stock_count.setStyleSheet(self.report_action_btn_style())
        
        self.low_stock_count.clicked.connect(self.show_low_stock_dialog)
        
        second_line_layout.addWidget(low_stock_count_label, 3)
        second_line_layout.addWidget(self.low_stock_count, 1)
        
        card_layout.addLayout(second_line_layout)

        third_line_layout = QHBoxLayout()

        movement_label = QLabel("Stock Movement")
        self.stock_movement_btn = QPushButton("Open")
        self.stock_movement_btn.setStyleSheet(self.report_action_btn_style())
        self.stock_movement_btn.clicked.connect(self.show_stock_movement_dialog)

        third_line_layout.addWidget(movement_label, 3)
        third_line_layout.addWidget(self.stock_movement_btn, 1)

        card_layout.addLayout(third_line_layout)

        fourth_line_layout = QHBoxLayout()
        activity_label = QLabel("Activity Log")
        self.activity_log_btn = QPushButton("Open")
        self.activity_log_btn.setStyleSheet(self.report_action_btn_style())
        self.activity_log_btn.clicked.connect(self.show_activity_log_dialog)

        fourth_line_layout.addWidget(activity_label, 3)
        fourth_line_layout.addWidget(self.activity_log_btn, 1)

        card_layout.addLayout(fourth_line_layout)

        fifth_line_layout = QHBoxLayout()
        dead_nonmoving_label = QLabel("Dead / Non-moving")
        self.dead_nonmoving_btn = QPushButton("Open")
        self.dead_nonmoving_btn.setStyleSheet(self.report_action_btn_style())
        self.dead_nonmoving_btn.clicked.connect(self.show_dead_nonmoving_stock_dialog)

        fifth_line_layout.addWidget(dead_nonmoving_label, 3)
        fifth_line_layout.addWidget(self.dead_nonmoving_btn, 1)

        card_layout.addLayout(fifth_line_layout)
        
        
        snapshot = report_service.ReportService().get_inventory_overview_snapshot()
        count = snapshot.get("stock_alerts", {})

        near_expiry = count.get('near_expiry_batches', 0)
        low_stock = count.get('low_stock_products', 0)
        
        self.expiry_count.setText(f"{near_expiry:.2f}")
        self.low_stock_count.setText(f"{low_stock:.2f}")
        
        
        return card


    def show_stock_movement_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QLabel, QPushButton
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Stock Movement History")
        dialog.resize(1200, 650)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Duration"))
        duration_combo = QComboBox()
        duration_combo.addItems(["Today", "Past Week", "Past Month", "Past Year", "All"])
        duration_combo.setCurrentText("Past Month")
        filter_row.addWidget(duration_combo)

        filter_row.addWidget(QLabel("Movement Type"))
        movement_type_combo = QComboBox()
        movement_type_combo.addItems([
            "All",
            "PURCHASE_IN",
            "OPENING_STOCK",
            "SALE_OUT",
            "SALES_RETURN_IN",
            "PURCHASE_RETURN_OUT",
            "ADJUSTMENT_IN",
            "ADJUSTMENT_OUT",
        ])
        filter_row.addWidget(movement_type_combo)

        filter_row.addWidget(QLabel("Product"))
        product_combo = QComboBox()
        product_combo.setEditable(True)
        product_combo.addItem("All Products", None)

        for product_row in report_service.ReportService().get_used_product_options():
            product_combo.addItem(product_row["display_name"], product_row["product_id"])
        filter_row.addWidget(product_combo, 1)

        reload_btn = QPushButton("Reload", objectName="TopRightButton")
        filter_row.addWidget(reload_btn)
        header_layout.addLayout(filter_row)

        hint = QLabel("Tip: Double-click any row to open source details from the reference.")
        hint.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        header_layout.addWidget(hint)

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Date/Time",
            "Type",
            "Product",
            "Batch",
            "Qty Change",
            "Reference",
            "User",
            "Reason",
        ])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        content_layout.addWidget(table)

        def reload_data():
            duration_map = {
                "Today": "today",
                "Past Week": "week",
                "Past Month": "month",
                "Past Year": "year",
                "All": "all",
            }

            rows = report_service.ReportService().get_stock_movements(
                duration=duration_map.get(duration_combo.currentText(), "month"),
                product_id=product_combo.currentData(),
                movement_type=movement_type_combo.currentText(),
                limit=1500,
            )

            table.setRowCount(len(rows))

            for r, row_data in enumerate(rows):
                values = [
                    row_data["movement_date"],
                    row_data["movement_type"],
                    row_data["product_name"],
                    row_data["batch_no"],
                    row_data["qty_change"],
                    row_data["reference"],
                    row_data["performed_by"],
                    row_data["reason"],
                ]

                for c, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    table.setItem(r, c, item)

                qty_item = table.item(r, 4)
                if qty_item:
                    qty_value = int(row_data["qty_change"] or 0)
                    if qty_value > 0:
                        qty_item.setForeground(QColor(0, 120, 0))
                    elif qty_value < 0:
                        qty_item.setForeground(QColor(180, 30, 30))

            table.resizeColumnsToContents()

        def on_row_double_click(row, _col):
            reference_item = table.item(row, 5)
            movement_item = table.item(row, 1)

            if not reference_item or not movement_item:
                return

            reference = reference_item.text().strip()
            movement_type = movement_item.text().strip()
            self.open_stock_movement_reference(reference, movement_type)

        reload_btn.clicked.connect(reload_data)
        duration_combo.currentIndexChanged.connect(reload_data)
        movement_type_combo.currentIndexChanged.connect(reload_data)
        product_combo.currentIndexChanged.connect(reload_data)
        table.cellDoubleClicked.connect(on_row_double_click)

        reload_data()

        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)
        dialog.exec()


    def show_dead_nonmoving_stock_dialog(self):
        from PySide6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QTableWidget,
            QTableWidgetItem,
            QComboBox,
            QLabel,
            QPushButton,
            QHeaderView,
        )
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Dead / Non-moving Stock")
        dialog.resize(1250, 680)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Threshold"))

        threshold_combo = QComboBox()
        threshold_combo.addItems(["30 days", "60 days", "90 days", "180 days", "365 days"])
        threshold_combo.setCurrentText("90 days")
        threshold_combo.setFixedWidth(120)
        filter_row.addWidget(threshold_combo)

        filter_row.addWidget(QLabel("View"))
        view_combo = QComboBox()
        view_combo.addItems(["All", "Dead Only", "Non-moving Only"])
        view_combo.setFixedWidth(170)
        filter_row.addWidget(view_combo)

        filter_row.addStretch()
        reload_btn = QPushButton("Reload", objectName="TopRightButton")
        filter_row.addWidget(reload_btn)
        header_layout.addLayout(filter_row)

        hint = QLabel("Dead: never sold. Non-moving: no sale since threshold. Sorted by stock value.")
        hint.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        header_layout.addWidget(hint)

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Status",
            "Product",
            "Stock Qty",
            "Stock Value",
            "Last Sale Date",
            "Days Since Last Sale",
            "Oldest Batch Date",
            "Total Sold",
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        content_layout.addWidget(table)

        summary_label = QLabel("Rows: 0")
        summary_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(summary_label)

        def get_threshold_days():
            txt = (threshold_combo.currentText() or "90 days").strip().split(" ")[0]
            try:
                return int(txt)
            except Exception:
                return 90

        def get_view_mode_key():
            text = (view_combo.currentText() or "All").strip().lower()
            if text == "dead only":
                return "dead"
            if text == "non-moving only":
                return "non_moving"
            return "all"

        def reload_data():
            threshold_days = get_threshold_days()
            view_mode = get_view_mode_key()

            rows = report_service.ReportService().get_dead_nonmoving_stock(
                threshold_days=threshold_days,
                view_mode=view_mode,
                limit=5000,
            )

            total_qty = sum(float(r.get("stock_qty", 0) or 0.0) for r in rows)
            total_value = sum(float(r.get("stock_value", 0) or 0.0) for r in rows)
            dead_count = sum(1 for r in rows if r.get("stock_status") == "DEAD")
            nonmoving_count = sum(1 for r in rows if r.get("stock_status") == "NON_MOVING")

            table.setSortingEnabled(False)
            table.setRowCount(len(rows) + (1 if rows else 0))

            for r, row_data in enumerate(rows):
                status = str(row_data.get("stock_status", "NON_MOVING"))
                last_sale = str(row_data.get("last_sale_date", "") or "")
                days_since = row_data.get("days_since_last_sale")
                days_display = "Never" if status == "DEAD" else str(days_since if days_since is not None else "")

                values = [
                    status,
                    str(row_data.get("product_name", "")),
                    f"{float(row_data.get('stock_qty', 0) or 0.0):.2f}",
                    f"{float(row_data.get('stock_value', 0) or 0.0):.2f}",
                    last_sale if last_sale else "Never",
                    days_display,
                    str(row_data.get("oldest_batch_date", "") or ""),
                    f"{float(row_data.get('total_sold', 0) or 0.0):.2f}",
                ]

                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)

                    if c == 0:
                        if status == "DEAD":
                            item.setForeground(QColor("#b71c1c"))
                        else:
                            item.setForeground(QColor("#ef6c00"))
                    elif c == 5 and status != "DEAD":
                        ds = int(days_since or 0)
                        if ds >= 180:
                            item.setForeground(QColor("#b71c1c"))
                        elif ds >= 90:
                            item.setForeground(QColor("#c62828"))
                        elif ds >= 30:
                            item.setForeground(QColor("#ef6c00"))

                    table.setItem(r, c, item)

            if rows:
                totals_row_idx = len(rows)
                totals_values = [
                    "TOTAL",
                    f"Products: {len(rows)}",
                    f"{total_qty:.2f}",
                    f"{total_value:.2f}",
                    "",
                    "",
                    "",
                    "",
                ]
                for c, value in enumerate(totals_values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    item.setBackground(QColor("#fff3e0"))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    table.setItem(totals_row_idx, c, item)

            table.setSortingEnabled(True)
            table.sortItems(3, Qt.DescendingOrder)
            summary_label.setText(
                f"Rows: {len(rows)} | Dead: {dead_count} | Non-moving: {nonmoving_count} | "
                f"Qty: {total_qty:.2f} | Value: {total_value:.2f}"
            )

            if not rows:
                summary_label.setText("Rows: 0 | No dead/non-moving stock found for selected threshold/view.")

        reload_btn.clicked.connect(reload_data)
        threshold_combo.currentIndexChanged.connect(lambda _: reload_data())
        view_combo.currentIndexChanged.connect(lambda _: reload_data())
        reload_data()

        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)
        dialog.exec()


    def open_stock_movement_reference(self, reference: str, movement_type: str):
        ref = (reference or "").strip().upper()
        if not ref:
            return

        if ref.startswith("SALE#"):
            self.show_reference_detail_dialog(
                title=f"Sales Detail ({ref})",
                rows=self.fetch_sales_reference_details(ref)
            )
            return

        if ref.startswith("SR#"):
            self.show_reference_detail_dialog(
                title=f"Sales Return Detail ({ref})",
                rows=self.fetch_sales_return_reference_details(ref)
            )
            return

        if ref.startswith("PR#"):
            self.show_reference_detail_dialog(
                title=f"Purchase Return Detail ({ref})",
                rows=self.fetch_purchase_return_reference_details(ref)
            )
            return

        if ref.startswith("ADJ#"):
            self.show_reference_detail_dialog(
                title=f"Inventory Adjustment Detail ({ref})",
                rows=self.fetch_adjustment_reference_details(ref)
            )
            return

        if ref.startswith("PI#"):
            self.show_reference_detail_dialog(
                title=f"Purchase Item Detail ({ref})",
                rows=self.fetch_purchase_item_reference_details(ref)
            )
            return

        if ref.startswith("BATCH#"):
            self.show_reference_detail_dialog(
                title=f"Batch Detail ({ref})",
                rows=self.fetch_batch_reference_details(ref)
            )
            return

        self.show_reference_detail_dialog(
            title=f"Movement Detail ({movement_type})",
            rows=[("Reference", reference), ("Type", movement_type)]
        )


    def parse_reference_id(self, reference: str, prefix: str):
        upper_ref = (reference or "").strip().upper()
        if not upper_ref.startswith(prefix):
            return None

        try:
            return int(upper_ref.replace(prefix, "", 1))
        except ValueError:
            return None


    def fetch_sales_reference_details(self, reference: str):
        sales_id = self.parse_reference_id(reference, "SALE#")
        if sales_id is None:
            return [("Error", "Invalid sales reference")]
        rows = report_service.ReportService().get_sales_reference_details(sales_id)
        if rows:
            return rows
        return [("Not Found", f"No sales record for {reference}")]


    def fetch_sales_return_reference_details(self, reference: str):
        return_id = self.parse_reference_id(reference, "SR#")
        if return_id is None:
            return [("Error", "Invalid sales return reference")]
        rows = report_service.ReportService().get_sales_return_reference_details(return_id)
        if rows:
            return rows
        return [("Not Found", f"No sales return record for {reference}")]


    def fetch_purchase_return_reference_details(self, reference: str):
        return_id = self.parse_reference_id(reference, "PR#")
        if return_id is None:
            return [("Error", "Invalid purchase return reference")]
        rows = report_service.ReportService().get_purchase_return_reference_details(return_id)
        if rows:
            return rows
        return [("Not Found", f"No purchase return record for {reference}")]


    def fetch_adjustment_reference_details(self, reference: str):
        adjustment_id = self.parse_reference_id(reference, "ADJ#")
        if adjustment_id is None:
            return [("Error", "Invalid adjustment reference")]
        rows = report_service.ReportService().get_adjustment_reference_details(adjustment_id)
        if rows:
            return rows
        return [("Not Found", f"No adjustment record for {reference}")]


    def fetch_purchase_item_reference_details(self, reference: str):
        purchase_item_id = self.parse_reference_id(reference, "PI#")
        if purchase_item_id is None:
            return [("Error", "Invalid purchase item reference")]
        rows = report_service.ReportService().get_purchase_item_reference_details(purchase_item_id)
        if rows:
            return rows
        return [("Not Found", f"No purchase item record for {reference}")]

    def fetch_purchase_reference_details(self, purchase_id):
        try:
            purchase_id = int(purchase_id)
        except Exception:
            return [("Error", "Invalid purchase reference")]
        rows = report_service.ReportService().get_purchase_reference_details(purchase_id)
        if rows:
            return rows
        return [("Not Found", f"No purchase record for ID {purchase_id}")]

    def fetch_po_reference_details(self, po_id):
        try:
            po_id = int(po_id)
        except Exception:
            return [("Error", "Invalid PO reference")]
        rows = report_service.ReportService().get_po_reference_details(po_id)
        if rows:
            return rows
        return [("Not Found", f"No purchase order found for ID {po_id}")]

    def fetch_grn_reference_details(self, grn_id):
        try:
            grn_id = int(grn_id)
        except Exception:
            return [("Error", "Invalid GRN reference")]
        rows = report_service.ReportService().get_grn_reference_details(grn_id)
        if rows:
            return rows
        return [("Not Found", f"No GRN found for ID {grn_id}")]

    def fetch_customer_transaction_reference_details(self, txn_id):
        try:
            txn_id = int(txn_id)
        except Exception:
            return [("Error", "Invalid receipt reference")]
        rows = report_service.ReportService().get_customer_transaction_reference_details(txn_id)
        if rows:
            return rows
        return [("Not Found", f"No receipt found for ID {txn_id}")]

    def fetch_price_change_reference_details(self, change_id):
        try:
            change_id = int(change_id)
        except Exception:
            return [("Error", "Invalid price change reference")]
        rows = report_service.ReportService().get_price_change_reference_details(change_id)
        if rows:
            return rows
        return [("Not Found", f"No price change found for ID {change_id}")]

    def fetch_daily_session_reference_details(self, session_id):
        try:
            session_id = int(session_id)
        except Exception:
            return [("Error", "Invalid session reference")]
        rows = report_service.ReportService().get_daily_session_reference_details(session_id)
        if rows:
            return rows
        return [("Not Found", f"No daily session found for ID {session_id}")]


    def fetch_batch_reference_details(self, reference: str):
        batch_id = self.parse_reference_id(reference, "BATCH#")
        if batch_id is None:
            return [("Error", "Invalid batch reference")]
        rows = report_service.ReportService().get_batch_reference_details(batch_id)
        if rows:
            return rows
        return [("Not Found", f"No batch record for {reference}")]


    def show_activity_log_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QLabel, QPushButton, QLineEdit
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Activity Log")
        dialog.resize(1300, 680)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        # --- Filter bar ---
        filter_row = QHBoxLayout()

        duration_combo = QComboBox()
        duration_combo.addItems(["Today", "Week", "Month", "Year", "All"])
        duration_combo.setCurrentIndex(2)
        duration_combo.setFixedWidth(130)

        category_combo = QComboBox()
        category_combo.addItems(["All Categories", "login", "price", "stock", "sales", "purchase"])
        category_combo.setFixedWidth(160)

        user_edit = QLineEdit()
        user_edit.setPlaceholderText("Filter by user...")
        user_edit.setFixedWidth(180)

        reload_btn = QPushButton("Reload")

        filter_row.addWidget(QLabel("Duration:"))
        filter_row.addWidget(duration_combo)
        filter_row.addSpacing(12)
        filter_row.addWidget(QLabel("Category:"))
        filter_row.addWidget(category_combo)
        filter_row.addSpacing(12)
        filter_row.addWidget(QLabel("User:"))
        filter_row.addWidget(user_edit)
        filter_row.addSpacing(12)
        filter_row.addWidget(reload_btn)
        filter_row.addStretch()
        header_layout.addLayout(filter_row)

        # --- Table ---
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Category", "Action",
            "Entity", "Entity ID", "Note", "Previous", "New"
        ])
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        content_layout.addWidget(table)

        hint = QLabel("Tip: rows are ordered newest first")
        hint.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        content_layout.addWidget(hint)

        CATEGORY_COLORS = {
            "price":    QColor(255, 243, 205),   # soft yellow
            "stock":    QColor(209, 236, 241),   # soft blue
            "login":    QColor(212, 237, 218),   # soft green
            "sales":    QColor(248, 215, 218),   # soft red/salmon
            "purchase": QColor(226, 212, 243),   # soft purple
        }

        def reload_data():
            dur_map = {"Today": "today", "Week": "week", "Month": "month", "Year": "year", "All": "all"}
            duration = dur_map.get(duration_combo.currentText(), "month")
            cat_text = category_combo.currentText()
            category = None if cat_text == "All Categories" else cat_text
            username_filter = user_edit.text().strip() or None

            rows = report_service.ReportService().get_activity_log(
                duration=duration,
                category=category,
                username=username_filter,
            )

            table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                values = [
                    row["timestamp"], row["username"], row["category"], row["action"],
                    row["entity_type"], row["entity_id"], row["note"],
                    row["previous_value"], row["new_value"],
                ]
                row_color = CATEGORY_COLORS.get(row["category"].lower())
                for c, val in enumerate(values):
                    item = QTableWidgetItem(str(val))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if row_color:
                        item.setBackground(row_color)
                    table.setItem(r, c, item)

            table.resizeColumnsToContents()
            table.horizontalHeader().setStretchLastSection(True)

        reload_btn.clicked.connect(reload_data)
        duration_combo.currentIndexChanged.connect(reload_data)
        category_combo.currentIndexChanged.connect(reload_data)

        reload_data()

        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)
        dialog.exec()


    def show_reference_detail_dialog(self, title: str, rows):
        from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QLabel, QPushButton
        from PySide6.QtCore import Qt

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(700, 420)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        heading = QLabel(title)
        heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        header_layout.addWidget(heading)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Field", "Value"])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setRowCount(len(rows or []))

        for row_index, row_data in enumerate(rows or []):
            field_item = QTableWidgetItem(str(row_data[0]))
            value_item = QTableWidgetItem(str(row_data[1]))
            field_item.setFlags(field_item.flags() ^ Qt.ItemIsEditable)
            value_item.setFlags(value_item.flags() ^ Qt.ItemIsEditable)
            table.setItem(row_index, 0, field_item)
            table.setItem(row_index, 1, value_item)

        table.resizeColumnsToContents()
        content_layout.addWidget(table)
        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)
        dialog.exec()
    
    
    
    
    def create_supplier_card(self):
        # Create the card container
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        
        # 2. Create the VBoxLayout for the 2 lines of info
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(10)
        
        pay_label = QLabel(f'You have to PAY')
        self.supplier_payable = QLabel()
        
        spacer_label = QLabel()
        
        receive_label = QLabel(f'You have to RECEIVE')
        self.supplier_receivable = QLabel()
        
        
        card_layout.addWidget(pay_label, 3)
        card_layout.addWidget(self.supplier_payable, 1)
        
        card_layout.addWidget(spacer_label, 4)
        
        card_layout.addWidget(receive_label, 3)
        card_layout.addWidget(self.supplier_receivable, 1)

        aging_btn = QPushButton("View Payable Aging")
        aging_btn.setCursor(QCursor(Qt.PointingHandCursor))
        aging_btn.setStyleSheet(self.report_action_btn_style())
        aging_btn.clicked.connect(self.show_supplier_payable_aging_dialog)
        card_layout.addWidget(aging_btn, 2)

        forecast_btn = QPushButton("Payment Schedule")
        forecast_btn.setCursor(QCursor(Qt.PointingHandCursor))
        forecast_btn.setStyleSheet(self.report_action_btn_style())
        forecast_btn.clicked.connect(self.show_supplier_payable_forecast_dialog)
        card_layout.addWidget(forecast_btn, 2)
        
        payable, receiveable = report_service.ReportService().get_supplier_balances()

        self.supplier_payable.setText(f"{payable:,.2f}")
        self.supplier_receivable.setText(f"{receiveable:,.2f}")

        
        return card
    
    
    
    def create_customer_card(self):
        # Create the card container
        card = QFrame()
        card.setStyleSheet(self.report_card_style())
        
        # 2. Create the VBoxLayout for the 2 lines of info
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(10)
        
        pay_label = QLabel(f'You have to PAY')
        self.customer_payable = QLabel()
        
        spacer_label = QLabel()
        
        receive_label = QLabel(f'You have to RECEIVE')
        self.customer_receivable = QLabel()
        
        
        card_layout.addWidget(pay_label, 3)
        card_layout.addWidget(self.customer_payable, 1)

        card_layout.addWidget(spacer_label, 4)

        card_layout.addWidget(receive_label, 3)
        card_layout.addWidget(self.customer_receivable, 1)

        aging_btn = QPushButton("View Aging Report")
        aging_btn.setCursor(QCursor(Qt.PointingHandCursor))
        aging_btn.setStyleSheet(self.report_action_btn_style())
        aging_btn.clicked.connect(self.show_receivable_aging_dialog)
        card_layout.addWidget(aging_btn, 2)

        forecast_btn = QPushButton("Payment Forecast")
        forecast_btn.setCursor(QCursor(Qt.PointingHandCursor))
        forecast_btn.setStyleSheet(self.report_action_btn_style())
        forecast_btn.clicked.connect(self.show_receivable_forecast_dialog)
        card_layout.addWidget(forecast_btn, 2)

        receivable, payable = report_service.ReportService().get_customer_balances()


        self.customer_payable.setText(f"{payable:,.2f}")
        self.customer_receivable.setText(f"{receivable:,.2f}")
        
        
        
        
        return card
    
    
    
    def show_receivable_aging_dialog(self):
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
            QLabel, QPushButton, QHeaderView, QLineEdit
        )
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor, QFont

        dialog = QDialog(self)
        dialog.setWindowTitle("Customer Receivable Aging Report")
        dialog.resize(1100, 580)

        layout = QVBoxLayout(dialog)

        # ── Header info row ────────────────────────────────────────────────
        info_row = QHBoxLayout()
        from datetime import date as _date
        info_row.addWidget(QLabel(f"As of: {_date.today().strftime('%B %d, %Y')}"))
        info_row.addStretch()
        switch_btn = QPushButton("Open Forecast")
        switch_btn.setCursor(Qt.PointingHandCursor)
        info_row.addWidget(switch_btn)
        reload_btn = QPushButton("Reload", objectName="TopRightButton")
        reload_btn.setCursor(Qt.PointingHandCursor)
        info_row.addWidget(reload_btn)
        layout.addLayout(info_row)

        # ── Customer filter row ────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Customer"))
        customer_filter = QLineEdit()
        customer_filter.setPlaceholderText("Type customer name to filter...")
        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.setCursor(Qt.PointingHandCursor)
        filter_row.addWidget(customer_filter, 1)
        filter_row.addWidget(clear_filter_btn)
        layout.addLayout(filter_row)

        # ── Bucket legend ──────────────────────────────────────────────────
        legend_row = QHBoxLayout()
        for label_text, color in [
            ("■ Not Yet Due", "#2e7d32"),
            ("■ 1–30 days",  "#f9a825"),
            ("■ 31–60 days", "#ef6c00"),
            ("■ 61–90 days", "#c62828"),
            ("■ 90+ days",   "#4a148c"),
            ("■ No Due Date","#546e7a"),
        ]:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {color}; font-weight: bold; margin-right: 12px;")
            legend_row.addWidget(lbl)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        # ── Summary table ──────────────────────────────────────────────────
        COLUMNS = ["Customer", "Total Due", "Not Yet Due", "1–30 Days", "31–60 Days", "61–90 Days", "90+ Days", "No Due Date"]
        BUCKET_COLORS = {
            2: QColor("#2e7d32"),
            3: QColor("#f9a825"),
            4: QColor("#ef6c00"),
            5: QColor("#c62828"),
            6: QColor("#4a148c"),
            7: QColor("#546e7a"),
        }

        table = QTableWidget()
        table.setColumnCount(len(COLUMNS))
        table.setHorizontalHeaderLabels(COLUMNS)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(table)

        hint = QLabel("Double-click a row to see individual invoices for that customer.")
        hint.setStyleSheet("color: #777; font-size: 11px;")
        layout.addWidget(hint)

        # ── Totals footer ──────────────────────────────────────────────────
        totals_row = QHBoxLayout()
        totals_labels = {}
        for key in ["total", "current", "130", "3160", "6190", "90p", "nodup"]:
            lbl = QLabel("0.00")
            lbl.setStyleSheet("font-weight: bold;")
            totals_labels[key] = lbl
        totals_row.addWidget(QLabel("Totals:"))
        for key in ["total", "current", "130", "3160", "6190", "90p", "nodup"]:
            totals_row.addWidget(totals_labels[key], 1)
        layout.addLayout(totals_row)

        # ── Load data ──────────────────────────────────────────────────────
        aging_rows = []
        visible_aging_rows = []

        def render_aging_rows(rows):
            nonlocal visible_aging_rows
            visible_aging_rows = rows
            table.setRowCount(len(rows))

            col_totals = [0.0] * 7

            for r, row in enumerate(rows):
                values = [
                    row["customer_name"],
                    f"{row['total_due']:,.2f}",
                    f"{row['current_due']:,.2f}",
                    f"{row['days_1_30']:,.2f}",
                    f"{row['days_31_60']:,.2f}",
                    f"{row['days_61_90']:,.2f}",
                    f"{row['days_90plus']:,.2f}",
                    f"{row['no_due_date']:,.2f}",
                ]

                col_totals[0] += row["total_due"]
                col_totals[1] += row["current_due"]
                col_totals[2] += row["days_1_30"]
                col_totals[3] += row["days_31_60"]
                col_totals[4] += row["days_61_90"]
                col_totals[5] += row["days_90plus"]
                col_totals[6] += row["no_due_date"]

                for c, val in enumerate(values):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter if c > 0 else Qt.AlignLeft | Qt.AlignVCenter)
                    if c in BUCKET_COLORS and row[
                        ["total_due", "current_due", "days_1_30", "days_31_60", "days_61_90", "days_90plus", "no_due_date"][c - 1]
                    ] > 0:
                        item.setForeground(BUCKET_COLORS[c])
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                    table.setItem(r, c, item)

            table.resizeColumnsToContents()
            keys_order = ["total", "current", "130", "3160", "6190", "90p", "nodup"]
            for i, key in enumerate(keys_order):
                totals_labels[key].setText(f"{col_totals[i]:,.2f}")

        def apply_customer_filter():
            text = customer_filter.text().strip().lower()
            if not text:
                render_aging_rows(aging_rows)
                return
            filtered = [
                row for row in aging_rows
                if text in str(row.get("customer_name", "")).lower()
            ]
            render_aging_rows(filtered)

        def reload_data():
            nonlocal aging_rows
            aging_rows = report_service.ReportService().get_receivable_aging()
            apply_customer_filter()

        # ── Drill-down: individual invoices ────────────────────────────────
        def on_row_double_click(row, _col):
            if row >= len(visible_aging_rows):
                return
            customer = visible_aging_rows[row]
            cust_id   = customer["customer_id"]
            cust_name = customer["customer_name"]

            invoices = report_service.ReportService().get_receivable_aging_invoices(cust_id)
            if not invoices:
                from PySide6.QtWidgets import QMessageBox
                AppMessageBox.information(dialog, "No Data", f"No outstanding invoices found for {cust_name}.")
                return

            inv_dialog = QDialog(dialog)
            inv_dialog.setWindowTitle(f"Outstanding Invoices — {cust_name}")
            inv_dialog.resize(800, 450)

            inv_layout = QVBoxLayout(inv_dialog)
            inv_table  = QTableWidget()
            inv_table.setColumnCount(6)
            inv_table.setHorizontalHeaderLabels(
                ["Invoice #", "Date", "Total", "Received", "Outstanding", "Due Date / Status"]
            )
            inv_table.horizontalHeader().setStretchLastSection(True)
            inv_table.verticalHeader().setVisible(False)
            inv_table.setAlternatingRowColors(True)
            inv_table.setEditTriggers(QTableWidget.NoEditTriggers)
            inv_layout.addWidget(inv_table)

            inv_table.setRowCount(len(invoices))
            for r, inv in enumerate(invoices):
                status = inv["aging_status"]
                row_values = [
                    f"#{inv['invoice_id']}",
                    inv["invoice_date"],
                    f"{inv['total']:,.2f}",
                    f"{inv['received']:,.2f}",
                    f"{inv['receiveable']:,.2f}",
                    f"{inv['due_date'] or '—'}  ({status})",
                ]
                for c, val in enumerate(row_values):
                    item = QTableWidgetItem(val)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if c == 5:
                        if "overdue" in status:
                            item.setForeground(QColor("#c62828"))
                        elif status == "Not Yet Due":
                            item.setForeground(QColor("#2e7d32"))
                    inv_table.setItem(r, c, item)

            inv_table.resizeColumnsToContents()
            inv_dialog.exec()

        def open_forecast_dialog():
            dialog.done(0)
            self.show_receivable_forecast_dialog()

        reload_btn.clicked.connect(reload_data)
        switch_btn.clicked.connect(open_forecast_dialog)
        customer_filter.textChanged.connect(apply_customer_filter)
        clear_filter_btn.clicked.connect(customer_filter.clear)
        table.cellDoubleClicked.connect(on_row_double_click)

        reload_data()
        dialog.exec()

    def show_receivable_forecast_dialog(self):
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
            QLabel, QPushButton, QHeaderView, QLineEdit
        )
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Receivable Payment Forecast")
        dialog.resize(1200, 580)

        layout = QVBoxLayout(dialog)

        header_row = QHBoxLayout()
        from datetime import date as _date
        header_row.addWidget(QLabel(f"As of: {_date.today().strftime('%B %d, %Y')}"))
        header_row.addStretch()
        switch_btn = QPushButton("Open Aging")
        switch_btn.setCursor(Qt.PointingHandCursor)
        header_row.addWidget(switch_btn)
        reload_btn = QPushButton("Reload", objectName="TopRightButton")
        reload_btn.setCursor(Qt.PointingHandCursor)
        header_row.addWidget(reload_btn)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Customer"))
        customer_filter = QLineEdit()
        customer_filter.setPlaceholderText("Type customer name to filter...")
        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.setCursor(Qt.PointingHandCursor)
        filter_row.addWidget(customer_filter, 1)
        filter_row.addWidget(clear_filter_btn)
        layout.addLayout(filter_row)

        legend_row = QHBoxLayout()
        for label_text, color in [
            ("■ Overdue", "#c62828"),
            ("■ Due in 0-7 days", "#2e7d32"),
            ("■ Due in 8-15 days", "#f9a825"),
            ("■ Due in 16-30 days", "#ef6c00"),
            ("■ Due next month", "#1565c0"),
            ("■ Due later", "#6a1b9a"),
            ("■ No Due Date", "#546e7a"),
        ]:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {color}; font-weight: bold; margin-right: 12px;")
            legend_row.addWidget(lbl)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        table = QTableWidget()
        columns = [
            "Customer", "Total Due", "Overdue", "0-7 Days", "8-15 Days", "16-30 Days", "Next Month", "Due Later", "No Due Date"
        ]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(table)

        hint = QLabel("Double-click a row to see invoice-level forecast buckets for that customer.")
        hint.setStyleSheet("color: #777; font-size: 11px;")
        layout.addWidget(hint)

        totals_row = QHBoxLayout()
        totals_labels = {}
        total_keys = ["total", "overdue", "d07", "d815", "d1630", "next_month", "due_later", "no_due"]
        totals_row.addWidget(QLabel("Totals:"))
        for key in total_keys:
            lbl = QLabel("0.00")
            lbl.setStyleSheet("font-weight: bold;")
            totals_labels[key] = lbl
            totals_row.addWidget(lbl, 1)
        layout.addLayout(totals_row)

        forecast_rows = []
        visible_forecast_rows = []

        bucket_colors = {
            2: QColor("#c62828"),
            3: QColor("#2e7d32"),
            4: QColor("#f9a825"),
            5: QColor("#ef6c00"),
            6: QColor("#1565c0"),
            7: QColor("#6a1b9a"),
            8: QColor("#546e7a"),
        }
        value_keys = ["total_due", "overdue", "due_0_7", "due_8_15", "due_16_30", "due_next_month", "due_later", "no_due_date"]

        def render_forecast_rows(rows):
            nonlocal visible_forecast_rows
            visible_forecast_rows = rows
            table.setRowCount(len(rows))

            sums = {k: 0.0 for k in total_keys}

            for r, row in enumerate(rows):
                row_values = [
                    row["customer_name"],
                    f"{row['total_due']:,.2f}",
                    f"{row['overdue']:,.2f}",
                    f"{row['due_0_7']:,.2f}",
                    f"{row['due_8_15']:,.2f}",
                    f"{row['due_16_30']:,.2f}",
                    f"{row['due_next_month']:,.2f}",
                    f"{row['due_later']:,.2f}",
                    f"{row['no_due_date']:,.2f}",
                ]

                sums["total"] += row["total_due"]
                sums["overdue"] += row["overdue"]
                sums["d07"] += row["due_0_7"]
                sums["d815"] += row["due_8_15"]
                sums["d1630"] += row["due_16_30"]
                sums["next_month"] += row["due_next_month"]
                sums["due_later"] += row["due_later"]
                sums["no_due"] += row["no_due_date"]

                for c, value in enumerate(row_values):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter if c == 0 else Qt.AlignRight | Qt.AlignVCenter)
                    if c in bucket_colors and row[value_keys[c - 1]] > 0:
                        item.setForeground(bucket_colors[c])
                    table.setItem(r, c, item)

            for key in total_keys:
                totals_labels[key].setText(f"{sums[key]:,.2f}")
            table.resizeColumnsToContents()

        def apply_customer_filter():
            text = customer_filter.text().strip().lower()
            if not text:
                render_forecast_rows(forecast_rows)
                return
            filtered = [
                row for row in forecast_rows
                if text in str(row.get("customer_name", "")).lower()
            ]
            render_forecast_rows(filtered)

        def reload_data():
            nonlocal forecast_rows
            forecast_rows = report_service.ReportService().get_receivable_forecast()
            apply_customer_filter()

        def on_row_double_click(row, _col):
            if row >= len(visible_forecast_rows):
                return

            customer = visible_forecast_rows[row]
            cust_id = customer["customer_id"]
            cust_name = customer["customer_name"]
            invoices = report_service.ReportService().get_receivable_forecast_invoices(cust_id)

            if not invoices:
                return

            inv_dialog = QDialog(dialog)
            inv_dialog.setWindowTitle(f"Forecast Invoices - {cust_name}")
            inv_dialog.resize(860, 450)

            inv_layout = QVBoxLayout(inv_dialog)
            inv_table = QTableWidget()
            inv_table.setColumnCount(6)
            inv_table.setHorizontalHeaderLabels([
                "Invoice #", "Date", "Total", "Received", "Outstanding", "Due Date / Forecast Bucket"
            ])
            inv_table.horizontalHeader().setStretchLastSection(True)
            inv_table.verticalHeader().setVisible(False)
            inv_table.setAlternatingRowColors(True)
            inv_table.setEditTriggers(QTableWidget.NoEditTriggers)
            inv_layout.addWidget(inv_table)

            inv_table.setRowCount(len(invoices))
            for r, inv in enumerate(invoices):
                bucket = inv["forecast_bucket"]
                due_text = inv["due_date"] if inv["due_date"] else "-"
                values = [
                    f"#{inv['invoice_id']}",
                    inv["invoice_date"],
                    f"{inv['total']:,.2f}",
                    f"{inv['received']:,.2f}",
                    f"{inv['receiveable']:,.2f}",
                    f"{due_text} ({bucket})",
                ]

                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if c == 5:
                        if bucket == "Overdue":
                            item.setForeground(QColor("#c62828"))
                        elif bucket == "Due in 0-7 days":
                            item.setForeground(QColor("#2e7d32"))
                        elif bucket == "Due in 8-15 days":
                            item.setForeground(QColor("#f9a825"))
                        elif bucket == "Due in 16-30 days":
                            item.setForeground(QColor("#ef6c00"))
                        elif bucket == "Due next month":
                            item.setForeground(QColor("#1565c0"))
                        elif bucket == "Due later":
                            item.setForeground(QColor("#6a1b9a"))
                    inv_table.setItem(r, c, item)

            inv_table.resizeColumnsToContents()
            inv_dialog.exec()

        def open_aging_dialog():
            dialog.done(0)
            self.show_receivable_aging_dialog()

        reload_btn.clicked.connect(reload_data)
        switch_btn.clicked.connect(open_aging_dialog)
        customer_filter.textChanged.connect(apply_customer_filter)
        clear_filter_btn.clicked.connect(customer_filter.clear)
        table.cellDoubleClicked.connect(on_row_double_click)

        reload_data()
        dialog.exec()

    def show_supplier_payable_aging_dialog(self):
        """Display supplier payable aging report with drill-down capability."""
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
            QLabel, QPushButton, QHeaderView, QLineEdit
        )
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Supplier Payable Aging Report")
        dialog.setGeometry(100, 100, 1200, 600)
        layout = QVBoxLayout(dialog)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Type supplier name to filter..."))
        supplier_filter = QLineEdit()
        supplier_filter.setPlaceholderText("Type supplier name to filter...")
        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.setCursor(QCursor(Qt.PointingHandCursor))
        filter_row.addWidget(supplier_filter, 1)
        filter_row.addWidget(clear_filter_btn)
        layout.addLayout(filter_row)

        # Legend row
        legend_row = QHBoxLayout()
        legend_items = [
            ("Current Due", "#2e7d32"),
            ("1-30 Days", "#f9a825"),
            ("31-60 Days", "#ef6c00"),
            ("61-90 Days", "#ff6f00"),
            ("90+ Days", "#c62828"),
            ("No Due Date", "#808080"),
        ]
        for text, color in legend_items:
            legend_label = QLabel(text)
            legend_label.setStyleSheet(f"color: {color}; font-weight: bold; margin: 0 10px;")
            legend_row.addWidget(legend_label)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        # Summary table
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "Supplier", "Total Due", "Current Due", "1-30 Days", "31-60 Days",
            "61-90 Days", "90+ Days", "No Due Date", "Actions"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        # Summary labels
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(QLabel("Total Payables:"))
        total_label = QLabel("0.00")
        total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(total_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Buttons
        button_layout = QHBoxLayout()
        reload_btn = QPushButton("Reload")
        reload_btn.setCursor(QCursor(Qt.PointingHandCursor))
        reload_btn.setStyleSheet("background: #2e7d32; color: white; padding: 5px 15px; border-radius: 4px;")
        switch_btn = QPushButton("Open Forecast")
        switch_btn.setCursor(QCursor(Qt.PointingHandCursor))
        switch_btn.setStyleSheet("background: #004c72; color: white; padding: 5px 15px; border-radius: 4px;")
        button_layout.addStretch()
        button_layout.addWidget(reload_btn)
        button_layout.addWidget(switch_btn)
        layout.addLayout(button_layout)

        # Data tracking
        payable_aging_rows = []
        visible_payable_aging_rows = []

        def render_payable_aging_rows(rows):
            """Render aging rows to table with proper coloring."""
            table.setRowCount(len(rows))
            total = 0.0

            for r, row_data in enumerate(rows):
                total += row_data.get("total_due", 0)
                values = [
                    row_data.get("supplier_name", ""),
                    f"{row_data.get('total_due', 0):.2f}",
                    f"{row_data.get('current_due', 0):.2f}",
                    f"{row_data.get('days_1_30', 0):.2f}",
                    f"{row_data.get('days_31_60', 0):.2f}",
                    f"{row_data.get('days_61_90', 0):.2f}",
                    f"{row_data.get('days_90plus', 0):.2f}",
                    f"{row_data.get('no_due_date', 0):.2f}",
                    "View",
                ]

                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if c == 2:  # Current Due (green)
                        item.setForeground(QColor("#2e7d32"))
                    elif c == 3:  # 1-30 Days (amber)
                        item.setForeground(QColor("#f9a825"))
                    elif c == 4:  # 31-60 Days (orange)
                        item.setForeground(QColor("#ef6c00"))
                    elif c == 5:  # 61-90 Days (orange-red)
                        item.setForeground(QColor("#ff6f00"))
                    elif c == 6:  # 90+ Days (red)
                        item.setForeground(QColor("#c62828"))
                    elif c == 7:  # No Due Date (grey)
                        item.setForeground(QColor("#808080"))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    table.setItem(r, c, item)

            table.resizeColumnsToContents()
            total_label.setText(f"{total:.2f}")

        def apply_supplier_filter():
            """Filter rows by supplier name."""
            text = supplier_filter.text().strip().lower()
            if not text:
                render_payable_aging_rows(payable_aging_rows)
                visible_payable_aging_rows.clear()
                visible_payable_aging_rows.extend(payable_aging_rows)
                return
            filtered = [row for row in payable_aging_rows 
                       if text in str(row.get("supplier_name", "")).lower()]
            render_payable_aging_rows(filtered)
            visible_payable_aging_rows.clear()
            visible_payable_aging_rows.extend(filtered)

        def reload_data():
            nonlocal payable_aging_rows
            payable_aging_rows = report_service.ReportService().get_supplier_payable_aging()
            visible_payable_aging_rows.clear()
            visible_payable_aging_rows.extend(payable_aging_rows)
            render_payable_aging_rows(payable_aging_rows)

        def on_row_double_click(row, col):
            """Show invoice drill-down for selected supplier."""
            if row < 0 or row >= len(visible_payable_aging_rows):
                return
            supplier_row = visible_payable_aging_rows[row]
            supplier_id = supplier_row.get("supplier_id")
            if not supplier_id:
                return

            invoices = report_service.ReportService().get_supplier_payable_aging_invoices(supplier_id)
            if not invoices:
                return

            inv_dialog = QDialog(dialog)
            inv_dialog.setWindowTitle(f"Payable Invoices - {supplier_row.get('supplier_name', '')}")
            inv_dialog.setGeometry(150, 150, 1000, 400)
            inv_layout = QVBoxLayout(inv_dialog)

            inv_table = QTableWidget()
            inv_table.setColumnCount(7)
            inv_table.setHorizontalHeaderLabels([
                "PO#", "Date", "Total", "Paid", "Payable", "Due Date", "Status"
            ])
            inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            inv_layout.addWidget(inv_table)

            inv_table.setRowCount(len(invoices))
            for r, inv_row in enumerate(invoices):
                values = [
                    str(inv_row.get("invoice_id", "")),
                    str(inv_row.get("invoice_date", "")),
                    f"{inv_row.get('total', 0):.2f}",
                    f"{inv_row.get('paid', 0):.2f}",
                    f"{inv_row.get('payable', 0):.2f}",
                    str(inv_row.get("due_date", "")),
                    str(inv_row.get("aging_status", "")),
                ]
                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    status = str(inv_row.get("aging_status", ""))
                    if c == 6:
                        if "days overdue" in status:
                            item.setForeground(QColor("#c62828"))
                        elif status == "Not Yet Due":
                            item.setForeground(QColor("#2e7d32"))
                    inv_table.setItem(r, c, item)

            inv_table.resizeColumnsToContents()
            inv_dialog.exec()

        def open_forecast_dialog():
            dialog.done(0)
            self.show_supplier_payable_forecast_dialog()

        reload_btn.clicked.connect(reload_data)
        switch_btn.clicked.connect(open_forecast_dialog)
        supplier_filter.textChanged.connect(apply_supplier_filter)
        clear_filter_btn.clicked.connect(supplier_filter.clear)
        table.cellDoubleClicked.connect(on_row_double_click)

        reload_data()
        dialog.exec()

    def show_supplier_payable_forecast_dialog(self):
        """Display supplier payment forecast/schedule with drill-down capability."""
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
            QLabel, QPushButton, QHeaderView, QLineEdit
        )
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Supplier Payment Schedule")
        dialog.setGeometry(100, 100, 1400, 600)
        layout = QVBoxLayout(dialog)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Type supplier name to filter..."))
        supplier_filter = QLineEdit()
        supplier_filter.setPlaceholderText("Type supplier name to filter...")
        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.setCursor(QCursor(Qt.PointingHandCursor))
        filter_row.addWidget(supplier_filter, 1)
        filter_row.addWidget(clear_filter_btn)
        layout.addLayout(filter_row)

        # Legend row
        legend_row = QHBoxLayout()
        legend_items = [
            ("Overdue", "#c62828"),
            ("Due 0-7 Days", "#2e7d32"),
            ("Due 8-15 Days", "#f9a825"),
            ("Due 16-30 Days", "#ef6c00"),
            ("Next Month", "#1565c0"),
            ("Due Later", "#6a1b9a"),
            ("No Due Date", "#808080"),
        ]
        for text, color in legend_items:
            legend_label = QLabel(text)
            legend_label.setStyleSheet(f"color: {color}; font-weight: bold; margin: 0 10px;")
            legend_row.addWidget(legend_label)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        # Summary table
        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels([
            "Supplier", "Total Due", "Overdue", "0-7 Days", "8-15 Days",
            "16-30 Days", "Next Month", "Due Later", "No Due Date", "Actions"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        # Summary labels
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(QLabel("Total Payables:"))
        total_label = QLabel("0.00")
        total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(total_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Buttons
        button_layout = QHBoxLayout()
        reload_btn = QPushButton("Reload")
        reload_btn.setCursor(QCursor(Qt.PointingHandCursor))
        reload_btn.setStyleSheet("background: #2e7d32; color: white; padding: 5px 15px; border-radius: 4px;")
        switch_btn = QPushButton("Open Aging")
        switch_btn.setCursor(QCursor(Qt.PointingHandCursor))
        switch_btn.setStyleSheet("background: #7a0044; color: white; padding: 5px 15px; border-radius: 4px;")
        button_layout.addStretch()
        button_layout.addWidget(reload_btn)
        button_layout.addWidget(switch_btn)
        layout.addLayout(button_layout)

        # Data tracking
        forecast_rows = []
        visible_forecast_rows = []

        def render_forecast_rows(rows):
            """Render forecast rows to table with proper coloring."""
            table.setRowCount(len(rows))
            total = 0.0

            for r, row_data in enumerate(rows):
                total += row_data.get("total_due", 0)
                values = [
                    row_data.get("supplier_name", ""),
                    f"{row_data.get('total_due', 0):.2f}",
                    f"{row_data.get('overdue', 0):.2f}",
                    f"{row_data.get('due_0_7', 0):.2f}",
                    f"{row_data.get('due_8_15', 0):.2f}",
                    f"{row_data.get('due_16_30', 0):.2f}",
                    f"{row_data.get('due_next_month', 0):.2f}",
                    f"{row_data.get('due_later', 0):.2f}",
                    f"{row_data.get('no_due_date', 0):.2f}",
                    "View",
                ]

                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if c == 2:  # Overdue (red)
                        item.setForeground(QColor("#c62828"))
                    elif c == 3:  # 0-7 Days (green)
                        item.setForeground(QColor("#2e7d32"))
                    elif c == 4:  # 8-15 Days (amber)
                        item.setForeground(QColor("#f9a825"))
                    elif c == 5:  # 16-30 Days (orange)
                        item.setForeground(QColor("#ef6c00"))
                    elif c == 6:  # Next Month (blue)
                        item.setForeground(QColor("#1565c0"))
                    elif c == 7:  # Due Later (purple)
                        item.setForeground(QColor("#6a1b9a"))
                    elif c == 8:  # No Due Date (grey)
                        item.setForeground(QColor("#808080"))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    table.setItem(r, c, item)

            table.resizeColumnsToContents()
            total_label.setText(f"{total:.2f}")

        def apply_supplier_filter():
            """Filter rows by supplier name."""
            text = supplier_filter.text().strip().lower()
            if not text:
                render_forecast_rows(forecast_rows)
                visible_forecast_rows.clear()
                visible_forecast_rows.extend(forecast_rows)
                return
            filtered = [row for row in forecast_rows 
                       if text in str(row.get("supplier_name", "")).lower()]
            render_forecast_rows(filtered)
            visible_forecast_rows.clear()
            visible_forecast_rows.extend(filtered)

        def reload_data():
            nonlocal forecast_rows
            forecast_rows = report_service.ReportService().get_supplier_payable_forecast()
            visible_forecast_rows.clear()
            visible_forecast_rows.extend(forecast_rows)
            render_forecast_rows(forecast_rows)

        def on_row_double_click(row, col):
            """Show invoice drill-down for selected supplier."""
            if row < 0 or row >= len(visible_forecast_rows):
                return
            supplier_row = visible_forecast_rows[row]
            supplier_id = supplier_row.get("supplier_id")
            if not supplier_id:
                return

            invoices = report_service.ReportService().get_supplier_payable_forecast_invoices(supplier_id)
            if not invoices:
                return

            inv_dialog = QDialog(dialog)
            inv_dialog.setWindowTitle(f"Payment Schedule - {supplier_row.get('supplier_name', '')}")
            inv_dialog.setGeometry(150, 150, 1000, 400)
            inv_layout = QVBoxLayout(inv_dialog)

            inv_table = QTableWidget()
            inv_table.setColumnCount(7)
            inv_table.setHorizontalHeaderLabels([
                "PO#", "Date", "Total", "Paid", "Payable", "Due Date", "Schedule"
            ])
            inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            inv_layout.addWidget(inv_table)

            inv_table.setRowCount(len(invoices))
            for r, inv_row in enumerate(invoices):
                bucket = str(inv_row.get("forecast_bucket", ""))
                values = [
                    str(inv_row.get("invoice_id", "")),
                    str(inv_row.get("invoice_date", "")),
                    f"{inv_row.get('total', 0):.2f}",
                    f"{inv_row.get('paid', 0):.2f}",
                    f"{inv_row.get('payable', 0):.2f}",
                    str(inv_row.get("due_date", "")),
                    bucket,
                ]

                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if c == 6:
                        if bucket == "Overdue":
                            item.setForeground(QColor("#c62828"))
                        elif bucket == "Due in 0-7 days":
                            item.setForeground(QColor("#2e7d32"))
                        elif bucket == "Due in 8-15 days":
                            item.setForeground(QColor("#f9a825"))
                        elif bucket == "Due in 16-30 days":
                            item.setForeground(QColor("#ef6c00"))
                        elif bucket == "Due next month":
                            item.setForeground(QColor("#1565c0"))
                        elif bucket == "Due later":
                            item.setForeground(QColor("#6a1b9a"))
                    inv_table.setItem(r, c, item)

            inv_table.resizeColumnsToContents()
            inv_dialog.exec()

        def open_aging_dialog():
            dialog.done(0)
            self.show_supplier_payable_aging_dialog()

        reload_btn.clicked.connect(reload_data)
        switch_btn.clicked.connect(open_aging_dialog)
        supplier_filter.textChanged.connect(apply_supplier_filter)
        clear_filter_btn.clicked.connect(supplier_filter.clear)
        table.cellDoubleClicked.connect(on_row_double_click)

        reload_data()
        dialog.exec()

    def create_revenue_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())

        outer_layout = QVBoxLayout(card)
        outer_layout.setContentsMargins(12, 10, 12, 10)
        outer_layout.setSpacing(8)

        metrics_grid = QGridLayout()
        metrics_grid.setHorizontalSpacing(18)
        metrics_grid.setVerticalSpacing(8)

        metric_label_style = "color: #5A7183; font-size: 12px; font-weight: 700; padding-left: 0;"
        metric_value_style = "color: #223746; font-size: 18px; font-weight: 700; padding-left: 0;"

        def add_metric(row, col, title_text):
            title = QLabel(title_text)
            title.setStyleSheet(metric_label_style)
            value = QLabel("0.00")
            value.setStyleSheet(metric_value_style)
            block = QVBoxLayout()
            block.setSpacing(2)
            block.setContentsMargins(0, 0, 0, 0)
            block.addWidget(title)
            block.addWidget(value)
            metrics_grid.addLayout(block, row, col)
            return value

        self.known_revenue_data = add_metric(0, 0, "Known Revenue")
        self.cogs_data = add_metric(0, 1, "COGS")
        self.profit_data = add_metric(0, 2, "Known Gross Profit")
        self.net_profit_data = add_metric(0, 3, "Net Known Profit")

        self.gross_margin_data = add_metric(1, 0, "Gross Margin %")
        self.net_margin_data = add_metric(1, 1, "Net Margin %")
        self.unknown_revenue_data = add_metric(1, 2, "Revenue With Unknown Cost")
        self.coverage_data = add_metric(1, 3, "Known Cost Coverage %")

        outer_layout.addLayout(metrics_grid)

        footer_row = QHBoxLayout()
        footer_row.setSpacing(10)

        note_label = QLabel("Unknown-cost revenue is excluded from known profit until stock cost is assigned.")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #587083; font-size: 11px; padding-left: 0;")
        footer_row.addWidget(note_label, 1)

        product_profit_btn = QPushButton("Product-wise Profit")
        product_profit_btn.setCursor(QCursor(Qt.PointingHandCursor))
        product_profit_btn.setStyleSheet(self.report_action_btn_style())
        product_profit_btn.clicked.connect(self.show_product_profit_report_dialog)
        footer_row.addWidget(product_profit_btn)

        audit_btn = QPushButton("Profit Audit")
        audit_btn.setCursor(QCursor(Qt.PointingHandCursor))
        audit_btn.setStyleSheet(self.report_action_btn_style())
        audit_btn.clicked.connect(self.show_profit_audit_dialog)
        footer_row.addWidget(audit_btn)

        outer_layout.addLayout(footer_row)

        snapshot = report_service.ReportService().get_profit_loss_snapshot("today")
        revenue_known = snapshot["revenue_known"]
        total_cogs = snapshot["total_cogs"]
        gross_profit = snapshot["gross_profit"]
        revenue_unknown = snapshot["revenue_unknown"]
        gross_margin_pct = snapshot["gross_margin_pct"]
        coverage_pct = snapshot["coverage_pct"]
        net_profit = snapshot["net_profit"]
        net_margin_pct = snapshot["net_margin_pct"]

        self.known_revenue_data.setText(f"{revenue_known:.2f}")
        self.cogs_data.setText(f"{total_cogs:.2f}")
        self.profit_data.setText(f"{gross_profit:.2f}")
        self.gross_margin_data.setText(f"{gross_margin_pct:.2f}%")
        self.unknown_revenue_data.setText(f"{revenue_unknown:.2f}")
        self.net_profit_data.setText(f"{net_profit:.2f}")
        self.net_margin_data.setText(f"{net_margin_pct:.2f}%")
        self.coverage_data.setText(f"{coverage_pct:.2f}%")

        positive_style = "color: #2e7d32; font-size: 18px; font-weight: 700; padding-left: 0;"
        negative_style = "color: #c62828; font-size: 18px; font-weight: 700; padding-left: 0;"
        self.profit_data.setStyleSheet(negative_style if gross_profit < 0 else positive_style)
        self.net_profit_data.setStyleSheet(negative_style if net_profit < 0 else positive_style)

        return card

    def show_profit_audit_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QComboBox
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Profit Audit")
        dialog.setGeometry(130, 90, 1200, 640)
        layout = QVBoxLayout(dialog)

        heading_row = QHBoxLayout()
        heading = QLabel(f"Item-level Profitability ({self.current_duration_key.title()})")
        heading.setStyleSheet("font-weight: bold; font-size: 14px;")
        heading_row.addWidget(heading)
        heading_row.addStretch()

        view_mode_combo = QComboBox()
        view_mode_combo.addItems(["All Items", "Loss Only"])
        view_mode_combo.setFixedWidth(130)
        view_mode_combo.setCursor(QCursor(Qt.PointingHandCursor))
        heading_row.addWidget(QLabel("View:"))
        heading_row.addWidget(view_mode_combo)

        reload_btn = QPushButton("Reload")
        reload_btn.setCursor(QCursor(Qt.PointingHandCursor))
        reload_btn.setStyleSheet("background: #2e7d32; color: white; padding: 5px 12px; border-radius: 4px;")
        heading_row.addWidget(reload_btn)
        layout.addLayout(heading_row)

        info = QLabel("Tip: rows at top are worst known-profit performers. Coverage < 100% means part of revenue has unknown cost.")
        info.setStyleSheet("color: #555;")
        layout.addWidget(info)

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Product",
            "Qty Sold",
            "Known Revenue",
            "Known COGS",
            "Known Gross Profit",
            "Margin %",
            "Unknown Revenue",
            "Coverage %",
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSortingEnabled(True)
        layout.addWidget(table)

        summary_row = QHBoxLayout()
        self.audit_summary_label = QLabel("Rows: 0 | Loss Rows: 0")
        self.audit_summary_label.setStyleSheet("font-weight: bold;")
        summary_row.addWidget(self.audit_summary_label)
        summary_row.addStretch()
        layout.addLayout(summary_row)

        all_rows = []

        def render_rows(rows):
            table.setSortingEnabled(False)
            table.setRowCount(len(rows))
            loss_rows = 0

            for r, row in enumerate(rows):
                known_profit = float(row.get("known_profit", 0))
                margin_pct = float(row.get("margin_pct", 0))
                coverage_pct = float(row.get("coverage_pct", 0))

                if known_profit < 0:
                    loss_rows += 1

                values = [
                    str(row.get("product_name", "")),
                    f"{float(row.get('qty_sold', 0)):.2f}",
                    f"{float(row.get('known_revenue', 0)):.2f}",
                    f"{float(row.get('known_cogs', 0)):.2f}",
                    f"{known_profit:.2f}",
                    f"{margin_pct:.2f}%",
                    f"{float(row.get('unknown_revenue', 0)):.2f}",
                    f"{coverage_pct:.2f}%",
                ]

                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)

                    if c == 4:
                        item.setForeground(QColor("#c62828") if known_profit < 0 else QColor("#2e7d32"))
                    elif c == 5:
                        if margin_pct < 0:
                            item.setForeground(QColor("#c62828"))
                        elif margin_pct < 10:
                            item.setForeground(QColor("#ef6c00"))
                        else:
                            item.setForeground(QColor("#2e7d32"))
                    elif c == 7 and coverage_pct < 100:
                        item.setForeground(QColor("#6a1b9a"))

                    table.setItem(r, c, item)

            table.setSortingEnabled(True)
            table.sortItems(4, Qt.AscendingOrder)
            self.audit_summary_label.setText(f"Rows: {len(rows)} | Loss Rows: {loss_rows}")

        def apply_view_filter():
            if view_mode_combo.currentText() == "Loss Only":
                rows = [r for r in all_rows if float(r.get("known_profit", 0)) < 0]
            else:
                rows = all_rows

            render_rows(rows)
            if not rows:
                if self.current_duration_key == "today":
                    self.audit_summary_label.setText("Rows: 0 | No rows for today. Try changing duration to Month/All.")
                else:
                    self.audit_summary_label.setText("Rows: 0 | No rows matched current filter.")

        def reload_data():
            nonlocal all_rows
            all_rows = report_service.ReportService().get_profit_audit_rows(self.current_duration_key)
            apply_view_filter()

        reload_btn.clicked.connect(reload_data)
        view_mode_combo.currentIndexChanged.connect(lambda _: apply_view_filter())
        reload_data()
        dialog.exec()

    def show_product_profit_report_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QComboBox, QLineEdit
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Product-wise Profit Report")
        dialog.setGeometry(120, 85, 1240, 680)
        layout = QVBoxLayout(dialog)

        heading_row = QHBoxLayout()
        heading = QLabel(f"Product-wise Profit ({self.current_duration_key.title()})")
        heading.setStyleSheet("font-weight: bold; font-size: 14px;")
        heading_row.addWidget(heading)
        heading_row.addStretch()

        view_mode_combo = QComboBox()
        view_mode_combo.addItems(["All Products", "Loss Only", "Profit Only"])
        view_mode_combo.setFixedWidth(135)
        view_mode_combo.setCursor(QCursor(Qt.PointingHandCursor))
        heading_row.addWidget(QLabel("View:"))
        heading_row.addWidget(view_mode_combo)

        filter_input = QLineEdit()
        filter_input.setPlaceholderText("Filter product name...")
        filter_input.setFixedWidth(230)
        heading_row.addWidget(filter_input)

        reload_btn = QPushButton("Reload")
        reload_btn.setCursor(QCursor(Qt.PointingHandCursor))
        reload_btn.setStyleSheet("background: #2e7d32; color: white; padding: 5px 12px; border-radius: 4px;")
        heading_row.addWidget(reload_btn)
        layout.addLayout(heading_row)

        info = QLabel("Double-click a row to open product journey trend (Day/Week/Month) with quantity, known COGS/profit, and unknown-cost revenue coverage.")
        info.setStyleSheet("color: #555;")
        layout.addWidget(info)

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Product",
            "Qty Sold",
            "Known Revenue",
            "Known COGS",
            "Known Gross Profit",
            "Margin %",
            "Unknown Revenue",
            "Coverage %",
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSortingEnabled(True)
        layout.addWidget(table)

        summary_row = QHBoxLayout()
        summary_label = QLabel("Rows: 0 | Loss Rows: 0")
        summary_label.setStyleSheet("font-weight: bold;")
        summary_row.addWidget(summary_label)
        summary_row.addStretch()
        layout.addLayout(summary_row)

        all_rows = []

        def render_rows(rows):
            table.setSortingEnabled(False)
            table.setRowCount(len(rows))
            loss_rows = 0

            for r, row in enumerate(rows):
                known_profit = float(row.get("known_profit", 0))
                margin_pct = float(row.get("margin_pct", 0))
                coverage_pct = float(row.get("coverage_pct", 0))
                if known_profit < 0:
                    loss_rows += 1

                values = [
                    str(row.get("product_name", "")),
                    f"{float(row.get('qty_sold', 0)):.2f}",
                    f"{float(row.get('known_revenue', 0)):.2f}",
                    f"{float(row.get('known_cogs', 0)):.2f}",
                    f"{known_profit:.2f}",
                    f"{margin_pct:.2f}%",
                    f"{float(row.get('unknown_revenue', 0)):.2f}",
                    f"{coverage_pct:.2f}%",
                ]

                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if c == 0:
                        item.setData(Qt.UserRole, int(row.get("product_id", 0)))
                        item.setData(Qt.UserRole + 1, str(row.get("product_name", "")))

                    if c == 4:
                        item.setForeground(QColor("#c62828") if known_profit < 0 else QColor("#2e7d32"))
                    elif c == 5:
                        if margin_pct < 0:
                            item.setForeground(QColor("#c62828"))
                        elif margin_pct < 10:
                            item.setForeground(QColor("#ef6c00"))
                        else:
                            item.setForeground(QColor("#2e7d32"))
                    elif c == 7 and coverage_pct < 100:
                        item.setForeground(QColor("#6a1b9a"))

                    table.setItem(r, c, item)

            table.setSortingEnabled(True)
            summary_label.setText(f"Rows: {len(rows)} | Loss Rows: {loss_rows}")

        def apply_filters():
            mode = view_mode_combo.currentText()
            text = filter_input.text().strip().lower()
            rows = all_rows

            if mode == "Loss Only":
                rows = [r for r in rows if float(r.get("known_profit", 0)) < 0]
            elif mode == "Profit Only":
                rows = [r for r in rows if float(r.get("known_profit", 0)) > 0]

            if text:
                rows = [r for r in rows if text in str(r.get("product_name", "")).lower()]

            render_rows(rows)
            if not rows:
                summary_label.setText("Rows: 0 | No products matched current filter.")

        def reload_data():
            nonlocal all_rows
            all_rows = report_service.ReportService().get_profit_audit_rows(self.current_duration_key, limit=500)
            apply_filters()

        def open_product_journey(row, _col):
            name_item = table.item(row, 0)
            if name_item is None:
                return
            product_id = int(name_item.data(Qt.UserRole) or 0)
            product_name = str(name_item.data(Qt.UserRole + 1) or name_item.text())
            if product_id > 0:
                self.show_product_profit_journey_dialog(product_id, product_name)

        table.cellDoubleClicked.connect(open_product_journey)
        reload_btn.clicked.connect(reload_data)
        view_mode_combo.currentIndexChanged.connect(lambda _: apply_filters())
        filter_input.textChanged.connect(lambda _: apply_filters())

        reload_data()
        dialog.exec()

    def show_product_profit_journey_dialog(self, product_id, product_name):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QComboBox
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Product Journey")
        dialog.setGeometry(160, 110, 1140, 620)
        layout = QVBoxLayout(dialog)

        heading_row = QHBoxLayout()
        heading = QLabel(f"{product_name} | Profit Journey")
        heading.setStyleSheet("font-weight: bold; font-size: 14px;")
        heading_row.addWidget(heading)
        heading_row.addStretch()

        heading_row.addWidget(QLabel("Period:"))
        period_combo = QComboBox()
        period_combo.addItems(["Today", "This Week", "This Month", "This Year", "All Time"])
        period_combo.setFixedWidth(120)
        period_combo.setCursor(QCursor(Qt.PointingHandCursor))
        heading_row.addWidget(period_combo)

        heading_row.addWidget(QLabel("View:"))
        view_combo = QComboBox()
        view_combo.setFixedWidth(150)
        view_combo.setCursor(QCursor(Qt.PointingHandCursor))
        heading_row.addWidget(view_combo)

        reload_btn = QPushButton("Reload")
        reload_btn.setCursor(QCursor(Qt.PointingHandCursor))
        reload_btn.setStyleSheet("background: #2e7d32; color: white; padding: 5px 12px; border-radius: 4px;")
        heading_row.addWidget(reload_btn)
        layout.addLayout(heading_row)

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Period", "Qty Sold", "Known Revenue", "Known COGS",
            "Known Gross Profit", "Margin %", "Revenue With Unknown Cost", "Coverage %",
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSortingEnabled(True)
        layout.addWidget(table)

        summary_label = QLabel("Periods: 0 | Loss Periods: 0")
        summary_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(summary_label)

        period_key_map = {
            "Today": "today",
            "This Week": "week",
            "This Month": "month",
            "This Year": "year",
            "All Time": "all",
        }

        # Available view options per period — broader windows unlock coarser groupings
        view_options_map = {
            "today": ["Day by Day"],
            "week":  ["Day by Day"],
            "month": ["Day by Day", "Week by Week"],
            "year":  ["Day by Day", "Week by Week", "Month by Month"],
            "all":   ["Day by Day", "Week by Week", "Month by Month"],
        }

        group_value_map = {
            "Day by Day":       "day",
            "Week by Week":     "week",
            "Month by Month":   "month",
        }

        def update_view_combo():
            period_key = period_key_map.get(period_combo.currentText(), "month")
            options = view_options_map.get(period_key, ["Day by Day"])
            current = view_combo.currentText()
            view_combo.blockSignals(True)
            view_combo.clear()
            view_combo.addItems(options)
            idx = view_combo.findText(current)
            view_combo.setCurrentIndex(idx if idx >= 0 else 0)
            view_combo.setEnabled(len(options) > 1)
            view_combo.blockSignals(False)

        def densify_daily_rows(rows, period_key):
            period_map = {str(r.get("period", "")): r for r in rows}

            if period_key == "today":
                start_date = QDate.currentDate()
            elif period_key == "week":
                start_date = QDate.currentDate().addDays(-6)
            elif period_key == "month":
                start_date = QDate.currentDate().addDays(-29)
            else:
                return rows

            end_date = QDate.currentDate()
            dense = []
            d = start_date
            while d <= end_date:
                key = d.toString("yyyy-MM-dd")
                source = period_map.get(key, {})
                dense.append({
                    "period": key,
                    "qty_sold":        float(source.get("qty_sold", 0.0) or 0.0),
                    "known_revenue":   float(source.get("known_revenue", 0.0) or 0.0),
                    "known_cogs":      float(source.get("known_cogs", 0.0) or 0.0),
                    "known_profit":    float(source.get("known_profit", 0.0) or 0.0),
                    "margin_pct":      float(source.get("margin_pct", 0.0) or 0.0),
                    "unknown_revenue": float(source.get("unknown_revenue", 0.0) or 0.0),
                    "coverage_pct":    float(source.get("coverage_pct", 0.0) or 0.0),
                })
                d = d.addDays(1)

            return dense

        def reload_data():
            update_view_combo()
            period_key = period_key_map.get(period_combo.currentText(), "month")
            group_by = group_value_map.get(view_combo.currentText(), "day")

            rows = report_service.ReportService().get_product_profit_timeline(
                product_id=product_id,
                duration=period_key,
                group_by=group_by,
            )

            if group_by == "day" and period_key in ("today", "week", "month"):
                rows = densify_daily_rows(rows, period_key)

            # Compute totals for the summary row
            tot_qty      = sum(float(r.get("qty_sold", 0) or 0) for r in rows)
            tot_revenue  = sum(float(r.get("known_revenue", 0) or 0) for r in rows)
            tot_cogs     = sum(float(r.get("known_cogs", 0) or 0) for r in rows)
            tot_profit   = sum(float(r.get("known_profit", 0) or 0) for r in rows)
            tot_unknown  = sum(float(r.get("unknown_revenue", 0) or 0) for r in rows)
            tot_margin   = ((tot_profit / tot_revenue) * 100) if tot_revenue else 0.0
            tot_coverage = ((tot_revenue / (tot_revenue + tot_unknown)) * 100) if (tot_revenue + tot_unknown) else 0.0

            table.setSortingEnabled(False)
            table.setRowCount(len(rows) + (1 if rows else 0))
            loss_periods = 0

            for r, row in enumerate(rows):
                known_profit = float(row.get("known_profit", 0))
                margin_pct = float(row.get("margin_pct", 0))
                coverage_pct = float(row.get("coverage_pct", 0))
                if known_profit < 0:
                    loss_periods += 1

                values = [
                    str(row.get("period", "")),
                    f"{float(row.get('qty_sold', 0)):.2f}",
                    f"{float(row.get('known_revenue', 0)):.2f}",
                    f"{float(row.get('known_cogs', 0)):.2f}",
                    f"{known_profit:.2f}",
                    f"{margin_pct:.2f}%",
                    f"{float(row.get('unknown_revenue', 0)):.2f}",
                    f"{coverage_pct:.2f}%",
                ]

                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)

                    if c == 4:
                        item.setForeground(QColor("#c62828") if known_profit < 0 else QColor("#2e7d32"))
                    elif c == 5:
                        if margin_pct < 0:
                            item.setForeground(QColor("#c62828"))
                        elif margin_pct < 10:
                            item.setForeground(QColor("#ef6c00"))
                        else:
                            item.setForeground(QColor("#2e7d32"))
                    elif c == 7 and coverage_pct < 100:
                        item.setForeground(QColor("#6a1b9a"))

                    table.setItem(r, c, item)

            if rows:
                totals_row_idx = len(rows)
                totals_values = [
                    "TOTAL",
                    f"{tot_qty:.2f}",
                    f"{tot_revenue:.2f}",
                    f"{tot_cogs:.2f}",
                    f"{tot_profit:.2f}",
                    f"{tot_margin:.2f}%",
                    f"{tot_unknown:.2f}",
                    f"{tot_coverage:.2f}%",
                ]
                totals_bg = QColor("#e8f5e9") if tot_profit >= 0 else QColor("#ffebee")
                for c, value in enumerate(totals_values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    item.setBackground(totals_bg)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    if c == 4:
                        item.setForeground(QColor("#c62828") if tot_profit < 0 else QColor("#2e7d32"))
                    elif c == 5:
                        if tot_margin < 0:
                            item.setForeground(QColor("#c62828"))
                        elif tot_margin < 10:
                            item.setForeground(QColor("#ef6c00"))
                        else:
                            item.setForeground(QColor("#2e7d32"))
                    elif c == 7 and tot_coverage < 100:
                        item.setForeground(QColor("#6a1b9a"))
                    table.setItem(totals_row_idx, c, item)

            table.setSortingEnabled(True)
            table.sortItems(0, Qt.AscendingOrder)
            summary_label.setText(f"Periods: {len(rows)} | Loss Periods: {loss_periods}")
            if not rows:
                summary_label.setText("Periods: 0 | No sales found for selected period/view.")

        # Pre-select the period that matches the current page filter
        default_period = {
            "today": "Today", "week": "This Week", "month": "This Month",
            "year": "This Year", "all": "All Time",
        }.get(self.current_duration_key, "This Month")
        period_combo.setCurrentText(default_period)

        period_combo.currentIndexChanged.connect(lambda _: reload_data())
        view_combo.currentIndexChanged.connect(lambda _: reload_data())
        reload_btn.clicked.connect(reload_data)
        update_view_combo()
        reload_data()
        dialog.exec()
    
    
    
    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Showing Reports page")
        
        
        
        
        

        
        
        
    

    def get_today_data(self):
        
        print("Going to Populate Summary Totals for today")
        today = QDate.currentDate().toString("yyyy-MM-dd")
        totals = report_service.ReportService().get_summary_totals(today, today)
        self.set_overview_totals(
            str(round(totals["sales"], 2)),
            str(round(totals["purchase"], 2)),
            str(round(totals["expense"], 2)),
        )
        
    
    
    def get_past_seven_days_data(self):
        
        print("Going to Populate Summary Totals for past 7 days")
        today = QDate.currentDate()
        seven_days_ago = today.addDays(-6)  # Include today, so -6
        date_from = seven_days_ago.toString("yyyy-MM-dd")
        date_to = today.toString("yyyy-MM-dd")

        totals = report_service.ReportService().get_summary_totals(date_from, date_to)
        
        print("Totals for past 7 days:", totals)

        self.set_overview_totals(
            str(round(totals["sales"], 2)),
            str(round(totals["purchase"], 2)),
            str(round(totals["expense"], 2)),
        )
    
    
        
        


    def get_hourly_sales_data(self):
        return report_service.ReportService().get_hourly_sales_data()



    
    def get_monthly_sales_data(self):
        return report_service.ReportService().get_monthly_sales_data()




    def on_duration_changed(self, index):
        # Map combo box selection to your method's duration parameter
        duration_map = {
            0: "today",
            1: "week",
            2: "month",
            3: "year",
            4: "all",
        }
        duration_key = duration_map.get(index, "today")
        self.current_duration_key = duration_key

        overview_snapshot = report_service.ReportService().get_overview_totals_snapshot(duration_key)
        total_sales = overview_snapshot["total_sales"]
        total_purchase = overview_snapshot["total_purchase"]
        total_expenses = overview_snapshot["total_expenses"]
        self.set_overview_totals(
            f"{total_sales:.2f}",
            f"{total_purchase:.2f}",
            f"{total_expenses:.2f}",
        )
        # The old revenue/stock/dues summary widgets were removed when the
        # reports page was simplified into overview + category cards.
        # Keep the duration filter scoped to widgets that still exist.
        if all(
            hasattr(self, attr)
            for attr in (
                "known_revenue_data",
                "cogs_data",
                "profit_data",
                "gross_margin_data",
                "unknown_revenue_data",
                "net_profit_data",
                "net_margin_data",
                "coverage_data",
            )
        ):
            profit_snapshot = overview_snapshot["profit_snapshot"]
            revenue_known = profit_snapshot["revenue_known"]
            total_cogs = profit_snapshot["total_cogs"]
            gross_profit = profit_snapshot["gross_profit"]
            revenue_unknown = profit_snapshot["revenue_unknown"]
            gross_margin_pct = profit_snapshot["gross_margin_pct"]
            coverage_pct = profit_snapshot["coverage_pct"]
            net_profit = profit_snapshot["net_profit"]
            net_margin_pct = profit_snapshot["net_margin_pct"]

            self.known_revenue_data.setText(f"{revenue_known:.2f}")
            self.cogs_data.setText(f"{total_cogs:.2f}")
            self.profit_data.setText(f"{gross_profit:.2f}")
            self.gross_margin_data.setText(f"{gross_margin_pct:.2f}%")
            self.unknown_revenue_data.setText(f"{revenue_unknown:.2f}")
            self.net_profit_data.setText(f"{net_profit:.2f}")
            self.net_margin_data.setText(f"{net_margin_pct:.2f}%")
            self.coverage_data.setText(f"{coverage_pct:.2f}%")

            self.profit_data.setStyleSheet("color: #c62828;" if gross_profit < 0 else "color: #2e7d32;")
            self.net_profit_data.setStyleSheet("color: #c62828;" if net_profit < 0 else "color: #2e7d32;")






    def show_near_expiry_dialog(self):
        from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QLabel, QPushButton
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Near Expiry Batches (Next 60 Days)")
        dialog.setMinimumHeight(400)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        heading = QLabel("Near Expiry Batches (Next 60 Days)")
        heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        header_layout.addWidget(heading)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Product", "Batch No", "Expiry Date", "Days Left", "Qty Remaining"
        ])
        table.horizontalHeader().setStretchLastSection(True)
        content_layout.addWidget(table)

        try:
            rows = report_service.ReportService().get_near_expiry_rows(days=60)
        except Exception as exc:
            print(str(exc))
            footer_layout.addStretch()
            close_btn = QPushButton("Close")
            close_btn.setCursor(QCursor(Qt.PointingHandCursor))
            close_btn.setStyleSheet(self.report_action_btn_style())
            close_btn.setMinimumHeight(34)
            close_btn.clicked.connect(dialog.accept)
            footer_layout.addWidget(close_btn)
            dialog.exec()
            return

        table.setRowCount(len(rows))

        for row_index, row_data in enumerate(rows):
            values = [
                row_data["product_name"],
                row_data["batch_no"],
                row_data["expiry_date"],
                row_data["days_left"],
                row_data["qty_remaining"],
            ]
            for col_index, value in enumerate(values):
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

            # Highlight if expiry exists AND < 30 days
            # days_left = row_data[3]
            
            # if days_left is not None and days_left < 30:
            #     for col in range(table.columnCount()):
            #         table.item(row_index, col).setBackground(QColor("yellow"))

        table.resizeColumnsToContents()
        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)
        dialog.exec()






    def show_low_stock_dialog(self):
        from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QLabel, QPushButton
        from PySide6.QtCore import Qt

        dialog = QDialog(self)
        dialog.setWindowTitle("Low Stock Products")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(400)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        heading = QLabel("Low Stock Products")
        heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        header_layout.addWidget(heading)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([
            "Product", "Current Stock"
        ])
        table.horizontalHeader().setStretchLastSection(True)
        content_layout.addWidget(table)

        try:
            rows = report_service.ReportService().get_low_stock_rows()
        except Exception as exc:
            print(str(exc))
            footer_layout.addStretch()
            close_btn = QPushButton("Close")
            close_btn.setCursor(QCursor(Qt.PointingHandCursor))
            close_btn.setStyleSheet(self.report_action_btn_style())
            close_btn.setMinimumHeight(34)
            close_btn.clicked.connect(dialog.accept)
            footer_layout.addWidget(close_btn)
            dialog.exec()
            return

        table.setRowCount(len(rows))

        for row_index, row_data in enumerate(rows):
            values = [row_data["product_name"], row_data["total_stock"]]
            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        table.resizeColumnsToContents()
        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.setMinimumHeight(34)
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)
        dialog.exec()
    def report_card_style(self):
        return """
            QFrame {
                background-color: #E8EEF3;
                border: 1px solid #D3DDE6;
                border-radius: 8px;
                padding: 6px;
            }
            QLabel {
                color: #223746;
                font-weight: 600;
                font-size: 13px;
                padding-left: 0;
            }
        """

    def report_action_btn_style(self):
        return (
            "QPushButton { background: #325D7B; color: white; border-radius: 5px;"
            " border: 1px solid #284B63; padding: 4px 10px; font-weight: 600; }"
            "QPushButton:hover { background: #284B63; }"
        )

    def dialog_section_style(self, tone="content"):
        if tone in ("header", "footer"):
            return (
                "background-color: #DFE8EF; border: 1px solid #C7D4DE; border-radius: 3px;"
            )
        return (
            "background-color: #EEF4F8; border: 1px solid #D3DDE6; border-radius: 3px;"
        )

    def build_report_dialog_shell(self, dialog):
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        header_section = QWidget()
        header_section.setObjectName("dialogHeader")
        header_section.setStyleSheet(f"QWidget#dialogHeader {{ {self.dialog_section_style('header')} }}")
        header_layout = QVBoxLayout(header_section)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(12)

        content_section = QWidget()
        content_section.setObjectName("dialogContent")
        content_section.setStyleSheet(f"QWidget#dialogContent {{ {self.dialog_section_style('content')} }}")
        content_layout = QVBoxLayout(content_section)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(12)

        footer_section = QWidget()
        footer_section.setObjectName("dialogFooter")
        footer_section.setStyleSheet(f"QWidget#dialogFooter {{ {self.dialog_section_style('footer')} }}")
        footer_layout = QHBoxLayout(footer_section)
        footer_layout.setContentsMargins(10, 10, 10, 10)
        footer_layout.setSpacing(8)

        layout.addWidget(header_section)
        layout.addWidget(content_section, 1)
        layout.addWidget(footer_section)

        return header_layout, content_layout, footer_layout

    def summary_card_style(self):
        return """
            QWidget#card {
                background-color: #E8EEF3;
                border: 1px solid #D3DDE6;
                border-radius: 8px;
                color: #223746;
            }
        """

    def summary_card_title_style(self):
        return "font-size: 16px; font-weight: 700; color: #4B6273; padding-left: 0;"

    def summary_card_value_style(self):
        return "font-size: 24px; font-weight: 700; color: #223746; padding-left: 0;"

    def compact_metric_label_style(self):
        return "color: #5A7183; font-size: 12px; font-weight: 700; padding-left: 0;"

    def compact_metric_value_style(self):
        return "color: #223746; font-size: 16px; font-weight: 700; padding-left: 0;"

    def get_duration_label(self, duration_key):
        return {
            "today": "Today",
            "week": "Past Week",
            "month": "Past Month",
            "year": "Past Year",
            "all": "All",
        }.get((duration_key or "today").lower(), "Today")

    def build_report_period_combo(self, current_duration_key):
        combo = QComboBox()
        options = [
            ("Today", "today"),
            ("Past Week", "week"),
            ("Past Month", "month"),
            ("Past Year", "year"),
            ("All", "all"),
        ]
        for label, key in options:
            combo.addItem(label, key)
        current_key = (current_duration_key or "today").lower()
        index = combo.findData(current_key)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.setCursor(Qt.PointingHandCursor)
        combo.setFixedWidth(130)
        return combo

    def get_business_name(self):
        return report_service.ReportService().get_business_name()

    def build_report_text(self, title, meta_lines=None, sections=None):
        business_name = self.get_business_name()
        generated_at = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        lines = [
            business_name,
            title,
            f"Generated: {generated_at}",
        ]

        if meta_lines:
            lines.extend(str(line) for line in meta_lines if str(line).strip())

        lines.append("")

        for section in sections or []:
            section_title = str(section.get("title", "")).strip()
            if section_title:
                lines.append(section_title)
                lines.append("-" * len(section_title))

            for entry in section.get("lines", []):
                if isinstance(entry, tuple) and len(entry) == 2:
                    label, value = entry
                    lines.append(f"{str(label):<36} {value}")
                else:
                    lines.append(str(entry))
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def export_report_text(self, default_name, title, content_text):
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        if self.demo_mode:
            AppMessageBox.information(
                self,
                "Demo Restriction",
                "TXT export is disabled in demo mode. Install a full license to unlock report exports.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {title}",
            f"{default_name}.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content_text)
            AppMessageBox.information(self, "Export Complete", f"{title} was exported successfully.")
        except Exception as exc:
            AppMessageBox.critical(self, "Export Failed", f"Could not export report.\n\n{exc}")

    def export_report_pdf(self, default_name, title, content_text):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6.QtGui import QTextDocument, QPageSize
        from PySide6.QtPrintSupport import QPrinter

        if self.demo_mode:
            AppMessageBox.information(
                self,
                "Demo Restriction",
                "PDF export is disabled in demo mode. Install a full license to unlock report exports.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {title} as PDF",
            f"{default_name}.pdf",
            "PDF Files (*.pdf)",
        )
        if not path:
            return

        try:
            document = QTextDocument()
            document.setDefaultStyleSheet(
                "body { font-family: 'Courier New', monospace; font-size: 11pt; color: #223746; }"
                "pre { white-space: pre-wrap; }"
            )
            document.setHtml(f"<pre>{html.escape(content_text)}</pre>")

            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageSize(QPageSize(QPageSize.A4))
            document.print(printer)
            AppMessageBox.information(self, "Export Complete", f"{title} was exported successfully as PDF.")
        except Exception as exc:
            AppMessageBox.critical(self, "Export Failed", f"Could not export PDF.\n\n{exc}")

    def print_report_text(self, title, content_text):
        from PySide6.QtGui import QTextDocument
        from PySide6.QtPrintSupport import QPrinter, QPrintDialog

        if self.demo_mode:
            AppMessageBox.information(
                self,
                "Demo Restriction",
                "Printing is disabled in demo mode. Install a full license to unlock report printing.",
            )
            return

        document = QTextDocument()
        document.setDefaultStyleSheet(
            "body { font-family: 'Courier New', monospace; font-size: 11pt; color: #223746; }"
            "pre { white-space: pre-wrap; }"
        )
        document.setHtml(f"<pre>{html.escape(content_text)}</pre>")

        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle(f"Print {title}")
        if dialog.exec():
            document.print(printer)

    def stock_card_subtitle_style(self):
        return "color: #4B6273; font-size: 12px; font-weight: 700; letter-spacing: 0.3px; padding-left: 0;"

    def create_inventory_valuation_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QLabel("Valuation")
        title.setStyleSheet(self.stock_card_subtitle_style())
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)

        def add_metric(row, col, title_text, value_widget):
            title_label = QLabel(title_text)
            title_label.setStyleSheet(self.compact_metric_label_style())
            block = QVBoxLayout()
            block.setContentsMargins(0, 0, 0, 0)
            block.setSpacing(2)
            block.addWidget(title_label)
            block.addWidget(value_widget)
            grid.addLayout(block, row, col)

        self.estimate_cost = QLabel("0.00")
        self.estimate_cost.setStyleSheet(self.compact_metric_value_style())
        self.known_stock_cost_data = QLabel("0.00")
        self.known_stock_cost_data.setStyleSheet(self.compact_metric_value_style())

        add_metric(0, 0, "Estimated Opening Stock Cost", self.estimate_cost)
        add_metric(0, 1, "Known Stock Cost", self.known_stock_cost_data)

        layout.addLayout(grid)

        snapshot = report_service.ReportService().get_inventory_overview_snapshot()
        self.estimate_cost.setText(f"{float(snapshot.get('opening_estimate_amount', 0.0) or 0.0):,.2f}")
        self.known_stock_cost_data.setText(f"{float(snapshot.get('known_stock_cost_amount', 0.0) or 0.0):.2f}")

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 4, 0, 0)
        action_row.addStretch()

        review_opening_costs_btn = QPushButton("Review Opening Costs")
        review_opening_costs_btn.setCursor(QCursor(Qt.PointingHandCursor))
        review_opening_costs_btn.setStyleSheet(self.report_action_btn_style())
        review_opening_costs_btn.clicked.connect(self.show_opening_stock_cost_review_dialog)
        action_row.addWidget(review_opening_costs_btn)

        layout.addLayout(action_row)

        return card

    def create_inventory_alerts_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QLabel("Alerts & Operations")
        title.setStyleSheet(self.stock_card_subtitle_style())
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)

        def add_metric(row, col, title_text, value_widget):
            title_label = QLabel(title_text)
            title_label.setStyleSheet(self.compact_metric_label_style())
            block = QVBoxLayout()
            block.setContentsMargins(0, 0, 0, 0)
            block.setSpacing(2)
            block.addWidget(title_label)
            block.addWidget(value_widget)
            grid.addLayout(block, row, col)

        self.expiry_count = QPushButton("0.00")
        self.expiry_count.setStyleSheet(self.report_action_btn_style())
        self.expiry_count.clicked.connect(self.show_near_expiry_dialog)

        self.low_stock_count = QPushButton("0.00")
        self.low_stock_count.setStyleSheet(self.report_action_btn_style())
        self.low_stock_count.clicked.connect(self.show_low_stock_dialog)

        self.stock_movement_btn = QPushButton("Open")
        self.stock_movement_btn.setStyleSheet(self.report_action_btn_style())
        self.stock_movement_btn.clicked.connect(self.show_stock_movement_dialog)

        self.activity_log_btn = QPushButton("Open")
        self.activity_log_btn.setStyleSheet(self.report_action_btn_style())
        self.activity_log_btn.clicked.connect(self.show_activity_log_dialog)

        self.dead_nonmoving_btn = QPushButton("Open")
        self.dead_nonmoving_btn.setStyleSheet(self.report_action_btn_style())
        self.dead_nonmoving_btn.clicked.connect(self.show_dead_nonmoving_stock_dialog)

        add_metric(0, 0, "Near Expiry Count", self.expiry_count)
        add_metric(0, 1, "Low Stock Count", self.low_stock_count)
        add_metric(0, 2, "Dead / Non-moving", self.dead_nonmoving_btn)
        add_metric(1, 0, "Stock Movement", self.stock_movement_btn)
        add_metric(1, 1, "Activity Log", self.activity_log_btn)

        layout.addLayout(grid)

        snapshot = report_service.ReportService().get_inventory_overview_snapshot()
        count = snapshot.get("stock_alerts", {})
        self.expiry_count.setText(f"{float(count.get('near_expiry_batches', 0) or 0):.2f}")
        self.low_stock_count.setText(f"{float(count.get('low_stock_products', 0) or 0):.2f}")

        return card

    def get_opening_stock_cost_review_rows(self):
        try:
            return report_service.ReportService().get_opening_stock_cost_review_rows()
        except Exception as exc:
            AppMessageBox.critical(self, "Load Failed", str(exc))
            return []

    def show_opening_stock_cost_review_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Opening Stock Cost Review")
        dialog.resize(1080, 640)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        heading = QLabel("Opening Stock Cost Review")
        heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        subtitle = QLabel(
            "Fill in missing opening-stock batch costs here. Saving a cost will also backfill matching sold-batch cost history so profit and loss can be recalculated more completely."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12px; color: #5A7183; padding-left: 0;")
        header_layout.addWidget(heading)
        header_layout.addWidget(subtitle)

        summary_label = QLabel()
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("font-size: 11px; color: #5A7183; font-weight: 600; padding-left: 0;")
        header_layout.addWidget(summary_label)

        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels([
            "Batch ID", "Product", "Batch", "Expiry", "Added", "Remaining",
            "Sold", "Unknown Sold", "Unit Cost", "Status"
        ])
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnHidden(0, True)
        content_layout.addWidget(table)

        note_label = QLabel(
            "Tip: rows marked Missing affect profit coverage. You can update them later anytime; the related opening-stock sales history will be refreshed with the new cost."
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        content_layout.addWidget(note_label)

        def make_readonly_item(text, align=Qt.AlignLeft | Qt.AlignVCenter):
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(align)
            return item

        def refresh_table():
            rows = self.get_opening_stock_cost_review_rows()
            table.setRowCount(0)
            missing_count = 0
            impacted_qty = 0.0

            for row_data in rows:
                row = table.rowCount()
                table.insertRow(row)

                unit_cost = row_data["unit_cost"]
                is_missing = unit_cost is None
                if is_missing:
                    missing_count += 1
                    impacted_qty += float(row_data["unknown_sold_qty"] or 0.0)

                status_text = "Missing Cost" if is_missing else "Known Cost"
                if is_missing and float(row_data["unknown_sold_qty"] or 0.0) > 0:
                    status_text = "Missing - Profit Pending"

                table.setItem(row, 0, make_readonly_item(str(row_data["batch_id"])))
                table.setItem(row, 1, make_readonly_item(str(row_data["product_name"])))
                table.setItem(row, 2, make_readonly_item(str(row_data["batch_no"])))
                table.setItem(row, 3, make_readonly_item(str(row_data["expiry_date"])))
                table.setItem(row, 4, make_readonly_item(f"{float(row_data['added_qty']):,.2f}", Qt.AlignRight | Qt.AlignVCenter))
                table.setItem(row, 5, make_readonly_item(f"{float(row_data['remaining_qty']):,.2f}", Qt.AlignRight | Qt.AlignVCenter))
                table.setItem(row, 6, make_readonly_item(f"{float(row_data['sold_qty']):,.2f}", Qt.AlignRight | Qt.AlignVCenter))
                table.setItem(row, 7, make_readonly_item(f"{float(row_data['unknown_sold_qty']):,.2f}", Qt.AlignRight | Qt.AlignVCenter))

                cost_edit = QLineEdit()
                cost_edit.setPlaceholderText("Enter unit cost")
                cost_edit.setText("" if unit_cost is None else f"{float(unit_cost):.6f}".rstrip("0").rstrip("."))
                cost_edit.setProperty("batch_id", row_data["batch_id"])
                cost_edit.setProperty("previous_cost", unit_cost)
                if is_missing:
                    cost_edit.setStyleSheet("QLineEdit { background-color: #FFF7E6; border: 1px solid #E0B04B; }")
                table.setCellWidget(row, 8, cost_edit)

                status_item = make_readonly_item(status_text)
                if is_missing:
                    status_item.setForeground(QColor("#B45309"))
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item is not None:
                            item.setBackground(QColor("#FFF9EE"))
                else:
                    status_item.setForeground(QColor("#2E7D32"))
                table.setItem(row, 9, status_item)

            table.resizeColumnsToContents()
            summary_label.setText(
                f"Opening batches: {len(rows)} | Missing cost: {missing_count} | Sold quantity still excluded from known profit: {impacted_qty:,.2f}"
            )

        def save_cost_updates():
            updates = []
            validation_errors = []

            for row in range(table.rowCount()):
                cost_widget = table.cellWidget(row, 8)
                if cost_widget is None:
                    continue

                batch_id = int(cost_widget.property("batch_id") or 0)
                previous_cost = cost_widget.property("previous_cost")
                raw_text = cost_widget.text().strip()

                if not raw_text:
                    continue

                try:
                    new_cost = float(raw_text)
                except ValueError:
                    validation_errors.append(f"Batch #{batch_id}: cost must be a valid number.")
                    continue

                if new_cost < 0:
                    validation_errors.append(f"Batch #{batch_id}: cost cannot be negative.")
                    continue

                old_cost = float(previous_cost) if previous_cost is not None else None
                if old_cost is not None and abs(old_cost - new_cost) < 0.000001:
                    continue

                updates.append((batch_id, new_cost))

            if validation_errors:
                AppMessageBox.warning(dialog, "Validation Error", "\n".join(validation_errors[:5]))
                return

            if not updates:
                AppMessageBox.information(dialog, "No Changes", "Enter or change at least one opening batch cost to save.")
                return

            try:
                result = report_service.ReportService().save_opening_stock_cost_updates(updates)
                refresh_table()
                AppMessageBox.success(
                    dialog,
                    "Saved",
                    f"Updated {result['updated_batches']} opening batch cost(s) and refreshed {result['updated_sold_rows']} sold-batch allocation row(s).",
                )
            except Exception as exc:
                AppMessageBox.critical(dialog, "Save Failed", f"Could not save opening stock costs: {exc}")

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
        refresh_btn.setStyleSheet(self.report_action_btn_style())
        refresh_btn.clicked.connect(refresh_table)

        save_btn = QPushButton("Save Costs")
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.setStyleSheet(self.report_action_btn_style())
        save_btn.clicked.connect(save_cost_updates)

        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.report_action_btn_style())
        close_btn.clicked.connect(dialog.accept)

        footer_layout.addWidget(refresh_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(save_btn)
        footer_layout.addWidget(close_btn)

        refresh_table()
        dialog.exec()

    def create_dues_summary_card(self):
        card = QFrame()
        card.setStyleSheet(self.report_card_style())

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        body = QGridLayout()
        body.setHorizontalSpacing(18)
        body.setVerticalSpacing(8)
        body.setColumnStretch(0, 1)
        body.setColumnStretch(1, 1)

        def add_due_block(row, col, section_title, pay_value, receive_value, btn1, btn2):
            section = QVBoxLayout()
            section.setContentsMargins(0, 0, 0, 0)
            section.setSpacing(6)

            section_heading = QLabel(section_title)
            section_heading.setStyleSheet(self.stock_card_subtitle_style())
            section.addWidget(section_heading)

            metrics = QGridLayout()
            metrics.setHorizontalSpacing(12)
            metrics.setVerticalSpacing(6)

            pay_label = QLabel("Pay")
            pay_label.setStyleSheet(self.compact_metric_label_style())
            pay_data = QLabel(pay_value)
            pay_data.setStyleSheet(self.compact_metric_value_style())

            receive_label = QLabel("Receive")
            receive_label.setStyleSheet(self.compact_metric_label_style())
            receive_data = QLabel(receive_value)
            receive_data.setStyleSheet(self.compact_metric_value_style())

            metrics.addWidget(pay_label, 0, 0)
            metrics.addWidget(pay_data, 0, 1)
            metrics.addWidget(receive_label, 0, 2)
            metrics.addWidget(receive_data, 0, 3)
            section.addLayout(metrics)

            actions = QHBoxLayout()
            actions.setSpacing(8)
            actions.addWidget(btn1)
            actions.addWidget(btn2)
            actions.addStretch()
            section.addLayout(actions)

            body.addLayout(section, row, col)

        payable, receiveable = report_service.ReportService().get_supplier_balances()
        supplier_aging_btn = QPushButton("Payable Aging")
        supplier_aging_btn.setCursor(QCursor(Qt.PointingHandCursor))
        supplier_aging_btn.setStyleSheet(self.report_action_btn_style())
        supplier_aging_btn.clicked.connect(self.show_supplier_payable_aging_dialog)

        supplier_forecast_btn = QPushButton("Payment Schedule")
        supplier_forecast_btn.setCursor(QCursor(Qt.PointingHandCursor))
        supplier_forecast_btn.setStyleSheet(self.report_action_btn_style())
        supplier_forecast_btn.clicked.connect(self.show_supplier_payable_forecast_dialog)

        receivable, payable_customer = report_service.ReportService().get_customer_balances()
        customer_aging_btn = QPushButton("Aging Report")
        customer_aging_btn.setCursor(QCursor(Qt.PointingHandCursor))
        customer_aging_btn.setStyleSheet(self.report_action_btn_style())
        customer_aging_btn.clicked.connect(self.show_receivable_aging_dialog)

        customer_forecast_btn = QPushButton("Payment Forecast")
        customer_forecast_btn.setCursor(QCursor(Qt.PointingHandCursor))
        customer_forecast_btn.setStyleSheet(self.report_action_btn_style())
        customer_forecast_btn.clicked.connect(self.show_receivable_forecast_dialog)

        add_due_block(0, 0, "Supplier Dues", f"{payable:,.2f}", f"{receiveable:,.2f}", supplier_aging_btn, supplier_forecast_btn)
        add_due_block(0, 1, "Customer Dues", f"{payable_customer:,.2f}", f"{receivable:,.2f}", customer_aging_btn, customer_forecast_btn)

        layout.addLayout(body)
        return card
