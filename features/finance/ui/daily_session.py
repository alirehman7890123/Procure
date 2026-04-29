import logging
import os
import sys

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QGridLayout, QPushButton,
    QLabel, QDialog, QComboBox, QFrame, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from medic.utilities.session_service import SessionErrorCode, check_active_session
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from features.finance.services import daily_session_service
from features.finance.services.financial_closing_service import get_month_close_prompt_state


logger = logging.getLogger(__name__)


def resource_path(relative_path):
    """Return the absolute path to a resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_stylesheets():
    """Load and combine all CSS files from the styles folder."""
    styles_dir = resource_path("styles")
    css_content = ""

    if os.path.exists(styles_dir):
        for file in os.listdir(styles_dir):
            if file.endswith(".css"):
                css_file = os.path.join(styles_dir, file)
                with open(css_file, "r") as f:
                    css_content += f.read() + "\n"

    return css_content


class MyTable(QTableWidget):
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(20)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = float(sum(self.column_ratios) or 0)
        if total <= 0:
            return
        width = max(0, self.viewport().width())
        for index, ratio in enumerate(self.column_ratios):
            self.setColumnWidth(index, int(width * (ratio / total)))


class DailySession(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Daily Sessions", objectName="SectionTitle")
        self.dashboard_btn = QPushButton("See Dashboard", objectName="TopRightButton")
        self.dashboard_btn.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.dashboard_btn)
        self.layout.addLayout(header_layout)

        self.add_history_summary_section()
        self.add_session_filters_section()
        self.add_session_history_section()

        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

        self.update_session_buttons()
        self.load_session_history()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_session_buttons()
        self.load_session_history()

    def _show_session_state_error(self, result, action_label="continue"):
        if result.code == SessionErrorCode.MULTIPLE_OPEN_SESSIONS:
            AppMessageBox.critical(
                self,
                "Session Data Error",
                "Multiple open daily sessions were found.\n\n"
                f"Please fix duplicate sessions before you {action_label}.",
            )
            return

        if result.code == SessionErrorCode.DB_ERROR:
            AppMessageBox.critical(
                self,
                "Database Error",
                f"Could not check daily session state.\n\n{result.error_text}",
            )
            return

        if result.code == SessionErrorCode.INVALID_SESSION_ROW:
            AppMessageBox.critical(
                self,
                "Session Data Error",
                "Daily session data is invalid. Please repair the latest open session record.",
            )

    def _get_strict_active_session_id(self, action_label="continue"):
        result = check_active_session(strict=True)
        if result.ok:
            return int(result.session_id)

        if result.code != SessionErrorCode.NO_OPEN_SESSION:
            self._show_session_state_error(result, action_label=action_label)
        return None

    def get_open_session(self):
        active_session_id = self._get_strict_active_session_id(action_label="view session details")
        if active_session_id is None:
            return None
        return daily_session_service.get_open_session(session_id=active_session_id)

    def open_session_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Open Daily Session")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        heading = QLabel("Open Daily Session")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("font-size:16px; font-weight:bold;")
        layout.addWidget(heading)

        form = QGridLayout()

        date_edit = QLineEdit()
        date_edit.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        date_edit.setReadOnly(True)

        carry_forward_edit = QLineEdit()
        carry_forward_edit.setReadOnly(True)
        carry_forward_edit.setText(str(self.get_previous_balance() or 0))

        added_cash_edit = QLineEdit()
        added_cash_edit.setPlaceholderText("Enter added cash")
        added_cash_edit.setText("0")

        opening_cash_edit = QLineEdit()
        opening_cash_edit.setReadOnly(True)

        def update_opening():
            try:
                carry = float(carry_forward_edit.text() or 0)
                added = float(added_cash_edit.text() or 0)
                opening_cash_edit.setText(str(carry + added))
            except ValueError:
                opening_cash_edit.setText("0")

        added_cash_edit.textChanged.connect(update_opening)
        update_opening()
        result_data = {}

        form.addWidget(QLabel("Date"), 0, 0)
        form.addWidget(date_edit, 0, 1)
        form.addWidget(QLabel("Carry Forward"), 1, 0)
        form.addWidget(carry_forward_edit, 1, 1)
        form.addWidget(QLabel("Added Cash"), 2, 0)
        form.addWidget(added_cash_edit, 2, 1)
        form.addWidget(QLabel("Opening Cash"), 3, 0)
        form.addWidget(opening_cash_edit, 3, 1)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        open_btn = QPushButton("Open Session")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        cancel_btn.clicked.connect(dialog.reject)

        def reset_form():
            carry_forward_edit.setText(str(self.get_previous_balance() or 0))
            added_cash_edit.setText("0")
            update_opening()

        def handle_open():
            try:
                added_cash = float(added_cash_edit.text() or 0)
                opening_cash = float(opening_cash_edit.text() or 0)
                if added_cash < 0:
                    AppMessageBox.warning(dialog, "Invalid Input", "Added cash cannot be negative.")
                    return
                if opening_cash < 0:
                    AppMessageBox.warning(dialog, "Invalid Input", "Opening cash cannot be negative.")
                    return
                result_data["session_date"] = date_edit.text().strip()
                result_data["carry_forward"] = float(carry_forward_edit.text() or 0)
                result_data["added_cash"] = added_cash
                result_data["opening_cash"] = opening_cash
                reset_form()
                dialog.accept()
            except ValueError:
                AppMessageBox.warning(dialog, "Invalid Input", "Please enter valid numeric values.")

        open_btn.clicked.connect(handle_open)

        if dialog.exec() == QDialog.Accepted:
            return result_data or {
                "session_date": date_edit.text().strip(),
                "carry_forward": float(carry_forward_edit.text() or 0),
                "added_cash": float(added_cash_edit.text() or 0),
                "opening_cash": float(opening_cash_edit.text() or 0),
            }
        return None

    def get_previous_balance(self):
        return daily_session_service.get_previous_balance()

    def get_cash_expenses(self):
        active_session_id = self._get_strict_active_session_id(action_label="close the session")
        if active_session_id is None:
            return 0.0
        return daily_session_service.get_cash_expenses(session_id=active_session_id)

    def get_session_payment_method_summary(self, methods=None):
        active_session_id = self._get_strict_active_session_id(action_label="close the session")
        if active_session_id is None:
            return {}
        return daily_session_service.get_session_payment_method_summary(session_id=active_session_id, methods=methods)

    def close_session_dialog(self, session_data):
        session_id, inflows, outflows = self.get_current_session_cash_flows()
        logger.debug(
            "Daily session close dialog cash flow snapshot",
            extra={"session_id": session_id, "inflows": inflows, "outflows": outflows},
        )

        opening_cash = self.get_opening_cash()
        cash_expenses = self.get_cash_expenses()
        non_cash_summary = self.get_session_payment_method_summary()

        dialog = QDialog(self)
        dialog.setWindowTitle("Close Daily Session")
        dialog.setMinimumWidth(560)

        layout = QVBoxLayout(dialog)
        heading = QLabel("Close Daily Session")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("font-size:16px; font-weight:bold;")
        layout.addWidget(heading)

        form = QGridLayout()
        opening_cash_edit = QLineEdit()
        opening_cash_edit.setReadOnly(True)
        opening_cash_edit.setText(str(session_data.get("opening_cash", 0)))

        system_cash_edit = QLineEdit()
        system_cash_edit.setReadOnly(True)
        system_cash_edit.setText(str(session_data.get("system_cash", 0)))

        actual_cash_edit = QLineEdit()
        actual_cash_edit.setPlaceholderText("Enter counted cash")

        withdraw_edit = QLineEdit()
        withdraw_edit.setPlaceholderText("Enter withdraw amount")
        withdraw_edit.setText("0")

        difference_edit = QLineEdit()
        difference_edit.setReadOnly(True)

        def update_difference():
            try:
                system = float(system_cash_edit.text() or 0)
                actual = float(actual_cash_edit.text() or 0)
                difference_edit.setText(str(actual - system))
            except ValueError:
                difference_edit.setText("0")

        actual_cash_edit.textChanged.connect(update_difference)
        update_difference()

        form.addWidget(QLabel("Opening Cash"), 0, 0)
        form.addWidget(opening_cash_edit, 0, 1)
        form.addWidget(QLabel("System Cash"), 1, 0)
        form.addWidget(system_cash_edit, 1, 1)
        form.addWidget(QLabel("Actual Cash"), 2, 0)
        form.addWidget(actual_cash_edit, 2, 1)
        form.addWidget(QLabel("Withdraw Amount"), 3, 0)
        form.addWidget(withdraw_edit, 3, 1)
        form.addWidget(QLabel("Difference"), 4, 0)
        form.addWidget(difference_edit, 4, 1)
        layout.addLayout(form)

        opening_cash_edit.setText(str(opening_cash))
        system_cash = opening_cash + inflows - outflows - cash_expenses
        system_cash_edit.setText(str(system_cash))

        non_cash_frame = QFrame()
        non_cash_frame.setObjectName("sectionCard")
        non_cash_layout = QVBoxLayout(non_cash_frame)
        non_cash_layout.setContentsMargins(10, 10, 10, 10)
        non_cash_layout.setSpacing(8)

        non_cash_title = QLabel("Non-Cash Session Summary")
        non_cash_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #223746; padding-left: 0;")
        non_cash_layout.addWidget(non_cash_title)

        non_cash_hint = QLabel("These amounts are informational and are not included in drawer cash.")
        non_cash_hint.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        non_cash_layout.addWidget(non_cash_hint)

        non_cash_grid = QGridLayout()
        non_cash_grid.setHorizontalSpacing(12)
        non_cash_grid.setVerticalSpacing(6)

        headers = ["Method", "Received", "Paid", "Expense", "Net"]
        for col, header_text in enumerate(headers):
            header = QLabel(header_text)
            header.setStyleSheet("font-weight: 700; color: #2F5D7C; padding-left: 0;")
            align = Qt.AlignLeft if col == 0 else Qt.AlignRight
            header.setAlignment(align | Qt.AlignVCenter)
            non_cash_grid.addWidget(header, 0, col)

        for row, method in enumerate(["Bank Transfer", "EasyPaisa", "JazzCash"], start=1):
            values = non_cash_summary.get(method, {})
            method_label = QLabel(method)
            method_label.setStyleSheet("font-weight: 600; color: #223746; padding-left: 0;")
            method_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            non_cash_grid.addWidget(method_label, row, 0)

            for col, key in enumerate(["received", "paid", "expense", "net"], start=1):
                amount = float(values.get(key, 0.0) or 0.0)
                amount_label = QLabel(f"{amount:,.2f}")
                color = "#223746"
                if key == "net" and amount > 0:
                    color = "#2E7D5A"
                elif key == "net" and amount < 0:
                    color = "#B74A4A"
                amount_label.setStyleSheet(
                    f"font-weight: {'700' if key == 'net' else '600'}; color: {color}; padding-left: 0;"
                )
                amount_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                non_cash_grid.addWidget(amount_label, row, col)

        non_cash_layout.addLayout(non_cash_grid)
        layout.addWidget(non_cash_frame)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close Session")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(close_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        cancel_btn.clicked.connect(dialog.reject)

        def handle_close():
            try:
                actual_cash = float(actual_cash_edit.text() or 0)
                withdraw_amount = float(withdraw_edit.text() or 0)
                if actual_cash < 0:
                    AppMessageBox.warning(dialog, "Invalid Input", "Actual cash cannot be negative.")
                    return
                if withdraw_amount < 0:
                    AppMessageBox.warning(dialog, "Invalid Input", "Withdraw amount cannot be negative.")
                    return
                dialog.accept()
            except ValueError:
                AppMessageBox.warning(dialog, "Invalid Input", "Please enter valid numeric values.")

        close_btn.clicked.connect(handle_close)

        if dialog.exec() == QDialog.Accepted:
            return {
                "system_cash": float(system_cash),
                "actual_cash": float(actual_cash_edit.text() or 0),
                "withdraw_amount": float(withdraw_edit.text() or 0),
                "cash_difference": float(difference_edit.text() or 0),
            }
        return None

    def get_opening_cash(self):
        active_session_id = self._get_strict_active_session_id(action_label="close the session")
        if active_session_id is None:
            return 0.0
        return daily_session_service.get_opening_cash(session_id=active_session_id)

    @Permissions.require_permission('dashboard')
    def handle_open_session(self):
        logger.info("Handling daily session open request")
        active_session = check_active_session(strict=True)
        if active_session.ok:
            AppMessageBox.info(self, "Session Already Open", "A daily session is already open.")
            self.update_session_buttons()
            return

        if active_session.code not in {SessionErrorCode.NO_OPEN_SESSION}:
            self._show_session_state_error(active_session, action_label="open a new session")
            self.update_session_buttons()
            return

        session_data = self.open_session_dialog()
        if not session_data:
            return

        try:
            daily_session_service.open_daily_session(
                session_date=session_data["session_date"],
                opening_cash=session_data["opening_cash"],
            )
        except Exception as exc:
            logger.error("Error opening session", extra={"error": str(exc)})
            AppMessageBox.error(self, "Database Error", f"Could not open daily session.\n\n{exc}")
            return

        self.update_session_buttons()
        self.load_session_history()
        AppMessageBox.success(self, "Session Opened", "Daily session opened successfully.")
        logger.info("Daily session opened successfully")

    @Permissions.require_permission('dashboard')
    def handle_close_session(self):
        session = self.get_open_session()
        if not session:
            AppMessageBox.warning(self, "No Active Session", "There is no active daily session to close.")
            return

        result = self.close_session_dialog(session)
        if not result:
            return

        try:
            daily_session_service.close_daily_session(
                session_id=session["id"],
                system_cash=result["system_cash"],
                actual_cash=result["actual_cash"],
                withdrawal=result["withdraw_amount"],
                cash_difference=result["cash_difference"],
            )
        except Exception as exc:
            logger.error("Error closing session", extra={"error": str(exc)})
            AppMessageBox.error(self, "Database Error", f"Could not close daily session.\n\n{exc}")
            return

        self.update_session_buttons()
        self.load_session_history()
        AppMessageBox.success(self, "Session Closed", "Daily session closed successfully.")

        state = get_month_close_prompt_state()
        if not state.get("show"):
            return

        answer = AppMessageBox.question(
            self,
            "Month Close Reminder",
            str(state.get("message") or ""),
        )
        if answer != QMessageBox.Yes:
            return

        main_window = self.window()
        if main_window is None or not hasattr(main_window, "set_financial_close"):
            AppMessageBox.warning(self, "Navigation Unavailable", "Could not open Financial Closing.")
            return

        main_window.set_financial_close(None, main_window.main_content_layout)
        if hasattr(main_window, "financial_close") and hasattr(main_window.financial_close, "set_financial_close_create_widget"):
            main_window.financial_close.set_financial_close_create_widget()

    def update_session_buttons(self):
        session_check = check_active_session(strict=True)
        if session_check.ok:
            self.session_msg.setText("Session is OPEN")
        elif session_check.code == SessionErrorCode.NO_OPEN_SESSION:
            self.session_msg.setText("No active session")
        elif session_check.code == SessionErrorCode.MULTIPLE_OPEN_SESSIONS:
            self.session_msg.setText("Session data error: multiple open sessions")
        else:
            self.session_msg.setText("Session status unavailable")

    def get_current_session_cash_flows(self):
        session_id = self._get_strict_active_session_id(action_label="close the session")
        if session_id is None:
            return None, 0.0, 0.0
        return daily_session_service.get_current_session_cash_flows(session_id=session_id)

    def add_history_summary_section(self):
        summary_frame = QFrame()
        summary_frame.setObjectName("sectionCard")
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        summary_layout.setSpacing(10)

        self.session_msg = QLabel("")
        self.session_msg.setStyleSheet("font-weight: 600; color: #2F5D7C;")
        summary_layout.addWidget(self.session_msg)
        summary_layout.addStretch()

        hint = QLabel("Open and close sessions from the Dashboard page.")
        hint.setStyleSheet("color: #666;")
        summary_layout.addWidget(hint)

        self.layout.addWidget(summary_frame)

    def add_session_filters_section(self):
        filter_frame = QFrame()
        filter_frame.setObjectName("sectionCard")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(12)

        count_label = QLabel("Show")
        count_label.setStyleSheet("font-weight: 600; color: #444;")
        filter_layout.addWidget(count_label)

        self.session_count_combo = QComboBox()
        self.session_count_combo.addItems(["10", "25", "50", "100"])
        self.session_count_combo.setCurrentText("10")
        self.session_count_combo.currentTextChanged.connect(self.load_session_history)
        filter_layout.addWidget(self.session_count_combo)

        status_label = QLabel("Status")
        status_label.setStyleSheet("font-weight: 600; color: #444;")
        filter_layout.addWidget(status_label)

        self.session_status_combo = QComboBox()
        self.session_status_combo.addItems(["All", "Open", "Closed"])
        self.session_status_combo.currentTextChanged.connect(self.load_session_history)
        filter_layout.addWidget(self.session_status_combo)

        date_from_label = QLabel("From")
        date_from_label.setStyleSheet("font-weight: 600; color: #444;")
        filter_layout.addWidget(date_from_label)

        self.session_date_from = QDateEdit()
        self.session_date_from.setCalendarPopup(True)
        self.session_date_from.setDisplayFormat("yyyy-MM-dd")
        self.session_date_from.setSpecialValueText("Any")
        self.session_date_from.setDateRange(QDate(2000, 1, 1), QDate(2099, 12, 31))
        self.session_date_from.setDate(QDate(2000, 1, 1))
        self.session_date_from.dateChanged.connect(self.load_session_history)
        filter_layout.addWidget(self.session_date_from)

        date_to_label = QLabel("To")
        date_to_label.setStyleSheet("font-weight: 600; color: #444;")
        filter_layout.addWidget(date_to_label)

        self.session_date_to = QDateEdit()
        self.session_date_to.setCalendarPopup(True)
        self.session_date_to.setDisplayFormat("yyyy-MM-dd")
        self.session_date_to.setSpecialValueText("Any")
        self.session_date_to.setDateRange(QDate(2000, 1, 1), QDate(2099, 12, 31))
        self.session_date_to.setDate(QDate(2000, 1, 1))
        self.session_date_to.dateChanged.connect(self.load_session_history)
        filter_layout.addWidget(self.session_date_to)

        self.session_date_clear_btn = QPushButton("Clear Dates", objectName="TopRightButton")
        self.session_date_clear_btn.setCursor(Qt.PointingHandCursor)
        self.session_date_clear_btn.clicked.connect(self.clear_session_date_filters)
        filter_layout.addWidget(self.session_date_clear_btn)

        filter_layout.addStretch()

        self.session_summary_label = QLabel("")
        self.session_summary_label.setStyleSheet("color: #666;")
        filter_layout.addWidget(self.session_summary_label)

        self.session_reload_btn = QPushButton("Reload", objectName="TopRightButton")
        self.session_reload_btn.setCursor(Qt.PointingHandCursor)
        self.session_reload_btn.clicked.connect(self.load_session_history)
        filter_layout.addWidget(self.session_reload_btn)

        self.layout.addWidget(filter_frame)

    def clear_session_date_filters(self):
        minimum_date = QDate(2000, 1, 1)
        self.session_date_from.blockSignals(True)
        self.session_date_to.blockSignals(True)
        self.session_date_from.setDate(minimum_date)
        self.session_date_to.setDate(minimum_date)
        self.session_date_from.blockSignals(False)
        self.session_date_to.blockSignals(False)
        self.load_session_history()

    def add_session_history_section(self):
        history_frame = QFrame()
        history_frame.setObjectName("sectionCard")
        history_layout = QVBoxLayout(history_frame)
        history_layout.setContentsMargins(10, 10, 10, 10)
        history_layout.setSpacing(8)

        title_row = QHBoxLayout()
        title = QLabel("Session History")
        title.setObjectName("SectionTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        history_layout.addLayout(title_row)

        self.session_table = MyTable(column_ratios=[0.06, 0.10, 0.12, 0.10, 0.10, 0.10, 0.10, 0.10, 0.09, 0.13])
        headers = ["ID", "Date", "Opened At", "Opening", "System", "Actual", "Withdraw", "Difference", "Status", "Closed At"]
        self.session_table.setColumnCount(len(headers))
        self.session_table.setHorizontalHeaderLabels(headers)
        self.session_table.verticalHeader().setVisible(False)
        self.session_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.session_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.session_table.setSelectionMode(QTableWidget.SingleSelection)
        self.session_table.setAlternatingRowColors(True)
        self.session_table.setWordWrap(False)
        self.session_table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.session_table.setMinimumWidth(700)
        self.session_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        history_layout.addWidget(self.session_table)
        self.layout.addWidget(history_frame)

    def load_session_history(self):
        try:
            limit = int(self.session_count_combo.currentText() or "10")
        except Exception:
            limit = 10

        status_filter = str(self.session_status_combo.currentText() or "All").strip().lower()
        minimum_date = QDate(2000, 1, 1)
        date_from = self.session_date_from.date() if self.session_date_from.date() > minimum_date else None
        date_to = self.session_date_to.date() if self.session_date_to.date() > minimum_date else None

        try:
            rows = daily_session_service.fetch_session_history(
                limit=limit,
                status_filter=status_filter,
                date_from=date_from.toString("yyyy-MM-dd") if date_from is not None else None,
                date_to=date_to.toString("yyyy-MM-dd") if date_to is not None else None,
            )
        except Exception as exc:
            self.session_table.setRowCount(0)
            self.session_summary_label.setText("Could not load sessions")
            AppMessageBox.critical(self, "Database Error", f"Could not load sessions.\n\n{exc}")
            return

        self.session_table.setRowCount(len(rows))
        for r, values in enumerate(rows):
            status_text = str(values[8] or "").strip().lower()
            if status_text == "open":
                bg_color = QColor("#E7F6EC")
            elif status_text == "closed":
                bg_color = QColor("#EEF3F8")
            else:
                bg_color = QColor("#FFFFFF")
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(bg_color)
                if c == 8:
                    if status_text == "open":
                        item.setForeground(Qt.darkGreen)
                    elif status_text == "closed":
                        item.setForeground(Qt.darkBlue)
                self.session_table.setItem(r, c, item)

        filter_label = status_filter.title() if status_filter in {"open", "closed"} else "All"
        date_parts = []
        if date_from is not None:
            date_parts.append(f"From {date_from.toString('yyyy-MM-dd')}")
        if date_to is not None:
            date_parts.append(f"To {date_to.toString('yyyy-MM-dd')}")
        date_summary = " | ".join(date_parts) if date_parts else "All dates"
        self.session_summary_label.setText(f"Showing {len(rows)} session(s) | Filter: {filter_label} | {date_summary}")
