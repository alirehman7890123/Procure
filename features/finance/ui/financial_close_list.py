import csv
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from medic.services.financial_closing_service import (
    get_quarter_summary_for_month,
    list_financial_close_audit_events,
    list_recent_period_closures,
    reopen_financial_period,
)
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.permissions import Permissions
from medic.utilities.stylus import load_stylesheets


class FinancialClosingListPage(QWidget):
    show_close_workflow = Signal()
    show_quarter_summary = Signal(str)

    def __init__(self, pro_enabled=True, parent=None):
        super().__init__(parent)
        self.pro_enabled = bool(pro_enabled)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignTop)

        header_layout = QHBoxLayout()
        heading = QLabel("Financial Closing History", objectName="SectionTitle")
        header_layout.addWidget(heading)
        header_layout.addStretch()
        self.close_current_period_btn = QPushButton("Close Current Period")
        self.close_current_period_btn.setObjectName("TopRightButton")
        self.close_current_period_btn.setCursor(Qt.PointingHandCursor)
        self.close_current_period_btn.clicked.connect(self.show_close_workflow.emit)
        header_layout.addWidget(self.close_current_period_btn)
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

        note = QLabel(
            "Browse closed and reopened financial periods here. Select a row to inspect the saved snapshot and audit trail."
        )
        note.setWordWrap(True)
        self.layout.addWidget(note)

        top_actions_wrap = QFrame()
        top_actions_layout = QHBoxLayout(top_actions_wrap)
        top_actions_layout.setContentsMargins(12, 12, 12, 12)
        top_actions_layout.setSpacing(8)

        self.details_btn = QPushButton("View Month Details")
        self.details_btn.setObjectName("TopRightButton")
        self.details_btn.clicked.connect(self.open_selected_details_dialog)
        self.details_btn.setEnabled(False)
        top_actions_layout.addWidget(self.details_btn)

        self.quarter_summary_btn = QPushButton("View Quarter Summary")
        self.quarter_summary_btn.setObjectName("TopRightButton")
        self.quarter_summary_btn.clicked.connect(self.open_selected_quarter_summary)
        self.quarter_summary_btn.setEnabled(False)
        top_actions_layout.addWidget(self.quarter_summary_btn)

        self.reload_btn = QPushButton("Reload History")
        self.reload_btn.setObjectName("TopRightButton")
        self.reload_btn.clicked.connect(self.refresh_all_data)
        top_actions_layout.addWidget(self.reload_btn)
        top_actions_layout.addStretch()
        self.layout.addWidget(top_actions_wrap)

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
        self.closures_table.itemSelectionChanged.connect(self._update_closure_actions)
        self.layout.addWidget(self.closures_table)

        reopen_wrap = QFrame()
        reopen_layout = QVBoxLayout(reopen_wrap)
        reopen_layout.setContentsMargins(12, 12, 12, 12)
        reopen_layout.setSpacing(8)

        reopen_notes_row = QHBoxLayout()
        reopen_notes_row.addWidget(QLabel("Reopen Notes"))
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Explain why this period needs to be reopened")
        reopen_notes_row.addWidget(self.notes_input, 1)
        reopen_layout.addLayout(reopen_notes_row)

        reopen_actions_row = QHBoxLayout()
        self.reopen_btn = QPushButton("Reopen Selected")
        self.reopen_btn.setObjectName("TopRightButton")
        self.reopen_btn.clicked.connect(self.reopen_selected_period)
        reopen_actions_row.addWidget(self.reopen_btn)
        reopen_actions_row.addStretch()
        reopen_layout.addLayout(reopen_actions_row)
        self.layout.addWidget(reopen_wrap)

        audit_controls = QHBoxLayout()
        audit_controls.addWidget(QLabel("Audit Trail"))
        self.audit_event_filter = QComboBox()
        self.audit_event_filter.addItem("All", "")
        self.audit_event_filter.addItem("Closed", "closed")
        self.audit_event_filter.addItem("Reopened", "reopened")
        self.audit_event_filter.currentIndexChanged.connect(self.refresh_audit_timeline)
        audit_controls.addWidget(self.audit_event_filter)
        self.audit_reload_btn = QPushButton("Refresh Audit")
        self.audit_reload_btn.setObjectName("TopRightButton")
        self.audit_reload_btn.clicked.connect(self.refresh_audit_timeline)
        audit_controls.addWidget(self.audit_reload_btn)
        self.audit_export_btn = QPushButton("Export CSV")
        self.audit_export_btn.setObjectName("TopRightButton")
        self.audit_export_btn.clicked.connect(self.export_audit_events_csv)
        audit_controls.addWidget(self.audit_export_btn)
        audit_controls.addStretch()
        self.layout.addLayout(audit_controls)

        self.audit_help_label = QLabel("Audit trail shows when a month was closed or reopened, who did it, and why.")
        self.audit_help_label.setStyleSheet("color: #5A7183; font-size: 11px;")
        self.audit_help_label.setWordWrap(True)
        self.layout.addWidget(self.audit_help_label)

        self.audit_summary_label = QLabel("No audit events loaded.")
        self.audit_summary_label.setStyleSheet("color: gray; font-size: 11px;")
        self.layout.addWidget(self.audit_summary_label)

        self.audit_table = QTableWidget(0, 6)
        self.audit_table.setHorizontalHeaderLabels(["Event", "At", "By", "Reason Code", "Reason", "Period"])
        self.audit_table.verticalHeader().setVisible(False)
        self.audit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.audit_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.layout.addWidget(self.audit_table)

        self.setStyleSheet(load_stylesheets())
        self.refresh_all_data()

        if not self.pro_enabled or not Permissions.has_permission("financialclose.close"):
            self.close_current_period_btn.setEnabled(False)
        if not self.pro_enabled or not Permissions.has_permission("financialclose.reopen"):
            self.reopen_btn.setEnabled(False)

    def reset_to_default(self):
        self.notes_input.clear()
        self.refresh_all_data()

    def refresh_all_data(self):
        self.refresh_closure_table()
        self.refresh_audit_timeline()

    def _selected_closure_payload(self):
        row = self.closures_table.currentRow()
        if row < 0:
            return None
        item = self.closures_table.item(row, 0)
        payload = item.data(Qt.UserRole) if item is not None else None
        return payload if isinstance(payload, dict) else None

    def refresh_closure_table(self):
        rows = list_recent_period_closures(limit=50)
        self.closures_table.setRowCount(0)
        for row_index, row in enumerate(rows):
            self.closures_table.insertRow(row_index)
            period_type_item = QTableWidgetItem(str(row.get("period_type") or "").title())
            period_type_item.setData(Qt.UserRole, row)
            self.closures_table.setItem(row_index, 0, period_type_item)
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
            self._update_closure_actions()
        else:
            self.details_btn.setEnabled(False)
            self.quarter_summary_btn.setEnabled(False)

    def _selected_audit_events(self):
        closure = self._selected_closure_payload()
        period_type = closure.get("period_type") if isinstance(closure, dict) else None
        period_label = closure.get("period_label") if isinstance(closure, dict) else None
        event_filter = str(self.audit_event_filter.currentData() or "").strip().lower()

        try:
            events = list_financial_close_audit_events(period_type=period_type, period_label=period_label, limit=100)
        except Exception:
            return []

        if event_filter:
            events = [event for event in events if str(event.get("event_type") or "").strip().lower() == event_filter]
        return events

    def refresh_audit_timeline(self):
        self.audit_table.setRowCount(0)
        events = self._selected_audit_events()

        count = len(events)
        filter_text = self.audit_event_filter.currentText()
        noun = "event" if count == 1 else "events"
        self.audit_summary_label.setText(f"Showing {count} {noun} · Filter: {filter_text}")

        for row_index, event in enumerate(events):
            event_type = str(event.get("event_type") or "").strip().lower()
            self.audit_table.insertRow(row_index)
            self.audit_table.setItem(row_index, 0, QTableWidgetItem(event_type.title()))
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
        default_name = f"financial_close_audit_{period_label}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Audit Events", default_name, "CSV Files (*.csv)")
        if not file_path:
            return

        try:
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
        except Exception as exc:
            AppMessageBox.critical(self, "Export Failed", str(exc))
            return

        AppMessageBox.information(self, "Export Complete", f"Audit events exported to:\n{file_path}")

    def _update_closure_actions(self):
        closure = self._selected_closure_payload()
        can_show = isinstance(closure, dict)
        self.details_btn.setEnabled(can_show)
        quarter_available = False
        if can_show:
            quarter_summary = get_quarter_summary_for_month(str(closure.get("period_label") or ""))
            quarter_available = bool(quarter_summary and quarter_summary.get("quarter_label"))
        self.quarter_summary_btn.setEnabled(can_show and quarter_available)
        can_reopen = can_show and self.pro_enabled and Permissions.has_permission("financialclose.reopen")
        self.reopen_btn.setEnabled(can_reopen)
        self.refresh_audit_timeline()

    def _build_closure_details_text(self, closure):
        if not isinstance(closure, dict):
            return "No closure data available."

        snapshot = closure.get("snapshot") if isinstance(closure.get("snapshot"), dict) else {}
        period_label = str(closure.get("period_label") or "")
        period_type = str(closure.get("period_type") or "").title()
        period_start = str(closure.get("period_start") or "")
        period_end = str(closure.get("period_end") or "")
        status = str(closure.get("status") or "")
        closed_at = str(closure.get("closed_at") or "")
        closed_by = str(closure.get("closed_by") or "")
        reopened_at = str(closure.get("reopened_at") or "")
        reopened_by = str(closure.get("reopened_by") or "")
        reopen_reason = str(closure.get("reopen_reason") or "")
        notes = str(closure.get("notes") or "")

        if not snapshot:
            return "No summary snapshot was saved for this period."

        lines = [
            f"{period_type} {period_label}".strip(),
            f"Range: {period_start} to {period_end}",
            f"Status: {status or '-'}",
            f"Closed At: {closed_at or '-'}",
            f"Closed By: {closed_by or '-'}",
            "",
            "Snapshot Totals",
            f"Sales Total: {float(snapshot.get('sales_total') or 0.0):,.2f}",
            f"Purchase Total: {float(snapshot.get('purchase_total') or 0.0):,.2f}",
            f"Expense Total: {float(snapshot.get('expense_total') or 0.0):,.2f}",
            f"Customer Due: {float(snapshot.get('customer_due') or 0.0):,.2f}",
            f"Supplier Due: {float(snapshot.get('supplier_due') or 0.0):,.2f}",
            f"Inventory Value: {float(snapshot.get('inventory_value') or 0.0):,.2f}",
        ]

        review_count = int(snapshot.get("review_item_count") or 0)
        if review_count:
            lines.append(f"Review Items Logged: {review_count}")

        if notes:
            lines.extend(["", f"Notes: {notes}"])

        if reopened_at or reopened_by or reopen_reason:
            lines.extend(
                [
                    "",
                    "Reopen Details",
                    f"Reopened At: {reopened_at or '-'}",
                    f"Reopened By: {reopened_by or '-'}",
                    f"Reason: {reopen_reason or '-'}",
                ]
            )

        return "\n".join(lines)

    def open_selected_details_dialog(self):
        closure = self._selected_closure_payload()
        if not isinstance(closure, dict):
            return
        details = self._build_closure_details_text(closure)
        AppMessageBox.information(self, "Month Details", details)

    def open_selected_quarter_summary(self):
        closure = self._selected_closure_payload()
        if not isinstance(closure, dict):
            return
        quarter_summary = get_quarter_summary_for_month(str(closure.get("period_label") or ""))
        quarter_label = str((quarter_summary or {}).get("quarter_label") or closure.get("quarter_label") or "").strip().upper()
        if not quarter_label:
            AppMessageBox.warning(self, "Quarter Summary", "Quarter summary is not available for the selected row.")
            return
        self.show_quarter_summary.emit(quarter_label)

    @Permissions.require_permission("financialclose.reopen")
    def reopen_selected_period(self):
        if not self.pro_enabled:
            AppMessageBox.warning(self, "Pro Feature", "Reopening financial periods is available in Pro version.")
            return

        closure = self._selected_closure_payload()
        if not isinstance(closure, dict):
            AppMessageBox.warning(self, "No Selection", "Choose a closed period first.")
            return

        notes = self.notes_input.text().strip()
        if not notes:
            AppMessageBox.warning(self, "Reason Required", "Please explain why this period needs to be reopened.")
            return

        answer = AppMessageBox.question(
            self,
            "Confirm Reopen",
            f"Reopen {closure.get('period_label') or 'selected period'}?\n\nThis should only be used for corrective action.",
        )
        if answer != AppMessageBox.Yes:
            return

        try:
            result = reopen_financial_period(
                period_type=closure.get("period_type"),
                period_label=closure.get("period_label"),
                reopened_by=str(QApplication.instance().property("username") or ""),
                reason=notes,
            )
        except Exception as exc:
            AppMessageBox.critical(self, "Reopen Failed", str(exc))
            return
        if not result.get("ok"):
            AppMessageBox.critical(self, "Reopen Failed", str(result.get("reason") or "Unknown error"))
            return

        AppMessageBox.information(self, "Reopened", "Financial period reopened successfully.")
        self.notes_input.clear()
        self.refresh_all_data()


sys.modules.setdefault("features.finance.ui.financial_close_list", sys.modules[__name__])
