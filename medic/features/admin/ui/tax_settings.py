from PySide6.QtCore import Qt, Signal
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

from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.permissions import Permissions
from medic.utilities.stylus import load_stylesheets
from medic.services.accounting_settings_service import (
    load_sales_tax_settings as load_sales_tax_settings_from_service,
    save_sales_tax_settings as save_sales_tax_settings_to_service,
)
from medic.services.group_settings_service import (
    fetch_active_sales_groups,
    fetch_sales_group_detail,
    fetch_sales_groups,
    save_sales_group,
)


class TaxSettingsWidget(QWidget):
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tax_group_id = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Tax Settings", objectName="SectionTitle")
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
            "Create reusable tax groups with a percentage, an optional fixed amount, and a toggle for whether the group should auto-apply during sales."
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
        self.name_edit.setPlaceholderText("Tax group name")

        self.percent_edit = QLineEdit()
        self.percent_edit.setPlaceholderText("0.00")

        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")

        self.apply_on_sale_check = QCheckBox("Apply automatically during sales")
        self.apply_on_sale_check.setChecked(True)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Active", "active")
        self.status_combo.addItem("Inactive", "inactive")

        self.sales_tax_policy_combo = QComboBox()
        self.sales_tax_policy_combo.addItem("Both Line And Header Tax", "both")
        self.sales_tax_policy_combo.addItem("Line Tax Only", "line_only")
        self.sales_tax_policy_combo.addItem("Header Tax Only", "header_only")

        self.global_tax_combo = QComboBox()
        self.global_tax_enabled_check = QCheckBox("Enable global sales tax")

        grid.addWidget(QLabel("Name"), 0, 0)
        grid.addWidget(self.name_edit, 0, 1)
        grid.addWidget(QLabel("Tax %"), 0, 2)
        grid.addWidget(self.percent_edit, 0, 3)
        grid.addWidget(QLabel("Fixed Amount"), 1, 0)
        grid.addWidget(self.amount_edit, 1, 1)
        grid.addWidget(QLabel("Status"), 1, 2)
        grid.addWidget(self.status_combo, 1, 3)
        grid.addWidget(QLabel("Sales Tax Policy"), 2, 0)
        grid.addWidget(self.sales_tax_policy_combo, 2, 1, 1, 3)
        grid.addWidget(self.apply_on_sale_check, 3, 0, 1, 4)

        for column in range(4):
            grid.setColumnStretch(column, 1)

        form_layout.addLayout(grid)

        button_row = QHBoxLayout()
        self.form_status = QLabel("Create a tax group and assign it to products or customers.")
        self.form_status.setStyleSheet("font-size: 11px; color: #666; padding-left: 0;")
        button_row.addWidget(self.form_status)
        button_row.addStretch()

        self.clear_btn = QPushButton("Clear", objectName="CancelButton")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_form)

        self.save_btn = QPushButton("Save Tax Group", objectName="SaveButton")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_tax_group)

        button_row.addWidget(self.clear_btn)
        button_row.addWidget(self.save_btn)
        form_layout.addLayout(button_row)

        self.layout.addWidget(form_card)

        promo_card = QFrame()
        promo_card.setObjectName("sectionCard")
        promo_layout = QVBoxLayout(promo_card)
        promo_layout.setContentsMargins(12, 12, 12, 12)
        promo_layout.setSpacing(10)

        promo_title = QLabel("Global Sales Tax")
        promo_title.setStyleSheet("font-weight: 700; font-size: 13px;")
        promo_layout.addWidget(promo_title)

        promo_hint = QLabel(
            "Choose a tax group here if you want one header tax to apply across all sales. This global tax overrides customer header tax while enabled."
        )
        promo_hint.setWordWrap(True)
        promo_hint.setStyleSheet("color: #666; padding-left: 0;")
        promo_layout.addWidget(promo_hint)

        promo_grid = QGridLayout()
        promo_grid.setContentsMargins(0, 0, 0, 0)
        promo_grid.setHorizontalSpacing(12)
        promo_grid.setVerticalSpacing(10)
        promo_grid.addWidget(QLabel("Global Tax Group"), 0, 0)
        promo_grid.addWidget(self.global_tax_combo, 0, 1)
        promo_grid.addWidget(self.global_tax_enabled_check, 1, 0, 1, 2)
        promo_grid.setColumnStretch(1, 1)
        promo_layout.addLayout(promo_grid)

        promo_actions = QHBoxLayout()
        self.settings_status = QLabel("Sales tax policy and global tax are saved separately from the group form.")
        self.settings_status.setStyleSheet("font-size: 11px; color: #666; padding-left: 0;")
        promo_actions.addWidget(self.settings_status)
        promo_actions.addStretch()
        self.save_settings_btn = QPushButton("Save Sales Tax Settings", objectName="SaveButton")
        self.save_settings_btn.setCursor(Qt.PointingHandCursor)
        self.save_settings_btn.clicked.connect(self.save_sales_tax_settings)
        promo_actions.addWidget(self.save_settings_btn)
        promo_layout.addLayout(promo_actions)

        self.layout.addWidget(promo_card)

        table_card = QFrame()
        table_card.setObjectName("sectionCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(10)

        table_header = QHBoxLayout()
        table_title = QLabel("Configured Tax Groups")
        table_title.setStyleSheet("font-weight: 700; font-size: 13px;")
        table_header.addWidget(table_title)
        table_header.addStretch()
        self.refresh_btn = QPushButton("Refresh", objectName="TopRightButton")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.load_tax_groups)
        table_header.addWidget(self.refresh_btn)
        table_layout.addLayout(table_header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "Tax %", "Fixed Amount", "Apply On Sale", "Status"])
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
        self.load_tax_groups()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_tax_groups()

    def _read_money(self, text, label):
        try:
            return max(float(str(text or "").strip() or 0.0), 0.0)
        except ValueError:
            raise ValueError(f"{label} must be a valid number.")

    def clear_form(self):
        self.current_tax_group_id = None
        self.name_edit.clear()
        self.percent_edit.setText("0.00")
        self.amount_edit.setText("0.00")
        self.apply_on_sale_check.setChecked(True)
        self.status_combo.setCurrentIndex(0)
        self.load_sales_tax_policy()
        self.load_global_sales_tax()
        self.table.clearSelection()
        self.form_status.setText("Create a tax group and assign it to products or customers.")
        self.save_btn.setText("Save Tax Group")
        self.name_edit.setFocus()

    def load_sales_tax_policy(self):
        settings = load_sales_tax_settings_from_service()
        policy = settings["policy"]
        index = self.sales_tax_policy_combo.findData(policy)
        self.sales_tax_policy_combo.setCurrentIndex(index if index >= 0 else 0)

    def populate_global_tax_combo(self, selected_id=None):
        self.global_tax_combo.blockSignals(True)
        self.global_tax_combo.clear()
        self.global_tax_combo.addItem("None", None)
        try:
            groups = fetch_active_sales_groups("tax")
        except Exception as exc:
            AppMessageBox.error(self, "Load Failed", str(exc))
            self.global_tax_combo.blockSignals(False)
            return

        for group in groups:
            self.global_tax_combo.addItem(
                f"{group['name']} ({group['percent']:.2f}% + {group['fixed_amount']:.2f}, {'Sale On' if group['apply_on_sale'] else 'Sale Off'})",
                group["id"],
            )
        index = self.global_tax_combo.findData(selected_id)
        self.global_tax_combo.setCurrentIndex(index if index >= 0 else 0)
        self.global_tax_combo.blockSignals(False)

    def load_global_sales_tax(self):
        settings = load_sales_tax_settings_from_service()
        selected_group_id = settings["group_id"]
        enabled = bool(settings["enabled"])
        self.populate_global_tax_combo(selected_group_id)
        self.global_tax_enabled_check.setChecked(enabled)

    def save_sales_tax_settings(self, show_feedback=True):
        sales_tax_policy = self.sales_tax_policy_combo.currentData()
        global_tax_group_id = self.global_tax_combo.currentData()
        global_tax_enabled = 1 if self.global_tax_enabled_check.isChecked() else 0
        try:
            save_sales_tax_settings_to_service(
                policy=sales_tax_policy,
                group_id=global_tax_group_id,
                enabled=bool(global_tax_enabled),
            )
        except ValueError as exc:
            AppMessageBox.warning(self, "Validation Error", str(exc))
            return False
        except Exception as exc:
            AppMessageBox.error(self, "Save Failed", str(exc))
            return False

        self.load_sales_tax_policy()
        self.load_global_sales_tax()
        self.settings_status.setText("Sales tax settings saved.")
        if show_feedback:
            AppMessageBox.success(self, "Saved", "Sales tax settings saved successfully.")
        return True

    def load_tax_groups(self):
        self.load_sales_tax_policy()
        self.load_global_sales_tax()
        try:
            groups = fetch_sales_groups("tax")
        except Exception as exc:
            AppMessageBox.error(self, "Load Failed", str(exc))
            return

        self.table.setRowCount(0)
        for group in groups:
            row = self.table.rowCount()
            self.table.insertRow(row)

            items = [
                QTableWidgetItem(group["name"]),
                QTableWidgetItem(f"{group['percent']:.2f}"),
                QTableWidgetItem(f"{group['fixed_amount']:.2f}"),
                QTableWidgetItem("Yes" if group["apply_on_sale"] else "No"),
                QTableWidgetItem(group["status"].title()),
            ]
            for col, item in enumerate(items):
                item.setData(Qt.UserRole, group["id"])
                if col in (1, 2):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col in (3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

        if self.table.rowCount() == 0:
            self.form_status.setText("No tax groups yet. Create the first one here.")

    def load_selected_row(self):
        row = self.table.currentRow()
        if row < 0:
            return

        group_id_item = self.table.item(row, 0)
        if group_id_item is None:
            return

        group_id = group_id_item.data(Qt.UserRole)
        try:
            group = fetch_sales_group_detail("tax", group_id)
        except Exception as exc:
            AppMessageBox.error(self, "Load Failed", str(exc))
            return
        if not group:
            return

        self.current_tax_group_id = int(group_id)
        self.name_edit.setText(group["name"])
        self.percent_edit.setText(f"{group['percent']:.2f}")
        self.amount_edit.setText(f"{group['fixed_amount']:.2f}")
        self.apply_on_sale_check.setChecked(group["apply_on_sale"])
        status_index = self.status_combo.findData(group["status"])
        self.status_combo.setCurrentIndex(status_index if status_index >= 0 else 0)
        self.form_status.setText("Editing selected tax group.")
        self.save_btn.setText("Update Tax Group")

    @Permissions.require_permission("business.update")
    def save_tax_group(self):
        name = str(self.name_edit.text() or "").strip()
        if not name:
            AppMessageBox.warning(self, "Validation Error", "Tax group name is required.")
            self.name_edit.setFocus()
            return

        status = self.status_combo.currentData()
        try:
            save_sales_group(
                group_kind="tax",
                name=name,
                percent_text=self.percent_edit.text(),
                fixed_amount_text=self.amount_edit.text(),
                apply_on_sale=self.apply_on_sale_check.isChecked(),
                status=status,
                group_id=self.current_tax_group_id,
            )
        except ValueError as exc:
            AppMessageBox.warning(self, "Validation Error", str(exc))
            return
        except Exception as exc:
            AppMessageBox.error(self, "Save Failed", str(exc))
            return

        if not self.save_sales_tax_settings(show_feedback=False):
            return

        AppMessageBox.success(
            self,
            "Saved",
            "Tax group saved successfully." if self.current_tax_group_id is None else "Tax group updated successfully.",
        )
        self.load_tax_groups()
        self.clear_form()
