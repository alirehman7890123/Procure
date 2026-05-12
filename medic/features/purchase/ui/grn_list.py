from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QDateEdit, QFrame, QTableWidget, QTableWidgetItem, QSizePolicy, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer

from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.table_helpers import centered_cell_widget, style_table_action_button
from medic.services.grn_transaction_service import (
    fetch_grn_health_check_counts,
    fetch_grn_list_rows,
)


class MyTable(QTableWidget):
    def __init__(self, column_ratios=None, parent=None):
        super().__init__(parent)
        self.column_ratios = column_ratios or []
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        if total <= 0:
            return
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            self.setColumnWidth(i, int(width * (ratio / total)))


class GRNListWidget(QWidget):
    add_grn_signal = Signal()
    detail_grn_signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Goods Receipt Notes", objectName="SectionTitle")
        self.add_grn_btn = QPushButton("Create GRN", objectName="TopRightButton")
        self.add_grn_btn.setCursor(Qt.PointingHandCursor)
        self.add_grn_btn.clicked.connect(self.add_grn_signal.emit)
        self.health_check_btn = QPushButton("PO/GRN Health Check", objectName="TopRightButton")
        self.health_check_btn.setCursor(Qt.PointingHandCursor)
        self.health_check_btn.clicked.connect(self.run_health_check)
        self.health_check_btn.setVisible(Permissions.has_permission("grn.audit"))
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.health_check_btn)
        header_layout.addWidget(self.add_grn_btn)
        self.layout.addLayout(header_layout)

        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        self.layout.addWidget(line)

        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(10)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search GRN number / PO number / supplier...")
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.load_grn_list)
        self.search_edit.textChanged.connect(lambda: self.search_timer.start(400))

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-90))

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())

        get_btn = QPushButton("Get Data", objectName="TopRightButton")
        get_btn.setCursor(Qt.PointingHandCursor)
        get_btn.clicked.connect(self.load_grn_list)

        filter_layout.addWidget(self.search_edit, 3)
        filter_layout.addWidget(QLabel("From"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("To"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(get_btn)

        self.layout.addLayout(filter_layout)

        self.table = MyTable(column_ratios=[0.06, 0.15, 0.15, 0.23, 0.12, 0.11, 0.10, 0.08])
        headers = ["ID", "GRN", "PO", "Supplier", "GRN Date", "Status", "Total", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setMinimumWidth(700)
        self.table.setFixedHeight(400)
        self.layout.addWidget(self.table)
        self.layout.addStretch()

        self.setStyleSheet(load_stylesheets())

    def showEvent(self, event):
        super().showEvent(event)
        self.load_grn_list()

    def load_grn_list(self):
        search = (self.search_edit.text() or "").strip()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        try:
            rows = fetch_grn_list_rows(date_from=date_from, date_to=date_to, search_text=search)
        except Exception as exc:
            self.table.setRowCount(0)
            print(str(exc))
            return

        self.table.setRowCount(0)
        row = 0
        for row_data in rows:
            self.table.insertRow(row)

            grn_id = int(row_data["grn_id"] or 0)
            self.table.setItem(row, 0, QTableWidgetItem(str(grn_id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(row_data["grn_number"] or "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(row_data["po_number"] or "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(row_data["supplier_name"] or "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(row_data["grn_date"] or "")))
            self.table.setItem(row, 5, QTableWidgetItem(str(row_data["status"] or "")))
            self.table.setItem(row, 6, QTableWidgetItem(f"{float(row_data['total_value'] or 0):.2f}"))

            detail_btn = style_table_action_button(QPushButton("Details"))
            detail_btn.setCursor(Qt.PointingHandCursor)
            detail_btn.clicked.connect(lambda _=False, gid=grn_id: self.detail_grn_signal.emit(gid))
            self.table.setCellWidget(row, 7, centered_cell_widget(detail_btn))

            row += 1

    def run_health_check(self):
        checks = fetch_grn_health_check_counts()

        lines = []
        total_issues = 0
        for row in checks:
            label = row["label"]
            count = row["count"]
            if count is None:
                lines.append(f"- {label}: error while checking")
                total_issues += 1
                continue
            lines.append(f"- {label}: {count}")
            total_issues += count

        report = "\n".join(lines)
        if total_issues == 0:
            AppMessageBox.information(
                self,
                "PO/GRN Health Check",
                "No inconsistencies found.\n\n" + report,
            )
        else:
            AppMessageBox.warning(
                self,
                "PO/GRN Health Check",
                f"Detected {total_issues} issue(s).\n\n" + report,
            )
