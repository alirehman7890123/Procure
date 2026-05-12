from datetime import datetime
import csv
import sys
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from medic.services.financial_closing_service import (
    close_financial_period,
    collect_preclose_checks,
    get_month_close_prompt_state,
    get_quarter_label_from_month,
    get_quarter_summary_for_month,
    is_quarter_end_month,
    list_available_periods,
    list_financial_close_audit_events,
    list_recent_period_closures,
    reopen_financial_period,
)
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.permissions import Permissions
from medic.utilities.stylus import load_stylesheets


def _auto_confirm_for_tests():
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


class FinancialClosingPage(QWidget):
    show_closing_list = Signal()
    show_quarter_summary = Signal(str)

    def __init__(self, pro_enabled=True, parent=None):
        super().__init__(parent)
        self.pro_enabled = bool(pro_enabled)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignTop)
        self._review_acknowledgements = {}

        header_layout = QHBoxLayout()
        heading = QLabel("Monthly Closing", objectName="SectionTitle")
        header_layout.addWidget(heading)
        header_layout.addStretch()
        self.history_btn = QPushButton("View Closing History")
        self.history_btn.setObjectName("TopRightButton")
        self.history_btn.setCursor(Qt.PointingHandCursor)
        self.history_btn.clicked.connect(self.show_closing_list.emit)
        header_layout.addWidget(self.history_btn)
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

        self.month_close_banner = QFrame()
        self.month_close_banner.setStyleSheet(
            """
            QFrame {
                background-color: #FFF6E8;
                border: 1px solid #E5C16F;
                border-radius: 10px;
            }
            """
        )
        banner_layout = QHBoxLayout(self.month_close_banner)
        banner_layout.setContentsMargins(12, 10, 12, 10)
        self.month_close_banner_text = QLabel("")
        self.month_close_banner_text.setWordWrap(True)
        self.month_close_banner_btn = QPushButton("Open Current Month")
        self.month_close_banner_btn.setObjectName("TopRightButton")
        self.month_close_banner_btn.setCursor(Qt.PointingHandCursor)
        self.month_close_banner_btn.clicked.connect(self.open_current_month_period)
        banner_layout.addWidget(self.month_close_banner_text, 1)
        banner_layout.addWidget(self.month_close_banner_btn, 0)
        self.layout.addWidget(self.month_close_banner)
        self.month_close_banner.hide()

        control_wrap = QFrame()
        control_layout = QVBoxLayout(control_wrap)
        control_layout.setContentsMargins(12, 12, 12, 12)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Month"))
        self.period_selector = QComboBox()
        self.period_selector.currentIndexChanged.connect(self._refresh_period_label)
        row1.addWidget(self.period_selector)
        row1.addWidget(QLabel("Selected"))
        self.period_label = QLabel("")
        row1.addWidget(self.period_label)
        row1.addStretch()
        control_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Notes"))
        self.notes_input = QLineEdit()
        row2.addWidget(self.notes_input, 1)
        control_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.reload_btn = QPushButton("Reload")
        self.reload_btn.setObjectName("TopRightButton")
        self.reload_btn.clicked.connect(self.refresh_all_data)
        self.close_btn = QPushButton("Close Month")
        self.close_btn.setObjectName("SaveButton")
        self.close_btn.clicked.connect(self.close_selected_period)
        row3.addWidget(self.reload_btn)
        row3.addWidget(self.close_btn)
        row3.addStretch()
        control_layout.addLayout(row3)

        self.layout.addWidget(control_wrap)

        self.checks_table = QTableWidget(0, 5)
        self.checks_table.setHorizontalHeaderLabels(["Check", "Severity", "Issues", "Action", "Status"])
        self.checks_table.verticalHeader().setVisible(False)
        self.checks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.checks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.checks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.checks_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.checks_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.checks_table.cellDoubleClicked.connect(self._open_check_resolution_from_row)
        self.layout.addWidget(self.checks_table)

        history_wrap = QFrame()
        history_layout = QVBoxLayout(history_wrap)
        history_layout.setContentsMargins(0, 6, 0, 0)
        history_layout.setSpacing(8)

        self.closures_table = QTableWidget(0, 9)
        self.closures_table.setHorizontalHeaderLabels(
            ["Type", "Label", "Range", "Status", "Closed At", "Closed By", "Reopened At", "Reopened By", "Reopen Reason"]
        )
        self.closures_table.verticalHeader().setVisible(False)
        self.closures_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.closures_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.closures_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.closures_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.closures_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.closures_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.closures_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.closures_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.closures_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        self.closures_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.closures_table.itemSelectionChanged.connect(self.refresh_audit_timeline)
        history_layout.addWidget(self.closures_table)

        history_actions = QHBoxLayout()
        self.reopen_btn = QPushButton("Reopen Selected")
        self.reopen_btn.setObjectName("TopRightButton")
        self.reopen_btn.clicked.connect(self.reopen_selected_period)
        history_actions.addWidget(self.reopen_btn)
        self.quarter_summary_btn = QPushButton("View Quarter Summary")
        self.quarter_summary_btn.setObjectName("TopRightButton")
        self.quarter_summary_btn.clicked.connect(self.open_selected_quarter_summary)
        history_actions.addWidget(self.quarter_summary_btn)
        history_actions.addStretch()
        history_layout.addLayout(history_actions)

        audit_controls = QHBoxLayout()
        audit_controls.addWidget(QLabel("Audit Trail"))
        self.audit_event_filter = QComboBox()
        self.audit_event_filter.addItem("All", "")
        self.audit_event_filter.addItem("Closed", "closed")
        self.audit_event_filter.addItem("Reopened", "reopened")
        self.audit_event_filter.currentIndexChanged.connect(self.refresh_audit_timeline)
        audit_controls.addWidget(self.audit_event_filter)
        self.audit_export_btn = QPushButton("Export CSV")
        self.audit_export_btn.setObjectName("TopRightButton")
        self.audit_export_btn.clicked.connect(self.export_audit_events_csv)
        audit_controls.addWidget(self.audit_export_btn)
        audit_controls.addStretch()
        history_layout.addLayout(audit_controls)

        self.audit_summary_label = QLabel("No audit events loaded.")
        self.audit_summary_label.setStyleSheet("color: gray; font-size: 11px;")
        history_layout.addWidget(self.audit_summary_label)

        self.audit_table = QTableWidget(0, 6)
        self.audit_table.setHorizontalHeaderLabels(["Event", "At", "By", "Reason Code", "Reason", "Period"])
        self.audit_table.verticalHeader().setVisible(False)
        self.audit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.audit_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        history_layout.addWidget(self.audit_table)

        self.layout.addWidget(history_wrap)

        self.setStyleSheet(load_stylesheets())
        self.refresh_all_data()

        if not self.pro_enabled or not Permissions.has_permission("financialclose.close"):
            self.close_btn.setEnabled(False)
        if not self.pro_enabled or not Permissions.has_permission("financialclose.reopen"):
            self.reopen_btn.setEnabled(False)

    def _selected_period_payload(self):
        period = self.period_selector.currentData()
        return period if isinstance(period, dict) else None

    def _load_available_periods(self):
        current_label = ""
        current_data = self.period_selector.currentData() if self.period_selector.count() else None
        if isinstance(current_data, dict):
            current_label = str(current_data.get("period_label") or "")

        periods = list_available_periods("monthly")
        self.period_selector.blockSignals(True)
        self.period_selector.clear()

        selected_index = 0
        for index, period in enumerate(periods):
            text = f"{period['display_label']} ({self._format_date(period['period_start'])} to {self._format_date(period['period_end'])})"
            self.period_selector.addItem(text, period)
            if current_label and current_label == period.get("period_label"):
                selected_index = index

        if periods:
            self.period_selector.setCurrentIndex(selected_index)
        else:
            self.period_selector.addItem("No open periods available", None)

        self.period_selector.blockSignals(False)
        self._refresh_period_label()

    def _refresh_period_label(self):
        period = self._selected_period_payload()
        if not period:
            self.period_label.setText("No eligible period")
            self.checks_table.setRowCount(0)
            return
        self.period_label.setText(
            f"{period['display_label']} ({self._format_date(period['period_start'])} to {self._format_date(period['period_end'])})"
        )
        self.run_preclose_checks()

    def _update_month_end_banner(self):
        state = get_month_close_prompt_state()
        if not state.get("show"):
            self.month_close_banner.hide()
            return
        self.month_close_banner_text.setText(str(state.get("message") or ""))
        self.month_close_banner.show()

    def open_current_month_period(self):
        self._load_available_periods()
        state = get_month_close_prompt_state()
        target = str(state.get("period_label") or "")
        for index in range(self.period_selector.count()):
            payload = self.period_selector.itemData(index)
            if isinstance(payload, dict) and payload.get("period_label") == target:
                self.period_selector.setCurrentIndex(index)
                self.run_preclose_checks()
                return
        if self.period_selector.count() > 0:
            self.period_selector.setCurrentIndex(0)
        self.run_preclose_checks()

    def reset_to_default(self):
        self.notes_input.clear()
        self.open_current_month_period()
        self._update_month_end_banner()

    def refresh_all_data(self):
        self._load_available_periods()
        self._update_month_end_banner()
        self.run_preclose_checks()
        self.refresh_closure_table()
        self.refresh_audit_timeline()

    def _open_check_resolution(self, check):
        if not isinstance(check, dict):
            AppMessageBox.warning(self, "Navigation Unavailable", "Selected check does not have navigation details.")
            return

        route = str(check.get("route") or "").strip()
        main_window = self.window()
        if main_window is None:
            AppMessageBox.warning(self, "Navigation Unavailable", "Could not open the related page.")
            return

        if route == "daily_session_history" and hasattr(main_window, "set_dashboard"):
            main_window.set_dashboard(None, main_window.main_content_layout)
            if hasattr(main_window, "dashboard") and hasattr(main_window.dashboard, "set_daily_session_widget"):
                main_window.dashboard.set_daily_session_widget()
                return
        if route == "product_list" and hasattr(main_window, "set_product"):
            main_window.set_product(None, main_window.main_content_layout)
            if hasattr(main_window, "product") and hasattr(main_window.product, "set_productlist_widget"):
                main_window.product.set_productlist_widget()
                return
        if route == "grn_list" and hasattr(main_window, "set_grn"):
            main_window.set_grn(None, main_window.main_content_layout)
            if hasattr(main_window, "grn") and hasattr(main_window.grn, "set_grn_list_widget"):
                main_window.grn.set_grn_list_widget()
                return
        if route == "supplier_transactions" and hasattr(main_window, "set_transaction"):
            main_window.set_transaction(None, main_window.main_content_layout)
            if hasattr(main_window, "transaction") and hasattr(main_window.transaction, "set_suppliertransaction_widget"):
                main_window.transaction.set_suppliertransaction_widget()
                return
        if route == "customer_transactions" and hasattr(main_window, "set_transaction"):
            main_window.set_transaction(None, main_window.main_content_layout)
            if hasattr(main_window, "transaction") and hasattr(main_window.transaction, "set_customertransaction_widget"):
                main_window.transaction.set_customertransaction_widget()
                return

        AppMessageBox.warning(self, "Navigation Unavailable", "No resolution page is mapped for this check.")

    def _open_check_resolution_from_row(self, row, _column):
        if row < 0:
            return

        item = self.checks_table.item(row, 0)
        payload = item.data(Qt.UserRole) if item is not None else None
        if isinstance(payload, dict) and int(payload.get("count") or 0) > 0:
            self._open_check_resolution(payload)

    def run_preclose_checks(self):
        period = self._selected_period_payload()
        self.checks_table.setRowCount(0)
        self._review_acknowledgements = {}
        if not period:
            self.close_btn.setEnabled(False)
            return

        if self.pro_enabled and Permissions.has_permission("financialclose.close"):
            self.close_btn.setEnabled(True)

        checks = collect_preclose_checks(period["period_start"], period["period_end"])
        for row, check in enumerate(checks):
            self.checks_table.insertRow(row)
            count = int(check.get("count") or 0)
            severity = str(check.get("severity") or "blocking").strip().lower()
            name_item = QTableWidgetItem(str(check.get("name") or ""))
            name_item.setData(Qt.UserRole, check)
            self.checks_table.setItem(row, 0, name_item)
            self.checks_table.setItem(row, 1, QTableWidgetItem("Blocking" if severity == "blocking" else "Review"))
            self.checks_table.setItem(row, 2, QTableWidgetItem(str(count)))
            self.checks_table.setItem(row, 3, QTableWidgetItem(str(check.get("action") or "")))
            self.checks_table.setCellWidget(row, 4, self._build_check_status_widget(check))

    def close_selected_period(self):
        if not self.pro_enabled:
            AppMessageBox.warning(self, "Pro Feature", "Financial period closing is available in Pro version.")
            return
        if not Permissions.has_permission("financialclose.close"):
            AppMessageBox.critical(self, "Not Authorized", "You do not have permission to close financial periods.")
            return

        period = self._selected_period_payload()
        if not period:
            AppMessageBox.warning(self, "No Period", "There is no eligible period available to close.")
            return

        checks = collect_preclose_checks(period["period_start"], period["period_end"])
        blocking_checks = self._blocking_checks(checks)
        review_checks = self._review_checks(checks)
        if blocking_checks:
            AppMessageBox.warning(self, "Cannot Close Period", self._build_blocking_checks_message(checks))
            self.run_preclose_checks()
            return
        unreviewed_checks = self._unreviewed_checks(review_checks)
        if unreviewed_checks:
            AppMessageBox.warning(self, "Review Required", self._build_review_required_message(unreviewed_checks))
            return

        summary = self._build_preclose_confirmation_text(period, result_snapshot=None, review_checks=review_checks)
        answer = AppMessageBox.Yes if _auto_confirm_for_tests() else AppMessageBox.question(self, "Confirm Monthly Close", summary)
        if answer != AppMessageBox.Yes:
            return

        try:
            result = close_financial_period(
                period_type=period["period_type"],
                period_label=period["period_label"],
                period_start=period["period_start"],
                period_end=period["period_end"],
                closed_by=str(QApplication.instance().property("username") or ""),
                notes=self.notes_input.text().strip(),
            )
        except Exception as exc:
            AppMessageBox.critical(self, "Close Failed", str(exc))
            return

        AppMessageBox.information(self, "Period Closed", self._build_close_success_message(result))
        quarter_label = str(result.get("quarter_label") or get_quarter_label_from_month(period["period_label"]) or "")
        if quarter_label and is_quarter_end_month(period["period_label"]):
            quarter_summary = get_quarter_summary_for_month(period["period_label"])
            if quarter_summary:
                self.show_quarter_summary.emit(get_quarter_label_from_month(period["period_label"]))
                return
        self.show_closing_list.emit()

    def _blocking_checks(self, checks):
        return [check for check in checks if str(check.get("severity") or "").strip().lower() == "blocking" and int(check.get("count") or 0) > 0]

    def _review_checks(self, checks):
        return [check for check in checks if str(check.get("severity") or "").strip().lower() == "review" and int(check.get("count") or 0) > 0]

    def _unreviewed_checks(self, review_checks):
        return [check for check in review_checks if not self._review_acknowledgements.get(str(check.get("code") or ""))]

    def _build_check_status_widget(self, check):
        count = int(check.get("count") or 0)
        severity = str(check.get("severity") or "blocking").strip().lower()
        code = str(check.get("code") or "")

        if count <= 0:
            button = QPushButton("Resolved")
            button.setEnabled(False)
            return button

        if severity == "review":
            checkbox = QCheckBox("Reviewed")
            checkbox.setChecked(bool(self._review_acknowledgements.get(code)))
            checkbox.toggled.connect(lambda checked, review_code=code: self._set_review_acknowledged(review_code, checked))
            return checkbox
        else:
            button = QPushButton("Resolve")
            button.setObjectName("TopRightButton")
            button.clicked.connect(lambda _checked=False, payload=check: self._open_check_resolution(payload))
            return button

    def _set_review_acknowledged(self, code, checked):
        self._review_acknowledgements[str(code or "")] = bool(checked)

    def _build_blocking_checks_message(self, checks):
        lines = ["The month cannot be closed because these blocking checks still have open issues:"]
        for check in checks:
            if int(check.get("count") or 0) > 0:
                lines.append(f"- {check.get('name')}: {int(check.get('count') or 0)}")
        return "\n".join(lines)

    def _build_review_required_message(self, checks):
        lines = ["Please mark these review items as reviewed before closing the month:"]
        for check in checks:
            lines.append(f"- {check.get('name')}: {int(check.get('count') or 0)}")
        return "\n".join(lines)

    def _build_preclose_confirmation_text(self, period, result_snapshot=None, review_checks=None):
        start_label = self._format_date(period.get("period_start"))
        end_label = self._format_date(period.get("period_end"))
        lines = [
            f"Period: {period.get('display_label') or period.get('period_label')}",
            f"Range: {start_label} to {end_label}",
        ]
        if review_checks:
            review_count = sum(int(check.get("count") or 0) for check in review_checks)
            if review_count:
                lines.append(f"Reviewed items acknowledged: {review_count}")
        if result_snapshot:
            lines.append("")
            lines.append(f"Snapshot rows saved: {int(result_snapshot.get('snapshot_rows') or 0)}")
        return "\n".join(lines)

    def _build_close_success_message(self, result):
        snapshot = result.get("snapshot") if isinstance(result.get("snapshot"), dict) else {}
        closed_at = str(result.get("closed_at") or snapshot.get("closed_at") or "")
        label = str(result.get("period_label") or "")
        snapshot_rows = int(result.get("snapshot_rows") or snapshot.get("review_item_count") or 0)
        return f"{label} closed successfully.\nClosed At: {closed_at}\nSnapshot Rows: {snapshot_rows}"

    def _selected_closure_payload(self):
        row = self.closures_table.currentRow()
        if row >= 0:
            item = self.closures_table.item(row, 0)
            payload = item.data(Qt.UserRole) if item is not None else None
            if isinstance(payload, dict):
                return payload
        period = self._selected_period_payload()
        if not isinstance(period, dict):
            return None
        return {
            "period_type": period.get("period_type"),
            "period_label": period.get("period_label"),
            "period_start": period.get("period_start"),
            "period_end": period.get("period_end"),
            "status": "",
            "closed_at": "",
            "closed_by": "",
            "reopened_at": "",
            "reopened_by": "",
            "reopen_reason": "",
            "quarter_label": get_quarter_label_from_month(period.get("period_label")),
            "snapshot": {},
        }

    def refresh_closure_table(self):
        try:
            rows = list_recent_period_closures(limit=50)
        except Exception:
            rows = []
        self.closures_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.closures_table.insertRow(row_index)
            quarter_label = str(row.get("quarter_label") or get_quarter_label_from_month(row.get("period_label")) or "")
            row_with_quarter = dict(row)
            row_with_quarter["quarter_label"] = quarter_label
            item = QTableWidgetItem(str(row.get("period_type") or "").title())
            item.setData(Qt.UserRole, row_with_quarter)
            self.closures_table.setItem(row_index, 0, item)
            self.closures_table.setItem(row_index, 1, QTableWidgetItem(str(row.get("period_label") or "")))
            self.closures_table.setItem(row_index, 2, QTableWidgetItem(f"{row.get('period_start') or ''} to {row.get('period_end') or ''}"))
            self.closures_table.setItem(row_index, 3, QTableWidgetItem(str(row.get("status") or "")))
            self.closures_table.setItem(row_index, 4, QTableWidgetItem(str(row.get("closed_at") or "")))
            self.closures_table.setItem(row_index, 5, QTableWidgetItem(str(row.get("closed_by") or "")))
            self.closures_table.setItem(row_index, 6, QTableWidgetItem(str(row.get("reopened_at") or "")))
            self.closures_table.setItem(row_index, 7, QTableWidgetItem(str(row.get("reopened_by") or "")))
            self.closures_table.setItem(row_index, 8, QTableWidgetItem(str(row.get("reopen_reason") or "")))
        if rows:
            self.closures_table.selectRow(0)
        self.quarter_summary_btn.setEnabled(bool(self._selected_closure_payload()))

    def _selected_audit_events(self):
        closure = self._selected_closure_payload()
        period_type = closure.get("period_type") if isinstance(closure, dict) else None
        period_label = closure.get("period_label") if isinstance(closure, dict) else None
        try:
            events = list_financial_close_audit_events(period_type=period_type, period_label=period_label, limit=100)
        except Exception:
            events = []
        event_filter = str(self.audit_event_filter.currentData() or "").strip().lower()
        if event_filter:
            events = [event for event in events if str(event.get("event_type") or "").strip().lower() == event_filter]
        return events

    def refresh_audit_timeline(self):
        self.audit_table.setRowCount(0)
        events = self._selected_audit_events()
        count = len(events)
        noun = "event" if count == 1 else "events"
        filter_text = self.audit_event_filter.currentText()
        self.audit_summary_label.setText(f"Showing {count} {noun} · Filter: {filter_text}")
        for row_index, event in enumerate(events):
            self.audit_table.insertRow(row_index)
            self.audit_table.setItem(row_index, 0, QTableWidgetItem(str(event.get("event_type") or "").title()))
            self.audit_table.setItem(row_index, 1, QTableWidgetItem(str(event.get("event_at") or "")))
            self.audit_table.setItem(row_index, 2, QTableWidgetItem(str(event.get("event_by") or "")))
            self.audit_table.setItem(row_index, 3, QTableWidgetItem(str(event.get("reason_code") or "")))
            self.audit_table.setItem(row_index, 4, QTableWidgetItem(str(event.get("reason_text") or "")))
            self.audit_table.setItem(
                row_index,
                5,
                QTableWidgetItem(f"{str(event.get('period_type') or '').title()} {str(event.get('period_label') or '')}".strip()),
            )

    def export_audit_events_csv(self):
        events = self._selected_audit_events()
        if not events:
            AppMessageBox.warning(self, "No Data", "There are no audit events to export for the selected filter.")
            return
        closure = self._selected_closure_payload()
        period_label = str(closure.get("period_label") or "all") if isinstance(closure, dict) else "all"
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Audit Events", f"financial_close_audit_{period_label}.csv", "CSV Files (*.csv)")
        if not file_path:
            return
        with open(file_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["event", "event_at", "event_by", "reason_code", "reason_text", "period_type", "period_label"])
            for event in events:
                writer.writerow([
                    str(event.get("event_type") or ""),
                    str(event.get("event_at") or ""),
                    str(event.get("event_by") or ""),
                    str(event.get("reason_code") or ""),
                    str(event.get("reason_text") or ""),
                    str(event.get("period_type") or ""),
                    str(event.get("period_label") or ""),
                ])
        noun = "record" if len(events) == 1 else "records"
        AppMessageBox.information(self, "Export Complete", f"Exported {len(events)} audit {noun} to:\n{file_path}")

    def open_selected_quarter_summary(self):
        closure = self._selected_closure_payload()
        if not isinstance(closure, dict):
            return
        quarter_summary = get_quarter_summary_for_month(str(closure.get("period_label") or ""))
        if not quarter_summary:
            AppMessageBox.warning(self, "Quarter Summary", "Quarter summary is not available for the selected row.")
            return
        quarter_label = str(quarter_summary.get("quarter_label") or get_quarter_label_from_month(closure.get("period_label")) or "")
        if quarter_label:
            self.show_quarter_summary.emit(quarter_label)

    def reopen_selected_period(self):
        if not self.pro_enabled:
            AppMessageBox.warning(self, "Pro Feature", "Reopening financial periods is available in Pro version.")
            return
        if not Permissions.has_permission("financialclose.reopen"):
            AppMessageBox.critical(self, "Not Authorized", "You do not have permission to reopen financial periods.")
            return
        closure = self._selected_closure_payload()
        if not isinstance(closure, dict):
            AppMessageBox.warning(self, "No Selection", "Choose a closed period first.")
            return
        notes = self.notes_input.text().strip()
        if len(notes) < 10:
            AppMessageBox.warning(self, "Reason Too Short", "Please provide a more detailed reopen reason.")
            return
        answer = (
            AppMessageBox.Yes
            if _auto_confirm_for_tests()
            else AppMessageBox.question(
                self,
                "Confirm Reopen",
                f"Reopen {closure.get('period_label') or 'selected period'}?\n\nThis should only be used for corrective action.",
            )
        )
        if answer != AppMessageBox.Yes:
            return
        result = reopen_financial_period(
            period_type=closure.get("period_type"),
            period_label=closure.get("period_label"),
            reopened_by=str(QApplication.instance().property("username") or ""),
            reason=notes,
        )
        if not result.get("ok"):
            AppMessageBox.critical(self, "Reopen Failed", str(result.get("reason") or "Unknown error"))
            return
        AppMessageBox.information(self, "Reopened", "Financial period reopened successfully.")
        self.notes_input.clear()
        self.refresh_all_data()

    def _format_date(self, value):
        text = str(value or "").strip()
        if not text:
            return "-"
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).strftime("%b %d, %Y")
            except ValueError:
                continue
        return text


sys.modules.setdefault("features.finance.ui.financial_close_page", sys.modules[__name__])
