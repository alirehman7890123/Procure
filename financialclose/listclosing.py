import csv
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
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

from services.financial_closing_service import (
    get_quarter_label_from_month,
    get_quarter_summary_for_month,
    is_quarter_end_month,
    list_financial_close_audit_events,
    list_recent_period_closures,
    reopen_financial_period,
)
from utilities.app_messagebox import AppMessageBox
from utilities.permissions import Permissions
from utilities.stylus import load_stylesheets


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
            [
                "Type",
                "Label",
                "Range",
                "Status",
                "Closed At",
                "Closed By",
                "Reopened At",
                "Reopened By",
                "Reopen Reason",
            ]
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
        self.audit_table.setHorizontalHeaderLabels(
            ["Event", "At", "By", "Reason Code", "Reason", "Period"]
        )
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
            self.closures_table.setItem(
                row_index,
                2,
                QTableWidgetItem(f"{row.get('period_start') or ''} to {row.get('period_end') or ''}"),
            )
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
            events = list_financial_close_audit_events(
                period_type=period_type,
                period_label=period_label,
                limit=100,
            )
        except Exception:
            return []

        if event_filter:
            events = [
                event
                for event in events
                if str(event.get("event_type") or "").strip().lower() == event_filter
            ]
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
                QTableWidgetItem(
                    f"{str(event.get('period_type') or '').title()} {str(event.get('period_label') or '')}".strip()
                ),
            )

    def export_audit_events_csv(self):
        events = self._selected_audit_events()
        if not events:
            AppMessageBox.warning(self, "No Data", "There are no audit events to export for the selected filter.")
            return

        closure = self._selected_closure_payload()
        period_label = str(closure.get("period_label") or "all") if isinstance(closure, dict) else "all"
        default_name = f"financial_close_audit_{period_label}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Audit Events",
            default_name,
            "CSV Files (*.csv)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["event", "event_at", "event_by", "reason_code", "reason_text", "period_type", "period_label"])
                for event in events:
                    writer.writerow(
                        [
                            str(event.get("event_type") or ""),
                            str(event.get("event_at") or ""),
                            str(event.get("event_by") or ""),
                            str(event.get("reason_code") or ""),
                            str(event.get("reason_text") or ""),
                            str(event.get("period_type") or ""),
                            str(event.get("period_label") or ""),
                        ]
                    )
        except OSError as exc:
            AppMessageBox.error(self, "Export Failed", f"Could not save CSV file.\n\n{exc}")
            return

        record_count = len(events)
        noun = "record" if record_count == 1 else "records"
        AppMessageBox.information(
            self,
            "Export Complete",
            f"Exported {record_count} audit {noun} to:\n{file_path}",
        )

    def reopen_selected_period(self):
        if not self.pro_enabled:
            AppMessageBox.warning(self, "Pro Feature", "Reopen controls are available in Pro version.")
            return
        if not Permissions.has_permission("financialclose.reopen"):
            AppMessageBox.critical(self, "Not Authorized", "You do not have permission to reopen financial periods.")
            return

        closure = self._selected_closure_payload()
        if not isinstance(closure, dict):
            AppMessageBox.warning(self, "Select Period", "Select a period row to reopen.")
            return

        if str(closure.get("status") or "").strip().lower() != "closed":
            AppMessageBox.warning(self, "Reopen Not Allowed", "Only closed periods can be reopened.")
            return

        reason = self._validated_reopen_reason()
        if reason is None:
            return

        app = QApplication.instance()
        reopened_by = str((app.property("username") if app else "") or "system")
        result = reopen_financial_period(
            period_type=str(closure.get("period_type") or "").strip().lower(),
            period_label=str(closure.get("period_label") or "").strip(),
            reopened_by=reopened_by,
            reason=reason,
        )
        if not result.get("ok"):
            AppMessageBox.error(self, "Reopen Failed", str(result.get("reason") or "Unknown error"))
            return

        AppMessageBox.information(self, "Period Reopened", "Selected period has been reopened.")
        self.refresh_all_data()

    def _validated_reopen_reason(self):
        reason = self.notes_input.text().strip()
        if not reason:
            AppMessageBox.warning(self, "Reason Required", "Enter a note to explain why this period is being reopened.")
            return None
        if len(reason) < 10:
            AppMessageBox.warning(self, "Reason Too Short", "Reopen reason must be at least 10 characters.")
            return None
        if len(reason.split()) < 2:
            AppMessageBox.warning(self, "Reason Too Short", "Reopen reason should include at least two words.")
            return None
        return reason

    def _update_closure_actions(self):
        closure = self._selected_closure_payload()
        if not isinstance(closure, dict):
            self.details_btn.setEnabled(False)
            self.quarter_summary_btn.setEnabled(False)
            self.refresh_audit_timeline()
            return

        snapshot = closure.get("snapshot") if isinstance(closure.get("snapshot"), dict) else {}
        self.details_btn.setEnabled(bool(snapshot) or bool(closure))
        can_view_quarter = bool(
            is_quarter_end_month(closure.get("period_label")) and get_quarter_summary_for_month(closure.get("period_label"))
        )
        self.quarter_summary_btn.setEnabled(can_view_quarter)
        self.refresh_audit_timeline()

    def _build_snapshot_details_text(self, snapshot, compact=False):
        if not isinstance(snapshot, dict) or not snapshot:
            return "No snapshot data saved for this period."

        def _money(value):
            try:
                return f"{float(value or 0):.2f}"
            except (TypeError, ValueError):
                return "0.00"

        lines = [
            f"Closed At: {snapshot.get('closed_at') or '-'}",
            f"Sales: {_money(snapshot.get('sales_total'))}",
            f"Purchases: {_money(snapshot.get('purchase_total'))}",
            f"Expenses: {_money(snapshot.get('expense_total'))}",
            f"Customer Due: {_money(snapshot.get('customer_due'))}",
            f"Supplier Due: {_money(snapshot.get('supplier_due'))}",
            f"Inventory Value: {_money(snapshot.get('inventory_value'))}",
        ]

        if compact:
            return " | ".join(lines[1:])
        return "\n".join(lines)

    def open_selected_details_dialog(self):
        closure = self._selected_closure_payload()
        if not isinstance(closure, dict):
            AppMessageBox.warning(self, "Select Period", "Select a closure row to view closing details.")
            return

        snapshot = closure.get("snapshot") if isinstance(closure.get("snapshot"), dict) else {}
        dialog = QDialog(self)
        dialog.setWindowTitle("Closing Details")
        dialog.setMinimumWidth(720)
        dialog.setModal(True)
        dialog.setStyleSheet(load_stylesheets())

        root_layout = QVBoxLayout(dialog)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(12)

        header_section = QFrame()
        header_section.setStyleSheet(self._dialog_section_style("header"))
        header_layout = QVBoxLayout(header_section)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_title = QLabel(f"{str(closure.get('period_label') or '').strip()} Closing Details")
        header_title.setObjectName("SectionTitle")
        header_subtitle = QLabel(
            f"Status: {str(closure.get('status') or '-').title()} | Closed by {closure.get('closed_by') or '-'}"
        )
        header_subtitle.setStyleSheet("color: #5A7183;")
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_subtitle)
        root_layout.addWidget(header_section)

        content_section = QFrame()
        content_section.setStyleSheet(self._dialog_section_style("content"))
        content_layout = QVBoxLayout(content_section)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)

        meta_grid = QGridLayout()
        meta_grid.setHorizontalSpacing(20)
        meta_grid.setVerticalSpacing(8)
        details_rows = [
            ("Period", f"{self._format_date(closure.get('period_start'))} to {self._format_date(closure.get('period_end'))}"),
            ("Closed At", self._format_datetime(closure.get("closed_at"))),
            ("Closed By", str(closure.get("closed_by") or "-")),
            ("Notes", str(closure.get("notes") or "-")),
            ("Reopened At", self._format_datetime(closure.get("reopened_at"))),
            ("Reopened By", str(closure.get("reopened_by") or "-")),
            ("Reopen Code", str(closure.get("reopen_reason_code") or "-")),
            ("Reopen Reason", str(closure.get("reopen_reason") or "-")),
        ]
        for row_index, (label_text, value_text) in enumerate(details_rows):
            key_label = QLabel(label_text)
            key_label.setStyleSheet("font-weight: 700; color: #314757;")
            value_label = QLabel(value_text)
            value_label.setWordWrap(True)
            meta_grid.addWidget(key_label, row_index, 0, Qt.AlignTop)
            meta_grid.addWidget(value_label, row_index, 1, Qt.AlignTop)
        content_layout.addLayout(meta_grid)

        snapshot_title = QLabel("Saved Snapshot")
        snapshot_title.setObjectName("SectionTitle")
        content_layout.addWidget(snapshot_title)

        snapshot_grid = QGridLayout()
        snapshot_grid.setHorizontalSpacing(20)
        snapshot_grid.setVerticalSpacing(8)
        snapshot_rows = [
            ("Sales", self._money(snapshot.get("sales_total"))),
            ("Purchases", self._money(snapshot.get("purchase_total"))),
            ("Expenses", self._money(snapshot.get("expense_total"))),
            ("Customer Due", self._money(snapshot.get("customer_due"))),
            ("Supplier Due", self._money(snapshot.get("supplier_due"))),
            ("Inventory Value", self._money(snapshot.get("inventory_value"))),
        ]
        for row_index, (label_text, value_text) in enumerate(snapshot_rows):
            key_label = QLabel(label_text)
            key_label.setStyleSheet("font-weight: 700; color: #314757;")
            value_label = QLabel(value_text)
            snapshot_grid.addWidget(key_label, row_index, 0, Qt.AlignTop)
            snapshot_grid.addWidget(value_label, row_index, 1, Qt.AlignTop)
        content_layout.addLayout(snapshot_grid)
        root_layout.addWidget(content_section)

        footer_section = QFrame()
        footer_section.setStyleSheet(self._dialog_section_style("footer"))
        footer_layout = QHBoxLayout(footer_section)
        footer_layout.setContentsMargins(12, 12, 12, 12)
        footer_layout.setSpacing(8)
        footer_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("TopRightButton")
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)
        root_layout.addWidget(footer_section)

        dialog.exec()

    def open_selected_quarter_summary(self):
        closure = self._selected_closure_payload()
        if not isinstance(closure, dict):
            AppMessageBox.warning(self, "Select Period", "Select a quarter-ending month to view the quarter summary.")
            return
        if not is_quarter_end_month(closure.get("period_label")):
            AppMessageBox.warning(self, "Unavailable", "Quarter summary is only available for quarter-ending months.")
            return
        if not get_quarter_summary_for_month(closure.get("period_label")):
            AppMessageBox.warning(self, "Unavailable", "Quarter summary is not available until all three months are closed.")
            return

        self.show_quarter_summary.emit(get_quarter_label_from_month(closure.get("period_label")))

    def _format_date(self, value):
        text = str(value or "").strip()
        if not text:
            return "-"
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).strftime("%B %d, %Y")
            except ValueError:
                continue
        return text

    def _format_datetime(self, value):
        text = str(value or "").strip()
        if not text:
            return "-"
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).strftime("%B %d, %Y %I:%M %p")
            except ValueError:
                continue
        return text

    def _money(self, value):
        try:
            return f"{float(value or 0):.2f}"
        except (TypeError, ValueError):
            return "0.00"

    def _dialog_section_style(self, section):
        if section == "header":
            return "QFrame { background-color: #EEF4F7; border: 1px solid #D7E2E8; border-radius: 10px; }"
        if section == "footer":
            return "QFrame { background-color: #F4F8FB; border: 1px solid #D7E2E8; border-radius: 10px; }"
        return "QFrame { background-color: #FFFFFF; border: 1px solid #D7E2E8; border-radius: 10px; }"
