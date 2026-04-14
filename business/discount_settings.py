from PySide6.QtCore import Qt, Signal
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from utilities.app_messagebox import AppMessageBox
from utilities.permissions import Permissions
from utilities.stylus import load_stylesheets


class DiscountSettingsWidget(QWidget):
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_discount_group_id = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Discount Settings", objectName="SectionTitle")
        self.back_btn = QPushButton("Back", objectName="TopRightButton")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.back_btn)
        self.layout.addLayout(header_layout)

        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        self.layout.addWidget(line)

        description = QLabel(
            "Create reusable discount groups with a percentage, an optional fixed amount, and a toggle for whether the group should auto-apply during sales."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #555; padding-left: 0;")
        self.layout.addWidget(description)

        form_card = QFrame()
        form_card.setObjectName("sectionCard")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Discount group name")

        self.percent_edit = QLineEdit()
        self.percent_edit.setPlaceholderText("0.00")

        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")

        self.apply_on_sale_check = QCheckBox("Apply automatically during sales")
        self.apply_on_sale_check.setChecked(True)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Active", "active")
        self.status_combo.addItem("Inactive", "inactive")

        self.sales_discount_policy_combo = QComboBox()
        self.sales_discount_policy_combo.addItem("Both Line And Header Discount", "both")
        self.sales_discount_policy_combo.addItem("Line Discount Only", "line_only")
        self.sales_discount_policy_combo.addItem("Header Discount Only", "header_only")

        self.global_discount_combo = QComboBox()
        self.global_discount_enabled_check = QCheckBox("Enable global sales promo discount")

        grid.addWidget(QLabel("Name"), 0, 0)
        grid.addWidget(self.name_edit, 0, 1)
        grid.addWidget(QLabel("Discount %"), 0, 2)
        grid.addWidget(self.percent_edit, 0, 3)
        grid.addWidget(QLabel("Fixed Amount"), 1, 0)
        grid.addWidget(self.amount_edit, 1, 1)
        grid.addWidget(QLabel("Status"), 1, 2)
        grid.addWidget(self.status_combo, 1, 3)
        grid.addWidget(QLabel("Sales Discount Policy"), 2, 0)
        grid.addWidget(self.sales_discount_policy_combo, 2, 1, 1, 3)
        grid.addWidget(self.apply_on_sale_check, 3, 0, 1, 4)

        for column in range(4):
            grid.setColumnStretch(column, 1)

        form_layout.addLayout(grid)

        button_row = QHBoxLayout()
        self.form_status = QLabel("Create a discount group and assign it to products or customers.")
        self.form_status.setStyleSheet("font-size: 11px; color: #666; padding-left: 0;")
        button_row.addWidget(self.form_status)
        button_row.addStretch()

        self.clear_btn = QPushButton("Clear", objectName="CancelButton")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_form)

        self.save_btn = QPushButton("Save Discount Group", objectName="SaveButton")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_discount_group)

        button_row.addWidget(self.clear_btn)
        button_row.addWidget(self.save_btn)
        form_layout.addLayout(button_row)

        self.layout.addWidget(form_card)

        promo_card = QFrame()
        promo_card.setObjectName("sectionCard")
        promo_layout = QVBoxLayout(promo_card)
        promo_layout.setContentsMargins(12, 12, 12, 12)
        promo_layout.setSpacing(10)

        promo_title = QLabel("Global Sales Promo")
        promo_title.setStyleSheet("font-weight: 700; font-size: 13px;")
        promo_layout.addWidget(promo_title)

        promo_hint = QLabel(
            "Choose a discount group here if you want one header discount to apply across all sales. This global promo overrides customer header discounts while enabled."
        )
        promo_hint.setWordWrap(True)
        promo_hint.setStyleSheet("color: #666; padding-left: 0;")
        promo_layout.addWidget(promo_hint)

        promo_grid = QGridLayout()
        promo_grid.setContentsMargins(0, 0, 0, 0)
        promo_grid.setHorizontalSpacing(12)
        promo_grid.setVerticalSpacing(10)
        promo_grid.addWidget(QLabel("Promo Discount Group"), 0, 0)
        promo_grid.addWidget(self.global_discount_combo, 0, 1)
        promo_grid.addWidget(self.global_discount_enabled_check, 1, 0, 1, 2)
        promo_grid.setColumnStretch(1, 1)
        promo_layout.addLayout(promo_grid)

        self.layout.addWidget(promo_card)

        table_card = QFrame()
        table_card.setObjectName("sectionCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(10)

        table_header = QHBoxLayout()
        table_title = QLabel("Configured Discount Groups")
        table_title.setStyleSheet("font-weight: 700; font-size: 13px;")
        table_header.addWidget(table_title)
        table_header.addStretch()
        self.refresh_btn = QPushButton("Refresh", objectName="TopRightButton")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.load_discount_groups)
        table_header.addWidget(self.refresh_btn)
        table_layout.addLayout(table_header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "Discount %", "Fixed Amount", "Apply On Sale", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self.load_selected_row)
        table_layout.addWidget(self.table)

        self.layout.addWidget(table_card, 1)
        self.setStyleSheet(load_stylesheets())
        self.load_discount_groups()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_discount_groups()

    def _read_money(self, text, label):
        try:
            return max(float(str(text or "").strip() or 0.0), 0.0)
        except ValueError:
            raise ValueError(f"{label} must be a valid number.")

    def clear_form(self):
        self.current_discount_group_id = None
        self.name_edit.clear()
        self.percent_edit.setText("0.00")
        self.amount_edit.setText("0.00")
        self.apply_on_sale_check.setChecked(True)
        self.status_combo.setCurrentIndex(0)
        self.load_sales_discount_policy()
        self.table.clearSelection()
        self.form_status.setText("Create a discount group and assign it to products or customers.")
        self.save_btn.setText("Save Discount Group")
        self.name_edit.setFocus()

    def load_sales_discount_policy(self):
        query = QSqlQuery()
        if query.exec("SELECT sales_discount_policy FROM accounting_settings WHERE id = 1") and query.next():
            policy = str(query.value(0) or "both").strip() or "both"
        else:
            policy = "both"
        index = self.sales_discount_policy_combo.findData(policy)
        self.sales_discount_policy_combo.setCurrentIndex(index if index >= 0 else 0)

    def populate_global_discount_combo(self, selected_id=None):
        self.global_discount_combo.blockSignals(True)
        self.global_discount_combo.clear()
        self.global_discount_combo.addItem("None", None)
        query = QSqlQuery()
        if query.exec(
            """
            SELECT id, name, COALESCE(discount_percent, 0), COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1)
            FROM discount_group
            WHERE COALESCE(status, 'active') = 'active'
            ORDER BY name ASC
            """
        ):
            while query.next():
                group_id = query.value(0)
                name = str(query.value(1) or "").strip()
                percent = float(query.value(2) or 0.0)
                fixed_amount = float(query.value(3) or 0.0)
                apply_on_sale = bool(int(query.value(4) or 0))
                self.global_discount_combo.addItem(
                    f"{name} ({percent:.2f}% + {fixed_amount:.2f}, {'Sale On' if apply_on_sale else 'Sale Off'})",
                    group_id,
                )
        index = self.global_discount_combo.findData(selected_id)
        self.global_discount_combo.setCurrentIndex(index if index >= 0 else 0)
        self.global_discount_combo.blockSignals(False)

    def load_global_sales_discount(self):
        query = QSqlQuery()
        if query.exec(
            """
            SELECT COALESCE(global_sales_discount_group_id, NULL), COALESCE(global_sales_discount_enabled, 0)
            FROM accounting_settings
            WHERE id = 1
            """
        ) and query.next():
            selected_group_id = query.value(0)
            enabled = bool(int(query.value(1) or 0))
        else:
            selected_group_id = None
            enabled = False
        self.populate_global_discount_combo(selected_group_id)
        self.global_discount_enabled_check.setChecked(enabled)

    def load_discount_groups(self):
        self.load_sales_discount_policy()
        self.load_global_sales_discount()
        query = QSqlQuery()
        if not query.exec(
            """
            SELECT id, name, COALESCE(discount_percent, 0), COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1), COALESCE(status, 'active')
            FROM discount_group
            ORDER BY
                CASE WHEN COALESCE(status, 'active') = 'active' THEN 0 ELSE 1 END,
                name ASC
            """
        ):
            AppMessageBox.error(self, "Load Failed", query.lastError().text())
            return

        self.table.setRowCount(0)
        while query.next():
            row = self.table.rowCount()
            self.table.insertRow(row)

            group_id = int(query.value(0))
            name = str(query.value(1) or "").strip()
            discount_percent = float(query.value(2) or 0.0)
            fixed_amount = float(query.value(3) or 0.0)
            apply_on_sale = int(query.value(4) or 0)
            status = str(query.value(5) or "active").strip()

            items = [
                QTableWidgetItem(name),
                QTableWidgetItem(f"{discount_percent:.2f}"),
                QTableWidgetItem(f"{fixed_amount:.2f}"),
                QTableWidgetItem("Yes" if apply_on_sale else "No"),
                QTableWidgetItem(status.title()),
            ]
            for col, item in enumerate(items):
                item.setData(Qt.UserRole, group_id)
                if col in (1, 2):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col in (3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

        if self.table.rowCount() == 0:
            self.form_status.setText("No discount groups yet. Create the first one here.")

    def load_selected_row(self):
        row = self.table.currentRow()
        if row < 0:
            return

        group_id_item = self.table.item(row, 0)
        if group_id_item is None:
            return

        group_id = group_id_item.data(Qt.UserRole)
        query = QSqlQuery()
        query.prepare(
            """
            SELECT name, COALESCE(discount_percent, 0), COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1), COALESCE(status, 'active')
            FROM discount_group
            WHERE id = ?
            """
        )
        query.addBindValue(group_id)
        if not query.exec() or not query.next():
            return

        self.current_discount_group_id = int(group_id)
        self.name_edit.setText(str(query.value(0) or "").strip())
        self.percent_edit.setText(f"{float(query.value(1) or 0.0):.2f}")
        self.amount_edit.setText(f"{float(query.value(2) or 0.0):.2f}")
        self.apply_on_sale_check.setChecked(bool(int(query.value(3) or 0)))
        status_index = self.status_combo.findData(str(query.value(4) or "active").strip())
        self.status_combo.setCurrentIndex(status_index if status_index >= 0 else 0)
        self.form_status.setText("Editing selected discount group.")
        self.save_btn.setText("Update Discount Group")

    @Permissions.require_permission("business.update")
    def save_discount_group(self):
        name = str(self.name_edit.text() or "").strip()
        if not name:
            AppMessageBox.warning(self, "Validation Error", "Discount group name is required.")
            self.name_edit.setFocus()
            return

        try:
            discount_percent = self._read_money(self.percent_edit.text(), "Discount percent")
            fixed_amount = self._read_money(self.amount_edit.text(), "Fixed amount")
        except ValueError as exc:
            AppMessageBox.warning(self, "Validation Error", str(exc))
            return

        status = self.status_combo.currentData()
        apply_on_sale = 1 if self.apply_on_sale_check.isChecked() else 0
        sales_discount_policy = self.sales_discount_policy_combo.currentData()
        global_discount_group_id = self.global_discount_combo.currentData()
        global_discount_enabled = 1 if self.global_discount_enabled_check.isChecked() else 0

        if global_discount_enabled and global_discount_group_id is None:
            AppMessageBox.warning(self, "Validation Error", "Select a global sales discount group before enabling the global promo.")
            return

        query = QSqlQuery()
        if self.current_discount_group_id is None:
            query.prepare(
                """
                INSERT INTO discount_group (name, discount_percent, fixed_amount, apply_on_sale, status)
                VALUES (?, ?, ?, ?, ?)
                """
            )
        else:
            query.prepare(
                """
                UPDATE discount_group
                SET name = ?, discount_percent = ?, fixed_amount = ?, apply_on_sale = ?, status = ?
                WHERE id = ?
                """
            )

        query.addBindValue(name)
        query.addBindValue(discount_percent)
        query.addBindValue(fixed_amount)
        query.addBindValue(apply_on_sale)
        query.addBindValue(status)
        if self.current_discount_group_id is not None:
            query.addBindValue(self.current_discount_group_id)

        if not query.exec():
            AppMessageBox.error(self, "Save Failed", query.lastError().text())
            return

        policy_query = QSqlQuery()
        policy_query.prepare(
            """
            INSERT INTO accounting_settings (
                id,
                sales_discount_policy,
                global_sales_discount_group_id,
                global_sales_discount_enabled,
                updated_at
            )
            VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id)
            DO UPDATE SET
                sales_discount_policy = excluded.sales_discount_policy,
                global_sales_discount_group_id = excluded.global_sales_discount_group_id,
                global_sales_discount_enabled = excluded.global_sales_discount_enabled,
                updated_at = CURRENT_TIMESTAMP
            """
        )
        policy_query.addBindValue(sales_discount_policy)
        policy_query.addBindValue(global_discount_group_id)
        policy_query.addBindValue(global_discount_enabled)
        if not policy_query.exec():
            AppMessageBox.error(self, "Save Failed", policy_query.lastError().text())
            return

        AppMessageBox.success(
            self,
            "Saved",
            "Discount group saved successfully." if self.current_discount_group_id is None else "Discount group updated successfully.",
        )
        self.load_discount_groups()
        self.clear_form()
