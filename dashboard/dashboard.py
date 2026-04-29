from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHeaderView,QDialog, QLineEdit,QSpacerItem, QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QFileDialog, QInputDialog, QApplication, QGridLayout, QToolTip
from PySide6.QtCore import Qt, QFile, QDate, QDateTime, Signal, QTimer
from PySide6.QtGui import QColor
import sys, os
from PySide6.QtSql import QSqlDatabase
from PySide6.QtCore import QDate
from functools import partial
from medic.utilities.database import SQLiteConnectionManager
from medic.utilities.activity_logger import log_activity
from medic.utilities.permissions import Permissions
from medic.utilities.session_service import SessionErrorCode, check_active_session
from medic.services.financial_closing_service import get_month_close_prompt_state
from services import daily_session_service
from medic.reports.report_service import ReportService
import pyqtgraph as pg
from medic.features.finance.ui.daily_session import DailySession


import os
import sys
from medic.utilities.app_messagebox import AppMessageBox
from functools import lru_cache


def resource_path(relative_path):
    """Return the absolute path to a resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS  # PyInstaller extracts files here
    except AttributeError:
        base_path = os.path.abspath(".")  # running from source
    return os.path.join(base_path, relative_path)



@lru_cache(maxsize=1)
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





class ClickableLabel(QLabel):
    clicked = Signal()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class DashboardWidget(QWidget):
    
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # main vertical layout
        self.layout = QVBoxLayout(self)
        self.report_service = ReportService()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignTop)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Business Dashboard", objectName="SectionTitle")
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)

        header_layout.addStretch()

        self.dashboard_datetime = ClickableLabel("")
        self.dashboard_datetime.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.dashboard_datetime.setCursor(Qt.PointingHandCursor)
        self.dashboard_datetime.setStyleSheet("""
            QLabel {
                color: #2F5D7C;
                font-weight: 600;
                padding: 2px 4px;
                border-radius: 4px;
            }
            QLabel:hover {
                color: #1F445D;
                background-color: #E7F1F8;
                text-decoration: underline;
            }
        """)
        self.dashboard_datetime.setToolTip("Click to view previous logins")
        self.dashboard_datetime.clicked.connect(self.show_login_history_dialog)
        header_layout.addWidget(self.dashboard_datetime, 0, Qt.AlignRight)

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
        self.layout.addSpacing(10)

        

        # today_sale_label = QLabel("Today's Sale - By Hour")
        # self.layout.addWidget(today_sale_label)
        
        # # Plot widget
        # plot_widget = pg.PlotWidget()
        # self.layout.setContentsMargins(10, 10, 10, 10)  # left, top, right, bottom margins around all widgets in the layout
        # self.layout.setSpacing(10)  # space between widgets

        # plot_widget.setStyleSheet("""
        #     background-color: #f0f0f0;      /* light gray background */
        #     border: 2px solid #3498db;     /* blue border */
        # """)


        # # self.layout.addWidget(plot_widget)

        # # Get sales data and plot
        # hourly_sales = self.get_hourly_sales_data()
        # hours = list(range(24))
        # hour_sales = [hourly_sales.get(h, 0) for h in hours]
        

        # # bg = pg.BarGraphItem(x=hours, height=sales, width=0.6, brush='skyblue')
        # from datetime import datetime
        # # Create a PlotDataItem (line plot) with markers
        # plot_widget.plot(hours, hour_sales,  pen=pg.mkPen('#e74c3c', width=2), symbol='o', symbolSize=8, symbolBrush='b')
        # hour_labels = []
        # for i in range(24):
        #     if i == 0:
        #         label = "12am"
        #     elif i == 12:
        #         label = "12pm"
        #     else:
        #         label = str(i % 12)
        #     hour_labels.append((i, label))

        # plot_widget.getAxis('bottom').setTicks([hour_labels])
        # plot_widget.setXRange(0, 23)
        
        # # plot_widget.addItem(bg)

        # plot_widget.setLabel('left', 'Total Sales')
        # plot_widget.setLabel('bottom', 'Hour of Day')
        # plot_widget.setTitle("Hourly Sales Today")
        # plot_widget.setBackground("w")
        # plot_widget.showGrid(x=True, y=True)
        
        
        # #################################################
        # ####            Monthly Sales         ###########
        
        # monthly_sale_label = QLabel("Monthly Sale - By Day")
        # # self.layout.addWidget(monthly_sale_label)

        
        # days = list(range(1, 32))  # Days 1 to 31
        # monthly_sales = self.get_monthly_sales_data()
        # month_sales = [monthly_sales[day - 1] for day in range(1, 32)]
        
        # print("Days:", len(days))
        # print("Sales:", len(month_sales))

        
        # # Plot widget
        # monthly_plot = pg.PlotWidget()
        # monthly_plot.setStyleSheet("""
        #     background-color: #f0f0f0;      /* light gray background */
        #     border: 2px solid #3498db;     /* blue border */
        # """)
        
        
        # # Create a PlotDataItem (line plot) with markers
        # monthly_plot.plot(days, month_sales,  pen=pg.mkPen("#000000", width=2), symbol='o', symbolSize=8, symbolBrush='b')
        # monthly_plot.getAxis('bottom').setTicks([[(i, str(i)) for i in range(1, 32)]])
        # monthly_plot.setXRange(0, 31)

    
        # # monthly_plot.addItem(bg)

        # monthly_plot.setLabel('left', 'Daily Sales')
        # monthly_plot.setLabel('bottom', 'Day')
        # monthly_plot.setTitle("Monthly Sales")
        # monthly_plot.setBackground("w")
        # monthly_plot.showGrid(x=True, y=True)
        
        # # self.layout.addWidget(monthly_plot)
        

        # # Spacer and CSS
        # spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # self.layout.addItem(spacer)


        # QTimer.singleShot(0, self.check_session)
        
        # dialog = DailySessionDialog(mode="open", parent=self)
        # dialog.exec()

        self.backup_manager = SQLiteConnectionManager("ProcureApp")
        self.backup_check_timer = QTimer(self)
        self.backup_check_timer.setInterval(15 * 60 * 1000)
        self.backup_check_timer.timeout.connect(self.run_scheduled_backup_cycle)
        self.backup_check_timer.start()

        self.update_dashboard_datetime()
        
        
        self.add_dashboard_alerts()

        # Let the first paint complete before loading heavier dashboard work.
        QTimer.singleShot(180, self.refresh_dashboard_alerts)
        QTimer.singleShot(4000, self.run_scheduled_backup_cycle)

        # set stylesheets
        self.setStyleSheet(load_stylesheets())
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    def add_dashboard_alerts(self):
        self.alerts_container = QWidget()
        self.alerts_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        alerts_layout = QVBoxLayout(self.alerts_container)
        alerts_layout.setSpacing(12)
        alerts_layout.setContentsMargins(0, 0, 0, 0)
        alerts_layout.setAlignment(Qt.AlignTop)

        self.quick_links_card = self.build_quick_links_card()
        self.session_card = self.build_session_card()
        self.low_stock_card = self.build_low_stock_card()
        self.expiry_card = self.build_expiry_card()
        self.reminders_card = self.build_reminders_card()
        self.sales_trend_card = self.build_sales_trend_card()
        self.top_selling_card = self.build_top_selling_card()
        self.backup_card = self.build_backup_health_card()

        self._apply_dashboard_card_style(self.quick_links_card)
        self._apply_dashboard_card_style(self.session_card)
        self._apply_dashboard_card_style(self.low_stock_card)
        self._apply_dashboard_card_style(self.expiry_card)
        self._apply_dashboard_card_style(self.reminders_card)
        self._apply_dashboard_card_style(self.sales_trend_card)
        self._apply_dashboard_card_style(self.top_selling_card)
        self._apply_dashboard_card_style(self.backup_card)

        alerts_layout.addWidget(self.quick_links_card)
        alerts_layout.addWidget(self.session_card)

        operational_row = QHBoxLayout()
        operational_row.setSpacing(12)
        operational_row.addWidget(self.low_stock_card, 1)
        operational_row.addWidget(self.expiry_card, 1)
        operational_row.addWidget(self.reminders_card, 1)
        alerts_layout.addLayout(operational_row)

        sales_snapshot_row = QHBoxLayout()
        sales_snapshot_row.setSpacing(12)
        sales_snapshot_row.addWidget(self.sales_trend_card, 2)
        sales_snapshot_row.addWidget(self.top_selling_card, 1)
        alerts_layout.addLayout(sales_snapshot_row)

        alerts_layout.addSpacing(10)
        alerts_layout.addWidget(self.backup_card)

        self.layout.addWidget(self.alerts_container, 0, Qt.AlignTop)

    def build_quick_links_card(self):
        card = QFrame()
        card.setObjectName("sectionCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Quick Links")
        title.setObjectName("SectionTitle")
        title_hint = QLabel("Jump into common sales and purchase actions")
        title_hint.setStyleSheet("color:#777; padding-left: 0;")

        header.addWidget(title)
        header.addSpacing(8)
        header.addWidget(title_hint)
        header.addStretch()
        layout.addLayout(header)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        helper_text = QLabel(
            "Use these shortcuts to start a new sales or purchase invoice, or review only today's sales for the active session."
        )
        helper_text.setWordWrap(True)
        helper_text.setStyleSheet("color:#5A7183; padding-left: 0;")
        action_row.addWidget(helper_text, 1)

        self.quick_create_sale_btn = QPushButton("Create Sale")
        self.quick_create_sale_btn.setCursor(Qt.PointingHandCursor)
        self.quick_create_sale_btn.setObjectName("TopRightButton")
        self.quick_create_sale_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.quick_create_sale_btn.clicked.connect(self.open_create_sale_page)
        action_row.addWidget(self.quick_create_sale_btn)

        self.quick_today_sales_btn = QPushButton("Show Today Sales")
        self.quick_today_sales_btn.setCursor(Qt.PointingHandCursor)
        self.quick_today_sales_btn.setObjectName("TopRightButton")
        self.quick_today_sales_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.quick_today_sales_btn.clicked.connect(self.show_today_sales_dialog)
        action_row.addWidget(self.quick_today_sales_btn)

        self.quick_create_purchase_btn = QPushButton("Purchase Invoice")
        self.quick_create_purchase_btn.setCursor(Qt.PointingHandCursor)
        self.quick_create_purchase_btn.setObjectName("TopRightButton")
        self.quick_create_purchase_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.quick_create_purchase_btn.clicked.connect(self.open_create_purchase_page)
        action_row.addWidget(self.quick_create_purchase_btn)

        layout.addLayout(action_row)
        return card

    def _apply_dashboard_card_style(self, card, min_height=0):
        if min_height > 0:
            card.setMinimumHeight(min_height)
        else:
            card.setMinimumHeight(0)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        card.setStyleSheet(
            """
            QFrame#sectionCard {
                background: #E8EEF3;
                border: 1px solid #D6E0E8;
                border-top: 2px solid #3E6B89;
                border-radius: 8px;
            }
            QLabel {
                color: #314757;
            }
            QLabel#SectionTitle {
                color: #223746;
            }
            """
        )

    def _format_sold_units(self, total_qty, pack_size):
        try:
            qty = int(float(total_qty or 0.0))
        except Exception:
            qty = 0
        try:
            normalized_pack_size = int(float(pack_size or 0.0))
        except Exception:
            normalized_pack_size = 0

        if normalized_pack_size <= 1:
            return f"0p {qty}s"

        packs = qty // normalized_pack_size
        singles = qty % normalized_pack_size
        return f"{packs}p {singles}s"

    def _build_sold_units_label(self, total_qty, pack_size, emphasized=False):
        label = QLabel()
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setTextFormat(Qt.RichText)

        try:
            qty = int(float(total_qty or 0.0))
        except Exception:
            qty = 0
        try:
            normalized_pack_size = int(float(pack_size or 0.0))
        except Exception:
            normalized_pack_size = 0

        if normalized_pack_size <= 1:
            packs = 0
            singles = qty
        else:
            packs = qty // normalized_pack_size
            singles = qty % normalized_pack_size

        pack_color = "#244F70" if emphasized else "#2F5D7C"
        single_color = "#738896" if emphasized else "#8AA0AD"
        label.setText(
            f"<span style='font-weight:700; color:{pack_color};'>{packs}p</span> "
            f"<span style='font-weight:600; color:{single_color};'>{singles}s</span>"
        )
        return label

    def dialog_section_style(self, section):
        if section == "header":
            return "background-color: #EEF4F7; border: 1px solid #D7E2E8; border-radius: 10px;"
        if section == "footer":
            return "background-color: #F4F8FB; border: 1px solid #D7E2E8; border-radius: 10px;"
        return "background-color: #FFFFFF; border: 1px solid #D7E2E8; border-radius: 10px;"

    def build_report_dialog_shell(self, dialog):
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

    def open_create_sale_page(self):
        main_window = self.window()
        if main_window is None or not hasattr(main_window, "set_sales"):
            AppMessageBox.warning(self, "Navigation Unavailable", "Could not open the Sales page from the dashboard.")
            return

        main_window.set_sales(main_window.base_sales, main_window.main_content_layout)
        if hasattr(main_window.base_sales, "set_createsales_widget"):
            main_window.base_sales.set_createsales_widget()

    def open_create_purchase_page(self):
        main_window = self.window()
        if main_window is None or not hasattr(main_window, "set_purchase"):
            AppMessageBox.warning(self, "Navigation Unavailable", "Could not open the Purchase page from the dashboard.")
            return

        main_window.set_purchase(main_window.purchase, main_window.main_content_layout)
        if hasattr(main_window.purchase, "set_addpurchase_widget"):
            main_window.purchase.set_addpurchase_widget()

    def open_financial_close_page(self):
        main_window = self.window()
        if main_window is None or not hasattr(main_window, "set_financial_close"):
            AppMessageBox.warning(self, "Navigation Unavailable", "Could not open Financial Closing from the dashboard.")
            return

        main_window.set_financial_close(None, main_window.main_content_layout)
        if hasattr(main_window, "financial_close") and hasattr(main_window.financial_close, "set_financial_close_create_widget"):
            main_window.financial_close.set_financial_close_create_widget()

    def get_today_session_sales_rows(self, session_id):
        return self.report_service.get_today_session_sales_rows(session_id)

    def get_today_session_sales_return_rows(self, session_id):
        return self.report_service.get_today_session_sales_return_rows(session_id)

    def show_today_sales_dialog(self):
        session_result = check_active_session(strict=True)
        if not session_result.ok or session_result.session_id is None:
            if session_result.code == SessionErrorCode.NO_OPEN_SESSION:
                AppMessageBox.information(
                    self,
                    "No Active Session",
                    "There is no active daily session right now. Open the day first to review today's session sales.",
                )
                return
            self._show_session_state_error(session_result, action_label="review today's sales")
            return

        session = self.get_open_session()
        session_id = int(session_result.session_id)
        session_date = session.get("session_date", "") if session else ""

        dialog = QDialog(self)
        dialog.setWindowTitle("Today's Session Sales")
        dialog.resize(1080, 640)

        header_layout, content_layout, footer_layout = self.build_report_dialog_shell(dialog)

        heading = QLabel("Today's Session Sales")
        heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #223746;")
        subtitle = QLabel(
            f"Sales recorded for the current daily session only. Session ID: {session_id}"
            + (f" | Session Date: {session_date}" if session_date else "")
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12px; color: #5A7183; padding-left: 0;")
        header_layout.addWidget(heading)
        header_layout.addWidget(subtitle)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(10)

        def make_metric_card(title_text, value_text):
            card = QFrame()
            card.setObjectName("card")
            card.setStyleSheet(
                """
                QFrame#card {
                    background-color: #E8EEF3;
                    border: 1px solid #D3DDE6;
                    border-radius: 8px;
                    color: #223746;
                }
                """
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(4)

            title_label = QLabel(title_text)
            title_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #5A7183; padding-left: 0;")
            value_label = QLabel(value_text)
            value_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #223746; padding-left: 0;")
            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            return card, value_label

        count_card, self.today_sales_count_value = make_metric_card("Invoices", "0")
        total_card, self.today_sales_total_value = make_metric_card("Sales", "0.00")
        returns_card, self.today_sales_returns_value = make_metric_card("Returns", "0.00")
        net_card, self.today_sales_net_value = make_metric_card("Net Sales", "0.00")

        summary_row.addWidget(count_card, 1)
        summary_row.addWidget(total_card, 1)
        summary_row.addWidget(returns_card, 1)
        summary_row.addWidget(net_card, 1)
        content_layout.addLayout(summary_row)

        note_label = QLabel("Only sales and sales returns created today and tied to the currently open daily session are shown below.")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("font-size: 11px; color: #5A7183; padding-left: 0;")
        content_layout.addWidget(note_label)

        sales_title = QLabel("Sales")
        sales_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #223746; padding-left: 0;")
        content_layout.addWidget(sales_title)

        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Sale ID", "Created At", "Customer", "Salesman", "Total", "Remaining", "Write-off"
        ])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        content_layout.addWidget(table, 1)

        returns_title = QLabel("Sales Returns")
        returns_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #223746; padding-left: 0;")
        content_layout.addWidget(returns_title)

        returns_table = QTableWidget()
        returns_table.setColumnCount(7)
        returns_table.setHorizontalHeaderLabels([
            "Return ID", "Sale ID", "Created At", "Customer", "Salesman", "Total", "Remaining"
        ])
        returns_table.verticalHeader().setVisible(False)
        returns_table.setEditTriggers(QTableWidget.NoEditTriggers)
        returns_table.setSelectionBehavior(QTableWidget.SelectRows)
        returns_table.setAlternatingRowColors(True)
        returns_table.horizontalHeader().setStretchLastSection(False)
        returns_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        returns_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        returns_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        returns_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        returns_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        returns_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        returns_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        returns_table.setMaximumHeight(220)
        content_layout.addWidget(returns_table)

        footer_status = QLabel("")
        footer_status.setStyleSheet("font-size: 11px; font-weight: 600; color: #5A7183; padding-left: 0;")
        footer_layout.addWidget(footer_status)
        footer_layout.addStretch()

        reload_btn = QPushButton("Reload")
        reload_btn.setObjectName("TopRightButton")
        reload_btn.setCursor(Qt.PointingHandCursor)
        open_sales_btn = QPushButton("Create Sale")
        open_sales_btn.setObjectName("TopRightButton")
        open_sales_btn.setCursor(Qt.PointingHandCursor)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("TopRightButton")
        close_btn.setCursor(Qt.PointingHandCursor)
        footer_layout.addWidget(reload_btn)
        footer_layout.addWidget(open_sales_btn)
        footer_layout.addWidget(close_btn)

        def load_rows():
            rows = self.get_today_session_sales_rows(session_id)
            return_rows = self.get_today_session_sales_return_rows(session_id)
            table.setRowCount(len(rows))
            returns_table.setRowCount(len(return_rows))

            total_sales = 0.0
            total_returns = 0.0

            for row_index, row in enumerate(rows):
                total_sales += float(row.get("total", 0.0) or 0.0)

                created_at = str(row.get("creation_date", "") or "")
                created_dt = QDateTime.fromString(created_at, "yyyy-MM-dd HH:mm:ss")
                if not created_dt.isValid():
                    created_dt = QDateTime.fromString(created_at, Qt.ISODate)
                if created_dt.isValid():
                    if created_dt.timeSpec() == Qt.LocalTime:
                        created_dt.setTimeSpec(Qt.UTC)
                    created_at = created_dt.toLocalTime().toString("dd MMM yyyy | hh:mm AP")

                writeoff_amount = float(row.get("writeoff", 0.0) or 0.0)
                remaining_amount = float(row.get("remaining", 0.0) or 0.0)
                if writeoff_amount > 0:
                    writeoff_status = "Clear"
                elif remaining_amount > 0:
                    writeoff_status = "Not Clear"
                else:
                    writeoff_status = "N/A"

                values = [
                    str(row.get("sale_id", "")),
                    created_at,
                    str(row.get("customer_name", "")),
                    str(row.get("salesman_name", "")),
                    f"{float(row.get('total', 0.0) or 0.0):,.2f}",
                    f"{remaining_amount:,.2f}",
                    writeoff_status,
                ]

                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if col in {4, 5}:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if col == 6:
                        if writeoff_status == "Clear":
                            item.setForeground(QColor("#2E7D32"))
                        elif writeoff_status == "Not Clear":
                            item.setForeground(QColor("#B45309"))
                    table.setItem(row_index, col, item)

            for row_index, row in enumerate(return_rows):
                total_returns += float(row.get("total", 0.0) or 0.0)

                created_at = str(row.get("creation_date", "") or "")
                created_dt = QDateTime.fromString(created_at, "yyyy-MM-dd HH:mm:ss")
                if not created_dt.isValid():
                    created_dt = QDateTime.fromString(created_at, Qt.ISODate)
                if created_dt.isValid():
                    if created_dt.timeSpec() == Qt.LocalTime:
                        created_dt.setTimeSpec(Qt.UTC)
                    created_at = created_dt.toLocalTime().toString("dd MMM yyyy | hh:mm AP")

                values = [
                    str(row.get("return_id", "")),
                    str(row.get("salesorder_id", "")),
                    created_at,
                    str(row.get("customer_name", "")),
                    str(row.get("salesman_name", "")),
                    f"{float(row.get('total', 0.0) or 0.0):,.2f}",
                    f"{float(row.get('remaining', 0.0) or 0.0):,.2f}",
                ]

                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if col in {5, 6}:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    returns_table.setItem(row_index, col, item)

            self.today_sales_count_value.setText(str(len(rows)))
            self.today_sales_total_value.setText(f"{total_sales:,.2f}")
            self.today_sales_returns_value.setText(f"{total_returns:,.2f}")
            self.today_sales_net_value.setText(f"{(total_sales - total_returns):,.2f}")
            footer_status.setText(
                f"Sales shown: {len(rows)} | Returns shown: {len(return_rows)} | Session ID: {session_id}"
                + (f" | Session Date: {session_date}" if session_date else "")
            )

        reload_btn.clicked.connect(load_rows)
        open_sales_btn.clicked.connect(lambda: (dialog.accept(), self.open_create_sale_page()))
        close_btn.clicked.connect(dialog.accept)

        load_rows()
        dialog.exec()

    def update_dashboard_datetime(self):
        app = QApplication.instance()
        username = (app.property("username") or "") if app else ""
        last_login_text = self.report_service.get_latest_login_timestamp(username)

        if last_login_text:
            login_dt = QDateTime.fromString(last_login_text, "yyyy-MM-dd HH:mm:ss")
            if not login_dt.isValid():
                login_dt = QDateTime.fromString(last_login_text, Qt.ISODate)

            if login_dt.isValid():
                if login_dt.timeSpec() == Qt.LocalTime:
                    login_dt.setTimeSpec(Qt.UTC)
                login_dt = login_dt.toLocalTime()
                formatted = login_dt.toString("ddd, dd MMM yyyy | hh:mm AP")
            else:
                formatted = last_login_text
            self.dashboard_datetime.setText(f"Login Time: {formatted}")
        else:
            self.dashboard_datetime.setText("Login Time: Not available")

    def show_login_history_dialog(self):
        app = QApplication.instance()
        username = (app.property("username") or "") if app else ""
        if not username:
            AppMessageBox.information(self, "Login History", "User context is not available.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Previous Logins")
        dialog.setMinimumSize(760, 520)
        dialog.setStyleSheet("""
            QDialog { background: #EEF4F8; }
            QFrame#loginHistoryHeader {
                background-color: #325D7B;
                border: 1px solid #284B63;
                border-radius: 8px;
            }
            QFrame#loginHistoryContent, QFrame#loginHistoryFooter {
                background: #FFFFFF;
                border: 1px solid #D3DEE7;
                border-radius: 8px;
            }
        """)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        header_frame = QFrame()
        header_frame.setObjectName("loginHistoryHeader")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(4)

        title = QLabel("Previous Logins")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        header_layout.addWidget(title)

        subtitle = QLabel("Login history for the current user. Default view shows the last week.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 11px; color: #DDEAF3;")
        header_layout.addWidget(subtitle)
        root.addWidget(header_frame)

        content_frame = QFrame()
        content_frame.setObjectName("loginHistoryContent")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(14, 12, 14, 12)
        content_layout.setSpacing(8)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        filter_row.addWidget(QLabel("Period"))

        period_combo = QComboBox()
        period_combo.addItem("Today", "today")
        period_combo.addItem("Last Week", "week")
        period_combo.addItem("Last Month", "month")
        period_combo.addItem("All", "all")
        period_combo.setCurrentIndex(period_combo.findData("week"))
        filter_row.addWidget(period_combo)
        filter_row.addStretch()

        reload_btn = QPushButton("Reload", objectName="TopRightButton")
        filter_row.addWidget(reload_btn)
        content_layout.addLayout(filter_row)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Login Date", "Login Time", "Logout Time", "Duration", "Daily Session"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        content_layout.addWidget(table)

        summary_label = QLabel("Rows: 0")
        summary_label.setStyleSheet("font-weight: 600; color: #223746;")
        content_layout.addWidget(summary_label)
        root.addWidget(content_frame)

        footer_frame = QFrame()
        footer_frame.setObjectName("loginHistoryFooter")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(14, 10, 14, 10)
        footer_layout.setSpacing(8)
        footer_layout.addStretch()

        close_btn = QPushButton("Close", objectName="TopRightButton")
        close_btn.clicked.connect(dialog.accept)
        footer_layout.addWidget(close_btn)
        root.addWidget(footer_frame)

        def load_rows():
            period_key = period_combo.currentData()
            rows = self.report_service.get_login_history_rows(username, period=period_key, limit=500)

            table.setRowCount(len(rows))
            for row_index, row in enumerate(rows):
                values = [
                    row["login_date"],
                    row["login_time"],
                    row["logout_time"],
                    row["duration"],
                    row["daily_session_label"],
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    table.setItem(row_index, col, item)

            summary_label.setText(f"Rows: {len(rows)} | User: {username} | Period: {period_combo.currentText()}")

        reload_btn.clicked.connect(load_rows)
        period_combo.currentIndexChanged.connect(lambda _: load_rows())
        load_rows()
        dialog.exec()

    def build_session_card(self):
        card = QFrame()
        card.setObjectName("sectionCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Daily Session")
        title.setObjectName("SectionTitle")

        self.session_status_badge = QLabel("UNKNOWN")
        self.session_status_badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.session_status_badge.setStyleSheet("font-weight:bold; color:#ef6c00;")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.session_status_badge)
        layout.addLayout(header)

        meta_row = QHBoxLayout()
        self.session_meta = QLabel("Session status not loaded yet")
        self.session_meta.setStyleSheet("color:#777; padding-left: 0;")
        meta_row.addWidget(self.session_meta)
        meta_row.addStretch()

        self.open_day_btn = QPushButton("Open Day")
        self.open_day_btn.setCursor(Qt.PointingHandCursor)
        self.open_day_btn.setObjectName("TopRightButton")
        self.open_day_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.open_day_btn.clicked.connect(self.handle_open_session)
        meta_row.addWidget(self.open_day_btn)

        self.close_day_btn = QPushButton("Close Day")
        self.close_day_btn.setCursor(Qt.PointingHandCursor)
        self.close_day_btn.setObjectName("TopRightButton")
        self.close_day_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.close_day_btn.clicked.connect(self.handle_close_session)
        meta_row.addWidget(self.close_day_btn)

        self.session_history_btn = QPushButton("History")
        self.session_history_btn.setCursor(Qt.PointingHandCursor)
        self.session_history_btn.setObjectName("TopRightButton")
        self.session_history_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        meta_row.addWidget(self.session_history_btn)

        layout.addLayout(meta_row)

        self.month_close_reminder_wrap = QFrame()
        self.month_close_reminder_wrap.setStyleSheet(
            """
            QFrame {
                background-color: #FFF6E8;
                border: 1px solid #E5C16F;
                border-radius: 8px;
            }
            """
        )
        reminder_row = QHBoxLayout(self.month_close_reminder_wrap)
        reminder_row.setContentsMargins(10, 8, 10, 8)
        reminder_row.setSpacing(10)
        self.month_close_reminder_label = QLabel("")
        self.month_close_reminder_label.setWordWrap(True)
        self.month_close_reminder_label.setStyleSheet("color:#7E5A10; font-weight:700; padding-left: 0;")
        reminder_row.addWidget(self.month_close_reminder_label, 1)
        self.month_close_reminder_btn = QPushButton("Close Month")
        self.month_close_reminder_btn.setCursor(Qt.PointingHandCursor)
        self.month_close_reminder_btn.setObjectName("TopRightButton")
        self.month_close_reminder_btn.clicked.connect(self.open_financial_close_page)
        reminder_row.addWidget(self.month_close_reminder_btn)
        self.month_close_reminder_wrap.hide()
        layout.addWidget(self.month_close_reminder_wrap)
        return card


    def build_backup_health_card(self):

        card = QFrame()
        card.setObjectName("sectionCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Backup Health")
        title.setObjectName("SectionTitle")

        self.backup_status_badge = QLabel("UNKNOWN")
        self.backup_status_badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.backup_status_badge.setStyleSheet("font-weight:bold; color:#ef6c00;")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.backup_status_badge)
        layout.addLayout(header)

        info_row = QHBoxLayout()
        self.backup_meta = QLabel("Backup status not loaded yet")
        self.backup_meta.setStyleSheet("color:#777; padding-left: 0;")
        info_row.addWidget(self.backup_meta)
        info_row.addStretch()

        self.backup_now_btn = QPushButton("Backup Now")
        self.backup_now_btn.setCursor(Qt.PointingHandCursor)
        self.backup_now_btn.setObjectName("SaveButton")
        self.backup_now_btn.clicked.connect(self.run_manual_backup)
        info_row.addWidget(self.backup_now_btn)

        self.backup_view_btn = QPushButton("View Status")
        self.backup_view_btn.setCursor(Qt.PointingHandCursor)
        self.backup_view_btn.setObjectName("SaveButton")
        self.backup_view_btn.clicked.connect(self.show_backup_status_dialog)
        info_row.addWidget(self.backup_view_btn)

        layout.addLayout(info_row)
        return card

    def build_sales_trend_card(self):
        card = QFrame()
        card.setObjectName("sectionCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Sales Overview")
        title.setObjectName("SectionTitle")
        self.sales_snapshot_range_combo = QComboBox()
        self.sales_snapshot_range_combo.addItem("Last 7 days", 7)
        self.sales_snapshot_range_combo.addItem("Last 30 days", 30)
        self.sales_snapshot_range_combo.addItem("Last 60 days", 60)
        self.sales_snapshot_range_combo.addItem("Last 90 days", 90)
        self.sales_snapshot_range_combo.setCurrentIndex(0)
        self.sales_snapshot_range_combo.setCursor(Qt.PointingHandCursor)
        self.sales_snapshot_range_combo.currentIndexChanged.connect(self.load_sales_snapshot_data)
        self.sales_trend_meta = QLabel("Last 7 days")
        self.sales_trend_meta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sales_trend_meta.setStyleSheet("color:#777; padding-left: 0;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.sales_snapshot_range_combo)
        header.addSpacing(8)
        header.addWidget(self.sales_trend_meta)
        layout.addLayout(header)

        self.sales_trend_plot = pg.PlotWidget()
        self.sales_trend_plot.setStyleSheet(
            """
            QToolTip {
                background-color: #183B56;
                color: #F8FBFD;
                border: 1px solid #2A5B7D;
                border-radius: 2px;
                padding: 6px 8px;
                font-weight: 600;
            }
            """
        )
        self.sales_trend_plot.setBackground("#F8FBFD")
        self.sales_trend_plot.setMinimumHeight(230)
        self.sales_trend_plot.showGrid(x=False, y=True, alpha=0.18)
        self.sales_trend_plot.setMenuEnabled(False)
        self.sales_trend_plot.setMouseEnabled(x=False, y=False)
        self.sales_trend_plot.hideButtons()
        self.sales_trend_plot.getPlotItem().setContentsMargins(6, 6, 12, 6)
        self.sales_trend_plot.getAxis("left").setTextPen(pg.mkPen("#607D8B"))
        self.sales_trend_plot.getAxis("bottom").setTextPen(pg.mkPen("#607D8B"))
        self.sales_trend_plot.getAxis("left").setPen(pg.mkPen("#C9D6DF"))
        self.sales_trend_plot.getAxis("bottom").setPen(pg.mkPen("#C9D6DF"))
        self.sales_trend_plot.getPlotItem().hideAxis("top")
        self.sales_trend_plot.getPlotItem().hideAxis("right")
        self.sales_trend_points = []
        self.sales_trend_scatter = None
        layout.addWidget(self.sales_trend_plot)

        return card

    def build_top_selling_card(self):
        card = QFrame()
        card.setObjectName("sectionCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Top Selling Items")
        title.setObjectName("SectionTitle")
        self.top_selling_meta = QLabel("Last 30 days")
        self.top_selling_meta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.top_selling_meta.setStyleSheet("color:#777; padding-left: 0;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.top_selling_meta)
        layout.addLayout(header)

        self.top_selling_table = QTableWidget(0, 3)
        self.top_selling_table.setHorizontalHeaderLabels(["Item Name", "Sold", "Sales (PKR)"])
        self.top_selling_table.verticalHeader().setVisible(False)
        self.top_selling_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.top_selling_table.setSelectionMode(QTableWidget.NoSelection)
        self.top_selling_table.setFocusPolicy(Qt.NoFocus)
        self.top_selling_table.setAlternatingRowColors(True)
        self.top_selling_table.setShowGrid(False)
        self.top_selling_table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.top_selling_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #F8FBFD;
                alternate-background-color: #F1F6FA;
                border: 1px solid #D9E5EC;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #EAF2F7;
                color: #36566C;
                font-weight: 700;
                border: none;
                border-bottom: 1px solid #D4E0E8;
                padding: 6px 8px;
            }
            """
        )
        self.top_selling_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.top_selling_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.top_selling_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.top_selling_table.verticalHeader().setDefaultSectionSize(34)
        self.top_selling_table.setMinimumHeight(230)
        layout.addWidget(self.top_selling_table)

        return card


    def build_reminders_card(self):

        card = QFrame()
        card.setObjectName("sectionCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()

        title = QLabel("Reminder Queue")
        title.setObjectName("SectionTitle")

        self.reminder_count = QLabel("0")
        self.reminder_count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.reminder_count)

        layout.addLayout(header)

        info_row = QHBoxLayout()
        self.reminder_meta = QLabel("Payments + stock reminders")
        self.reminder_meta.setStyleSheet("color:#777; padding-left: 0;")
        info_row.addWidget(self.reminder_meta)
        info_row.addStretch()

        self.reminder_open_btn = QPushButton("Open Queue")
        self.reminder_open_btn.setCursor(Qt.PointingHandCursor)
        self.reminder_open_btn.setObjectName("SaveButton")
        self.reminder_open_btn.clicked.connect(self.show_reminder_queue_dialog)
        info_row.addWidget(self.reminder_open_btn)

        layout.addLayout(info_row)

        return card

        
    def build_low_stock_card(self):
    
        card = QFrame()
        card.setObjectName("sectionCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # header
        header = QHBoxLayout()

        title = QLabel("Low Stock")
        title.setObjectName("SectionTitle")

        self.low_stock_count = QLabel("0")
        self.low_stock_count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.low_stock_count)

        layout.addLayout(header)

        info_row = QHBoxLayout()
        self.low_stock_meta = QLabel("No low-stock alerts")
        self.low_stock_meta.setStyleSheet("color:#777; padding-left: 0;")
        info_row.addWidget(self.low_stock_meta)
        info_row.addStretch()

        self.low_stock_open_btn = QPushButton("Open Queue")
        self.low_stock_open_btn.setCursor(Qt.PointingHandCursor)
        self.low_stock_open_btn.setObjectName("SaveButton")
        self.low_stock_open_btn.clicked.connect(self.show_low_stock_queue_dialog)
        info_row.addWidget(self.low_stock_open_btn)

        layout.addLayout(info_row)

        return card

    
    
    def build_expiry_card(self):
    
        card = QFrame()
        card.setObjectName("sectionCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # header
        header = QHBoxLayout()

        title = QLabel("Expiry Alerts")
        title.setObjectName("SectionTitle")

        self.expiry_count = QLabel("0")
        self.expiry_count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.expiry_count)

        layout.addLayout(header)

        info_row = QHBoxLayout()
        self.expiry_meta = QLabel("No expiry alerts")
        self.expiry_meta.setStyleSheet("color:#777; padding-left: 0;")
        info_row.addWidget(self.expiry_meta)
        info_row.addStretch()

        self.expiry_open_btn = QPushButton("Open Queue")
        self.expiry_open_btn.setCursor(Qt.PointingHandCursor)
        self.expiry_open_btn.setObjectName("SaveButton")
        self.expiry_open_btn.clicked.connect(self.show_expiry_queue_dialog)
        info_row.addWidget(self.expiry_open_btn)

        layout.addLayout(info_row)

        return card
        
        
    def load_inventory_alerts(self):
        self.update_session_status_card()
        self.load_backup_health_summary()
        self.load_reminder_summary()
        self.load_low_stock_data()
        self.load_expiry_data()
        self.load_sales_snapshot_data()

    def refresh_dashboard_alerts(self):
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            return
        self.load_inventory_alerts()
        self.update_month_close_reminder()

    def update_month_close_reminder(self):
        if not hasattr(self, "month_close_reminder_wrap"):
            return

        state = get_month_close_prompt_state()
        if not state.get("show"):
            self.month_close_reminder_wrap.hide()
            return

        self.month_close_reminder_label.setText(str(state.get("message") or ""))
        self.month_close_reminder_wrap.show()

    def prompt_month_close_if_needed(self):
        state = get_month_close_prompt_state()
        if not state.get("show"):
            return

        answer = AppMessageBox.question(
            self,
            "Month Close Reminder",
            str(state.get("message") or ""),
        )
        if answer == QMessageBox.Yes:
            self.open_financial_close_page()

    def _show_session_state_error(self, result, action_label="continue"):
        return DailySession._show_session_state_error(self, result, action_label)

    def _get_strict_active_session_id(self, action_label="continue"):
        return DailySession._get_strict_active_session_id(self, action_label)

    def get_open_session(self):
        active_session_id = self._get_strict_active_session_id(action_label="view session details")
        if active_session_id is None:
            return None
        return daily_session_service.get_open_session(session_id=active_session_id)

    def open_session_dialog(self):
        return DailySession.open_session_dialog(self)

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
        return DailySession.close_session_dialog(self, session_data)

    def get_opening_cash(self):
        active_session_id = self._get_strict_active_session_id(action_label="close the session")
        if active_session_id is None:
            return 0.0
        return daily_session_service.get_opening_cash(session_id=active_session_id)

    def get_current_session_cash_flows(self):
        active_session_id = self._get_strict_active_session_id(action_label="close the session")
        if active_session_id is None:
            return None, 0.0, 0.0
        return daily_session_service.get_current_session_cash_flows(session_id=active_session_id)

    def update_session_status_card(self):
        result = check_active_session(strict=True)

        self.open_day_btn.show()
        self.close_day_btn.hide()

        if result.ok:
            session = self.get_open_session()
            self.session_status_badge.setText("OPEN")
            self.session_status_badge.setStyleSheet("font-weight:bold; color:#2e7d32;")
            if session:
                self.session_meta.setText(
                    f"Opened {session.get('session_date', '')} | Opening cash: {float(session.get('opening_cash') or 0):.2f}"
                )
            else:
                self.session_meta.setText("An active session is open.")
            self.open_day_btn.hide()
            self.close_day_btn.show()
            return

        if result.code == SessionErrorCode.NO_OPEN_SESSION:
            self.session_status_badge.setText("CLOSED")
            self.session_status_badge.setStyleSheet("font-weight:bold; color:#ef6c00;")
            self.session_meta.setText("No active session. Open the day before creating transactions.")
            return

        if result.code == SessionErrorCode.MULTIPLE_OPEN_SESSIONS:
            self.session_status_badge.setText("ERROR")
            self.session_status_badge.setStyleSheet("font-weight:bold; color:#b71c1c;")
            self.session_meta.setText("Multiple open sessions detected. Fix session data before continuing.")
            self.open_day_btn.hide()
            self.close_day_btn.hide()
            return

        self.session_status_badge.setText("WARN")
        self.session_status_badge.setStyleSheet("font-weight:bold; color:#ef6c00;")
        self.session_meta.setText("Session status unavailable.")
        self.open_day_btn.hide()
        self.close_day_btn.hide()

    @Permissions.require_permission('dashboard')
    def handle_open_session(self):
        active_session = check_active_session(strict=True)
        if active_session.ok:
            AppMessageBox.information(self, "Session Already Open", "A daily session is already open.")
            self.update_session_status_card()
            return

        if active_session.code not in {SessionErrorCode.NO_OPEN_SESSION}:
            self._show_session_state_error(active_session, action_label="open a new session")
            self.update_session_status_card()
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
            AppMessageBox.critical(self, "Database Error", f"Could not open daily session.\n\n{exc}")
            return

        self.refresh_dashboard_alerts()

    @Permissions.require_permission('dashboard')
    def handle_close_session(self):
        session = self.get_open_session()
        if not session:
            AppMessageBox.warning(self, "No Active Session", "There is no active daily session to close.")
            self.update_session_status_card()
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
            AppMessageBox.critical(self, "Database Error", f"Could not close daily session.\n\n{exc}")
            return

        self.refresh_dashboard_alerts()
        self.prompt_month_close_if_needed()


    def run_scheduled_backup_cycle(self):
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            return

        try:
            self.backup_manager.run_scheduled_backup(interval_hours=24, keep_last=14)
        except Exception as exc:
            print("Scheduled backup failed:", str(exc))

        self.load_backup_health_summary()


    def run_manual_backup(self):
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            return

        try:
            backup_file = self.backup_manager.backup(trigger_source="manual")
            self.backup_manager.prune_backup_files(keep_last=14)
            log_activity(
                category="system",
                action="backup_created",
                entity_type="backup",
                entity_id=None,
                note=f"Manual backup created at {backup_file}",
            )
        except Exception as exc:
            print("Manual backup failed:", str(exc))
            log_activity(
                category="system",
                action="backup_failed",
                entity_type="backup",
                entity_id=None,
                note=f"Manual backup failed: {str(exc)}",
            )

        self.load_backup_health_summary()


    def verify_admin_password(self):
        user_id = QApplication.instance().property("user_id")

        if not Permissions.has_permission("system.backup.external") or user_id is None:
            AppMessageBox.warning(self, "Admin Required", "Only admin can run Backup To external location.")
            return False

        password, ok = QInputDialog.getText(
            self,
            "Admin Confirmation",
            "Enter admin password to continue:",
            QLineEdit.Password,
        )
        if not ok:
            return False

        verification = self.report_service.verify_active_admin_password(user_id, password)
        if not verification.get("ok"):
            AppMessageBox.warning(self, "Verification Failed", str(verification.get("error") or "Admin verification failed."))
            return False

        return True


    def run_manual_backup_to_location(self):
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            return

        if not self.verify_admin_password():
            return

        target_dir = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if not target_dir:
            return

        try:
            backup_file = self.backup_manager.backup(backup_dir=target_dir, trigger_source="manual-custom")
            log_activity(
                category="system",
                action="backup_created_external",
                entity_type="backup",
                entity_id=None,
                note=f"Manual backup created to custom location: {backup_file}",
            )
            AppMessageBox.information(self, "Backup Completed", f"Backup saved to:\n{backup_file}")
        except Exception as exc:
            log_activity(
                category="system",
                action="backup_failed_external",
                entity_type="backup",
                entity_id=None,
                note=f"External backup failed: {str(exc)}",
            )
            AppMessageBox.critical(self, "Backup Failed", str(exc))

        self.load_backup_health_summary()


    def load_backup_health_summary(self):
        health = self.report_service.get_backup_health_view_model(self.backup_manager, stale_after_hours=30)
        self.backup_status_badge.setText(str(health.get("badge_text", "WARN")))
        self.backup_status_badge.setStyleSheet(f"font-weight:bold; color:{health.get('badge_color', '#ef6c00')};")
        self.backup_meta.setText(str(health.get("summary_text", "")))


    def show_backup_status_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Backup Status")
        dialog.resize(1080, 640)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        health = self.report_service.get_backup_health_view_model(self.backup_manager, stale_after_hours=30)
        top_row.addWidget(QLabel(str(health.get("status_text", ""))))
        top_row.addStretch()
        backup_now_btn = QPushButton("Backup Now")
        backup_to_btn = QPushButton("Backup To...")
        validate_btn = QPushButton("Validate Selected")
        restore_btn = QPushButton("Restore Selected")
        reload_btn = QPushButton("Reload", objectName="TopRightButton")
        top_row.addWidget(backup_now_btn)
        top_row.addWidget(backup_to_btn)
        top_row.addWidget(validate_btn)
        top_row.addWidget(restore_btn)
        top_row.addWidget(reload_btn)
        layout.addLayout(top_row)

        status_note = QLabel("Select a backup row, validate it, then restore if needed. Restore creates a safety pre-restore backup automatically.")
        status_note.setStyleSheet("color:#666;")
        layout.addWidget(status_note)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Run At", "Status", "Trigger", "File", "Size (KB)", "Message"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        layout.addWidget(table)

        restore_log_title = QLabel("Restore History")
        restore_log_title.setStyleSheet("font-weight:bold;")
        layout.addWidget(restore_log_title)

        restore_table = QTableWidget()
        restore_table.setColumnCount(4)
        restore_table.setHorizontalHeaderLabels(["Run At", "Status", "Backup File", "Message"])
        restore_table.verticalHeader().setVisible(False)
        restore_table.setEditTriggers(QTableWidget.NoEditTriggers)
        restore_table.setSelectionBehavior(QTableWidget.SelectRows)
        restore_table.setAlternatingRowColors(True)
        restore_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        restore_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        restore_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        restore_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        restore_table.setMaximumHeight(180)
        layout.addWidget(restore_table)

        footer_label = QLabel("")
        footer_label.setStyleSheet("font-weight:bold;")
        layout.addWidget(footer_label)

        def selected_backup_file():
            row = table.currentRow()
            if row < 0:
                return ""
            file_item = table.item(row, 3)
            if not file_item:
                return ""
            return str(file_item.text() or "").strip()

        def load_log_rows():
            rows = self.report_service.get_backup_run_log_rows(self.backup_manager, limit=100)

            table.setRowCount(len(rows))
            for r, row_data in enumerate(rows):
                values = [
                    str(row_data.get("run_at", "")),
                    str(row_data.get("status", "")),
                    str(row_data.get("trigger_source", "")),
                    str(row_data.get("backup_file", "")),
                    str(row_data.get("backup_size_kb", "")),
                    str(row_data.get("message", "")),
                ]
                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if c == 1:
                        item.setForeground(QColor(str(row_data.get("status_color", "#ef6c00"))))
                    table.setItem(r, c, item)

            restore_rows = self.report_service.get_restore_run_log_rows(self.backup_manager, limit=50)

            restore_table.setRowCount(len(restore_rows))
            for r, row_data in enumerate(restore_rows):
                values = [
                    str(row_data.get("run_at", "")),
                    str(row_data.get("status", "")),
                    str(row_data.get("backup_file", "")),
                    str(row_data.get("message", "")),
                ]
                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if c == 1:
                        item.setForeground(QColor(str(row_data.get("status_color", "#ef6c00"))))
                    restore_table.setItem(r, c, item)

            footer_label.setText(f"Backups shown: {len(rows)} | Restore runs shown: {len(restore_rows)}")

        def validate_selected_backup():
            backup_file = selected_backup_file()
            if not backup_file:
                AppMessageBox.information(dialog, "Select Backup", "Please select a backup row first.")
                return

            result = self.backup_manager.validate_backup_file(backup_file)
            if result.get("ok"):
                AppMessageBox.information(
                    dialog,
                    "Validation Passed",
                    f"Backup is valid.\n\nTables: {result.get('table_count', 0)}\n"
                    f"Core tables found: {result.get('required_tables_found', 0)}/{result.get('required_tables_total', 3)}",
                )
            else:
                AppMessageBox.warning(dialog, "Validation Failed", str(result.get("message") or "Validation failed."))

        def restore_selected_backup():
            backup_file = selected_backup_file()
            if not backup_file:
                AppMessageBox.information(dialog, "Select Backup", "Please select a backup row first.")
                return

            _, accepted = AppMessageBox.confirm(
                dialog,
                "Confirm Restore",
                "Restore will replace current database data with selected backup.\n"
                "A pre-restore safety backup will be created automatically.\n\n"
                "Do you want to continue?",
                confirm_label="Restore",
                cancel_label="Cancel",
                kind="warning",
            )
            if not accepted:
                return

            try:
                self.backup_manager.restore_from_backup(backup_file, create_pre_restore_backup=True)
            except Exception as exc:
                log_activity(
                    category="system",
                    action="restore_failed",
                    entity_type="backup",
                    entity_id=None,
                    note=f"Restore failed from {backup_file}: {str(exc)}",
                )
                AppMessageBox.critical(dialog, "Restore Failed", str(exc))
                load_log_rows()
                self.load_backup_health_summary()
                return

            log_activity(
                category="system",
                action="restore_completed",
                entity_type="backup",
                entity_id=None,
                note=f"Database restored from {backup_file}",
            )

            AppMessageBox.information(
                dialog,
                "Restore Completed",
                "Database restore completed successfully.\n"
                "Please close and reopen the app to ensure all screens are refreshed with restored data.",
            )
            load_log_rows()
            self.load_backup_health_summary()

        def manual_backup_and_reload():
            self.run_manual_backup()
            load_log_rows()

        backup_now_btn.clicked.connect(manual_backup_and_reload)
        backup_to_btn.clicked.connect(lambda: (self.run_manual_backup_to_location(), load_log_rows()))
        validate_btn.clicked.connect(validate_selected_backup)
        restore_btn.clicked.connect(restore_selected_backup)
        reload_btn.clicked.connect(load_log_rows)

        load_log_rows()
        dialog.exec()


    def get_reminder_queue_rows(self, include_hidden_states=False):
        self.report_service.ensure_reminder_state_table()
        rows = self.report_service.get_dashboard_reminder_queue_rows()

        active_keys = [str(r.get("reminder_key", "")) for r in rows if str(r.get("reminder_key", ""))]
        state_map = self.report_service.get_reminder_state_map(active_keys)

        visible_rows = []
        for row in rows:
            key = str(row.get("reminder_key", ""))
            state = state_map.get(key, {})
            status = str(state.get("state", "open") or "open").lower()
            snooze_until = str(state.get("snooze_until", "") or "")

            row["state"] = status
            row["snooze_until"] = snooze_until

            is_snoozed = False
            if snooze_until:
                is_snoozed = self.report_service.is_reminder_snoozed(snooze_until)

            if status == "acknowledged":
                row["visibility_state"] = "acknowledged"
            elif is_snoozed:
                row["visibility_state"] = "snoozed"
            else:
                row["visibility_state"] = "open"

            if include_hidden_states:
                visible_rows.append(row)
                continue

            if status == "acknowledged":
                continue

            if is_snoozed:
                continue

            visible_rows.append(row)

        self.report_service.cleanup_stale_reminder_state(active_keys)

        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        visible_rows.sort(key=lambda r: (priority_order.get(str(r.get("priority")), 9), str(r.get("type", "")), str(r.get("entity", ""))))
        return visible_rows


    def ensure_reminder_state_table(self):
        self.report_service.ensure_reminder_state_table()


    def get_reminder_state_map(self, reminder_keys):
        return self.report_service.get_reminder_state_map(reminder_keys)


    def set_reminder_state(self, reminder_key, state="open", snooze_days=None, clear_snooze=False):
        self.report_service.set_reminder_state(
            reminder_key,
            state=state,
            snooze_days=snooze_days,
            clear_snooze=clear_snooze,
        )


    def cleanup_stale_reminder_state(self, active_keys):
        self.report_service.cleanup_stale_reminder_state(active_keys)


    def load_reminder_summary(self):
        rows = self.get_reminder_queue_rows()
        high_count = sum(1 for r in rows if r.get("priority") == "High")
        medium_count = sum(1 for r in rows if r.get("priority") == "Medium")
        low_count = sum(1 for r in rows if r.get("priority") == "Low")

        self.reminder_count.setText(str(len(rows)))
        self.reminder_meta.setText(f"High {high_count} | Medium {medium_count} | Low {low_count}")


    def show_reminder_queue_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Reminder Queue")
        dialog.resize(1180, 640)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(8)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Type"))
        type_combo = QComboBox()
        type_combo.addItems(["All", "Payment", "Low Stock", "Expiry"])
        type_combo.setFixedWidth(160)
        filter_row.addWidget(type_combo)

        filter_row.addWidget(QLabel("Priority"))
        priority_combo = QComboBox()
        priority_combo.addItems(["All", "High", "Medium", "Low"])
        priority_combo.setFixedWidth(140)
        filter_row.addWidget(priority_combo)

        filter_row.addWidget(QLabel("Status"))
        status_combo = QComboBox()
        status_combo.addItems(["Open Only", "Asleep Only", "Done Only", "All"])
        status_combo.setFixedWidth(170)
        filter_row.addWidget(status_combo)

        filter_row.addStretch()
        reload_btn = QPushButton("Reload", objectName="TopRightButton")
        filter_row.addWidget(reload_btn)
        layout.addLayout(filter_row)

        hint = QLabel("Auto reminders include payments due/overdue, low stock, and near-expiry batches.")
        hint.setStyleSheet("color:#666;")
        layout.addWidget(hint)

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(["Status", "Type", "Priority", "Entity", "Reference", "Due Date", "Amount", "Message"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        layout.addWidget(table)

        summary_label = QLabel("Rows: 0")
        summary_label.setStyleSheet("font-weight:bold;")
        layout.addWidget(summary_label)

        action_row = QHBoxLayout()
        acknowledge_btn = QPushButton("Mark Done")
        sleep_3_btn = QPushButton("Put to Sleep (3 Days)")
        sleep_7_btn = QPushButton("Put to Sleep (7 Days)")
        wake_btn = QPushButton("Wake Up Selected")
        action_row.addWidget(acknowledge_btn)
        action_row.addWidget(sleep_3_btn)
        action_row.addWidget(sleep_7_btn)
        action_row.addWidget(wake_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

        all_rows = []
        visible_rows = []

        def render_rows(rows):
            nonlocal visible_rows
            visible_rows = rows
            table.setRowCount(len(rows))
            total_payment = 0.0

            for r, row_data in enumerate(rows):
                amount = float(row_data.get("amount", 0.0) or 0.0)
                total_payment += amount if str(row_data.get("type", "")) == "Payment" else 0.0

                visibility_state = str(row_data.get("visibility_state", "open") or "open")
                snooze_until = str(row_data.get("snooze_until", "") or "")
                if visibility_state == "acknowledged":
                    status_text = "Done"
                elif visibility_state == "snoozed":
                    status_text = f"Asleep until {snooze_until}" if snooze_until else "Asleep"
                else:
                    status_text = "Open"

                values = [
                    status_text,
                    str(row_data.get("type", "")),
                    str(row_data.get("priority", "")),
                    str(row_data.get("entity", "")),
                    str(row_data.get("reference", "")),
                    str(row_data.get("due_date", "")),
                    f"{amount:.2f}" if amount > 0 else "",
                    str(row_data.get("message", "")),
                ]

                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)

                    if c == 2:
                        p = str(row_data.get("priority", ""))
                        if p == "High":
                            item.setForeground(QColor("#b71c1c"))
                        elif p == "Medium":
                            item.setForeground(QColor("#ef6c00"))
                        elif p == "Low":
                            item.setForeground(QColor("#2e7d32"))

                    if c == 6 and amount > 0:
                        item.setForeground(QColor("#b71c1c"))

                    if c == 0:
                        item.setData(Qt.UserRole, str(row_data.get("reminder_key", "")))

                    if c == 0:
                        if visibility_state == "acknowledged":
                            item.setForeground(QColor("#616161"))
                        elif visibility_state == "snoozed":
                            item.setForeground(QColor("#6a1b9a"))
                        else:
                            item.setForeground(QColor("#2e7d32"))

                    table.setItem(r, c, item)

            high_count = sum(1 for x in rows if x.get("priority") == "High")
            summary_label.setText(
                f"Rows: {len(rows)} | High: {high_count} | Payment Outstanding (in view): {total_payment:.2f}"
            )

        def apply_filters():
            rows = all_rows

            t = (type_combo.currentText() or "All").strip()
            p = (priority_combo.currentText() or "All").strip()

            if t != "All":
                rows = [r for r in rows if str(r.get("type", "")) == t]

            if p != "All":
                rows = [r for r in rows if str(r.get("priority", "")) == p]

            status_filter = (status_combo.currentText() or "Open Only").strip()
            if status_filter == "Open Only":
                rows = [r for r in rows if str(r.get("visibility_state", "open")) == "open"]
            elif status_filter == "Asleep Only":
                rows = [r for r in rows if str(r.get("visibility_state", "open")) == "snoozed"]
            elif status_filter == "Done Only":
                rows = [r for r in rows if str(r.get("visibility_state", "open")) == "acknowledged"]

            render_rows(rows)

        def reload_data():
            nonlocal all_rows
            all_rows = self.get_reminder_queue_rows(include_hidden_states=True)
            apply_filters()

        def get_selected_key():
            row = table.currentRow()
            if row < 0 or row >= len(visible_rows):
                return ""
            item = table.item(row, 0)
            if not item:
                return ""
            return str(item.data(Qt.UserRole) or "")

        def acknowledge_selected():
            key = get_selected_key()
            if not key:
                return
            self.set_reminder_state(key, state="acknowledged", clear_snooze=True)
            reload_data()
            self.load_reminder_summary()

        def sleep_selected(days):
            key = get_selected_key()
            if not key:
                return
            self.set_reminder_state(key, state="open", snooze_days=days)
            reload_data()
            self.load_reminder_summary()

        def wake_selected():
            key = get_selected_key()
            if not key:
                return
            self.set_reminder_state(key, state="open", clear_snooze=True)
            reload_data()
            self.load_reminder_summary()

        reload_btn.clicked.connect(reload_data)
        type_combo.currentIndexChanged.connect(lambda _: apply_filters())
        priority_combo.currentIndexChanged.connect(lambda _: apply_filters())
        status_combo.currentIndexChanged.connect(lambda _: apply_filters())
        acknowledge_btn.clicked.connect(acknowledge_selected)
        sleep_3_btn.clicked.connect(lambda: sleep_selected(3))
        sleep_7_btn.clicked.connect(lambda: sleep_selected(7))
        wake_btn.clicked.connect(wake_selected)

        reload_data()
        dialog.exec()




    
    def load_low_stock_data(self):
        rows = self.report_service.get_dashboard_low_stock_rows(limit=10)

        self.low_stock_rows = rows
        self.low_stock_count.setText(str(len(rows)))

        critical = sum(1 for r in rows if float(r.get("available_qty", 0)) <= 0)
        if rows:
            self.low_stock_meta.setText(f"Critical: {critical} | Showing top {len(rows)} items")
        else:
            self.low_stock_meta.setText("No low-stock alerts")



    def load_expiry_data(self):
        rows = self.report_service.get_dashboard_expiry_rows(limit=10)

        self.expiry_rows = rows
        self.expiry_count.setText(str(len(rows)))

        expired = sum(1 for r in rows if str(r.get("status", "")) == "Expired")
        if rows:
            self.expiry_meta.setText(f"Expired: {expired} | Showing top {len(rows)} items")
        else:
            self.expiry_meta.setText("No expiry alerts")

    def load_sales_snapshot_data(self):
        selected_days = int(self.sales_snapshot_range_combo.currentData() or 7)
        range_label = str(self.sales_snapshot_range_combo.currentText() or "Last 7 days")

        trajectory_rows = self.report_service.get_dashboard_sales_trajectory_rows(days=selected_days)
        top_rows = self.report_service.get_dashboard_top_selling_item_rows(limit=5, days=selected_days)

        labels = [row.get("label", "") for row in trajectory_rows]
        sales_values = [float(row.get("sales_total", 0.0) or 0.0) for row in trajectory_rows]

        self.sales_trend_plot.clear()
        self.sales_trend_scatter = None
        self.sales_trend_points = []
        if sales_values:
            x_values = list(range(len(sales_values)))
            self.sales_trend_plot.plot(
                x_values,
                sales_values,
                pen=pg.mkPen("#264E70", width=2.5),
            )
            self.sales_trend_points = [
                {"label": labels[index], "sales_total": sales_values[index]}
                for index in range(len(labels))
            ]
            self.sales_trend_scatter = pg.ScatterPlotItem(
                x=x_values,
                y=sales_values,
                size=9,
                pen=pg.mkPen("#2A9D8F", width=1.4),
                brush=pg.mkBrush("#2A9D8F"),
                hoverable=True,
                tip=None,
                hoverPen=pg.mkPen("#1E6F66", width=2),
                hoverBrush=pg.mkBrush("#49B7A8"),
            )
            self.sales_trend_scatter.sigHovered.connect(self._show_sales_trend_hover)
            self.sales_trend_plot.addItem(self.sales_trend_scatter)
            self.sales_trend_plot.getAxis("bottom").setTicks([list(enumerate(labels))])
            self.sales_trend_plot.setXRange(-0.2, max(len(sales_values) - 0.8, 0.8), padding=0)
            self.sales_trend_plot.setYRange(0, max(sales_values) * 1.18 if max(sales_values) > 0 else 10, padding=0)
            self.sales_trend_meta.setText(
                f"{range_label} | Peak {max(sales_values):,.0f} PKR"
            )
        else:
            self.sales_trend_meta.setText(f"{range_label} | No sales yet")

        self.top_selling_table.setRowCount(len(top_rows))
        for row_index, row_data in enumerate(top_rows):
            highlight = row_index == 0
            secondary_highlight = row_index == 1
            if highlight:
                row_bg = QColor("#E6F3EF")
            elif secondary_highlight:
                row_bg = QColor("#F1F7FB")
            else:
                row_bg = QColor("#F8FBFD" if row_index % 2 == 0 else "#F1F6FA")

            name_item = QTableWidgetItem(str(row_data.get("product_name", "")))
            name_item.setFlags(name_item.flags() ^ Qt.ItemIsEditable)
            name_item.setBackground(row_bg)
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            if highlight:
                name_item.setForeground(QColor("#1E5A46"))
            amount_item = QTableWidgetItem(f"{float(row_data.get('sales_amount', 0.0) or 0.0):,.0f}")
            amount_item.setFlags(amount_item.flags() ^ Qt.ItemIsEditable)
            amount_item.setBackground(row_bg)
            amount_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            amount_item.setBackground(row_bg)
            if highlight:
                amount_item.setForeground(QColor("#1E5A46"))
            self.top_selling_table.setItem(row_index, 0, name_item)
            self.top_selling_table.setCellWidget(
                row_index,
                1,
                self._build_sold_units_label(
                    row_data.get("total_qty", 0.0),
                    row_data.get("pack_size", 1.0),
                    emphasized=highlight,
                ),
            )
            self.top_selling_table.setItem(row_index, 2, amount_item)

        if top_rows:
            self.top_selling_meta.setText(
                f"{range_label} | Top {len(top_rows)} items"
            )
        else:
            self.top_selling_meta.setText(f"{range_label} | No sales yet")

    def _show_sales_trend_hover(self, _scatter, points, _event):
        if points is None or len(points) == 0:
            QToolTip.hideText()
            return

        index = int(round(points[0].pos().x()))
        if index < 0 or index >= len(self.sales_trend_points):
            QToolTip.hideText()
            return

        row = self.sales_trend_points[index]
        QToolTip.showText(
            self.cursor().pos(),
            (
                f"<div style='line-height:1.25;'>"
                f"<span style='font-size:11px; color:#B8D4E3;'>{row['label']}</span><br>"
                f"<span style='font-size:13px; font-weight:700;'>"
                f"{row['sales_total']:,.0f} PKR"
                f"</span></div>"
            ),
            self.sales_trend_plot,
        )


    def show_low_stock_queue_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Low Stock Queue")
        dialog.resize(900, 520)

        layout = QVBoxLayout(dialog)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Products at/below reorder level"))
        top_row.addStretch()
        reload_btn = QPushButton("Reload", objectName="TopRightButton")
        top_row.addWidget(reload_btn)
        layout.addLayout(top_row)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Product", "Available", "Reorder"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(table)

        summary = QLabel("Rows: 0")
        summary.setStyleSheet("font-weight:bold;")
        layout.addWidget(summary)

        def reload_data():
            self.load_low_stock_data()
            rows = getattr(self, "low_stock_rows", [])
            table.setRowCount(len(rows))

            for r, row_data in enumerate(rows):
                available_qty = float(row_data.get("available_qty", 0) or 0.0)
                reorder_level = float(row_data.get("reorder_level", 0) or 0.0)
                values = [
                    str(row_data.get("product_name", "")),
                    f"{available_qty:.0f}",
                    f"{reorder_level:.0f}",
                ]
                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if available_qty <= 0:
                        item.setBackground(QColor("#ffebee"))
                    else:
                        item.setBackground(QColor("#fff3e0"))
                    table.setItem(r, c, item)

            critical = sum(1 for x in rows if float(x.get("available_qty", 0) or 0) <= 0)
            summary.setText(f"Rows: {len(rows)} | Critical: {critical}")

        reload_btn.clicked.connect(reload_data)
        reload_data()
        dialog.exec()


    def show_expiry_queue_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Expiry Queue")
        dialog.resize(980, 560)

        layout = QVBoxLayout(dialog)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Expired and near-expiry batches"))
        top_row.addStretch()
        reload_btn = QPushButton("Reload", objectName="TopRightButton")
        top_row.addWidget(reload_btn)
        layout.addLayout(top_row)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Product", "Batch", "Expiry", "Status", "Remaining Days"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(table)

        summary = QLabel("Rows: 0")
        summary.setStyleSheet("font-weight:bold;")
        layout.addWidget(summary)

        def reload_data():
            self.load_expiry_data()
            rows = getattr(self, "expiry_rows", [])
            table.setRowCount(len(rows))

            for r, row_data in enumerate(rows):
                status = str(row_data.get("status", ""))
                remaining_days = int(row_data.get("remaining_days", 0) or 0)
                values = [
                    str(row_data.get("product_name", "")),
                    str(row_data.get("batch_no", "")),
                    str(row_data.get("expiry_date", "")),
                    status,
                    str(remaining_days) if status == "Expiring Soon" else "-",
                ]
                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if status == "Expired":
                        item.setBackground(QColor("#ffebee"))
                    else:
                        item.setBackground(QColor("#fff3e0"))
                    table.setItem(r, c, item)

            expired = sum(1 for x in rows if str(x.get("status", "")) == "Expired")
            summary.setText(f"Rows: {len(rows)} | Expired: {expired}")

        reload_btn.clicked.connect(reload_data)
        reload_data()
        dialog.exec()

























    def showEvent(self, event):
        
        super().showEvent(event)
        # Refresh shortly after the dashboard becomes visible without blocking
        # the first paint.
        QTimer.singleShot(150, self.refresh_dashboard_alerts)
        
        

        
        
    
    
    def get_hourly_sales_data(self):
        return self.report_service.get_hourly_sales_series()



    
    def get_monthly_sales_data(self):
        return self.report_service.get_monthly_sales_series()



   
