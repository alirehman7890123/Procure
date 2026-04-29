from functools import partial

from PySide6.QtWidgets import QWidget, QLineEdit, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt, Signal

from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from features.admin.services.user_service import fetch_user_list_rows


class UserListWidget(QWidget):
    detailpagesignal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("User Information", objectName="SectionTitle")
        self.adduser = QPushButton("Add User", objectName="TopRightButton")
        self.adduser.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.adduser)

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

        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search User...")
        self.search_edit.textChanged.connect(self.search_rows)
        search_layout.addWidget(self.search_edit)
        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)

        self.row_height = 35

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10, 0.10])
        headers = ["No.", "First Name", "Last Name", "Email", "Username", "Role", "Status", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        detail_col = headers.index("Detail")
        self.table.horizontalHeaderItem(detail_col).setTextAlignment(Qt.AlignCenter)

        self.table.setStyleSheet("QTableWidget::item { color: #333; }")
        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        self.table.setMinimumWidth(700)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

    def search_rows(self, text):
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_users_into_table()

    def load_users_into_table(self):
        try:
            rows = fetch_user_list_rows()
        except Exception as exc:
            self.table.setRowCount(0)
            AppMessageBox.critical(self, "Database Error", str(exc))
            return

        self.table.setRowCount(0)

        row = 0
        for row_data in rows:
            self.table.insertRow(row)

            row_no = row + 1
            user_id = int(row_data.get("id", 0) or 0)
            firstname = QTableWidgetItem(str(row_data.get("firstname", "")))
            lastname = QTableWidgetItem(str(row_data.get("lastname", "")))
            email = QTableWidgetItem(str(row_data.get("email", "")))
            username = QTableWidgetItem(str(row_data.get("username", "")))
            role = QTableWidgetItem(str(row_data.get("role", "")))
            status = QTableWidgetItem(str(row_data.get("status", "")))

            self.table.setItem(row, 0, QTableWidgetItem(str(row_no)))
            self.table.setItem(row, 1, firstname)
            self.table.setItem(row, 2, lastname)
            self.table.setItem(row, 3, email)
            self.table.setItem(row, 4, username)
            self.table.setItem(row, 5, role)
            self.table.setItem(row, 6, status)

            detail = QPushButton("Details")
            detail.setCursor(Qt.PointingHandCursor)
            detail.setStyleSheet(
                """
                    QPushButton {
                        background-color: transparent;
                        color: #333;
                        padding: 4px 12px;
                        border-radius: 2px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #244A62;
                        color: #fff;
                    }
                    QPushButton:pressed {
                        background-color: #2F5D7C;
                        color: #fff;
                    }
                """
            )

            self.table.setCellWidget(row, 7, detail)
            detail.clicked.connect(partial(self.detailpagesignal.emit, user_id))

            row += 1


class MyTable(QTableWidget):
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return

        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            col_width = int(width * (ratio / total))
            self.setColumnWidth(i, col_width)
