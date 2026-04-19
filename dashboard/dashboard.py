from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHeaderView,QDialog, QLineEdit,QSpacerItem, QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QFileDialog, QInputDialog, QApplication, QGridLayout
from PySide6.QtCore import Qt, QFile, QDate, QDateTime, Signal, QTimer
from PySide6.QtGui import QColor
import sys, os
from PySide6.QtSql import QSqlQuery, QSqlDatabase
from PySide6.QtCore import QDate
from functools import partial
from utilities import mylogin
from utilities.database import SQLiteConnectionManager
from utilities.activity_logger import log_activity
from utilities.permissions import Permissions
from utilities.session_service import SessionErrorCode, check_active_session
import pyqtgraph as pg
import bcrypt
from dashboard.daily_session import DailySession


import os
import sys
from utilities.app_messagebox import AppMessageBox
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
        self.backup_card = self.build_backup_health_card()

        self._apply_dashboard_card_style(self.quick_links_card)
        self._apply_dashboard_card_style(self.session_card)
        self._apply_dashboard_card_style(self.low_stock_card)
        self._apply_dashboard_card_style(self.expiry_card)
        self._apply_dashboard_card_style(self.reminders_card)
        self._apply_dashboard_card_style(self.backup_card)

        alerts_layout.addWidget(self.quick_links_card)
        alerts_layout.addWidget(self.session_card)

        operational_row = QHBoxLayout()
        operational_row.setSpacing(12)
        operational_row.addWidget(self.low_stock_card, 1)
        operational_row.addWidget(self.expiry_card, 1)
        operational_row.addWidget(self.reminders_card, 1)
        alerts_layout.addLayout(operational_row)

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

    def get_today_session_sales_rows(self, session_id):
        rows = []
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                s.id,
                COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                COALESCE(a.username, '') AS salesman_name,
                COALESCE(s.total, 0),
                COALESCE(s.received, 0),
                COALESCE(s.remaining, 0),
                COALESCE(s.writeoff, 0),
                COALESCE(s.creation_date, '')
            FROM sales s
            LEFT JOIN customer c ON c.id = s.customer
            LEFT JOIN auth a ON a.id = s.salesman
            WHERE s.session_id = :session_id
              AND DATE(s.creation_date) = DATE('now')
            ORDER BY datetime(s.creation_date) DESC, s.id DESC
            """
        )
        query.bindValue(":session_id", int(session_id))

        if not query.exec():
            raise Exception(f"Could not load today's sales.\n\n{query.lastError().text()}")

        while query.next():
            rows.append({
                "sale_id": int(query.value(0) or 0),
                "customer_name": str(query.value(1) or ""),
                "salesman_name": str(query.value(2) or ""),
                "total": float(query.value(3) or 0.0),
                "received": float(query.value(4) or 0.0),
                "remaining": float(query.value(5) or 0.0),
                "writeoff": float(query.value(6) or 0.0),
                "creation_date": str(query.value(7) or ""),
            })
        return rows

    def get_today_session_sales_return_rows(self, session_id):
        rows = []
        query = QSqlQuery()
        query.prepare(
            """
            SELECT
                sr.id,
                COALESCE(sr.salesorder, 0),
                COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                COALESCE(a.username, '') AS salesman_name,
                COALESCE(sr.total, 0),
                COALESCE(sr.paid, 0),
                COALESCE(sr.remaining, 0),
                COALESCE(sr.creation_date, '')
            FROM salesreturn sr
            LEFT JOIN customer c ON c.id = sr.customer
            LEFT JOIN auth a ON a.id = sr.salesman
            WHERE sr.session_id = :session_id
              AND DATE(sr.creation_date) = DATE('now')
            ORDER BY datetime(sr.creation_date) DESC, sr.id DESC
            """
        )
        query.bindValue(":session_id", int(session_id))

        if not query.exec():
            raise Exception(f"Could not load today's sales returns.\n\n{query.lastError().text()}")

        while query.next():
            rows.append({
                "return_id": int(query.value(0) or 0),
                "salesorder_id": int(query.value(1) or 0),
                "customer_name": str(query.value(2) or ""),
                "salesman_name": str(query.value(3) or ""),
                "total": float(query.value(4) or 0.0),
                "paid": float(query.value(5) or 0.0),
                "remaining": float(query.value(6) or 0.0),
                "creation_date": str(query.value(7) or ""),
            })
        return rows

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

        query = QSqlQuery()
        query.prepare(
            """
            SELECT timestamp
            FROM activity_log
            WHERE category = 'login'
              AND action = 'login'
              AND username = ?
            ORDER BY datetime(timestamp) DESC
            LIMIT 1
            """
        )
        query.addBindValue(username)

        last_login_text = ""
        if query.exec() and query.next():
            last_login_text = str(query.value(0) or "").strip()

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
            date_filter_sql = ""

            if period_key == "today":
                date_filter_sql = " AND DATE(timestamp) = DATE('now') "
            elif period_key == "week":
                date_filter_sql = " AND DATE(timestamp) >= DATE('now', '-6 days') "
            elif period_key == "month":
                date_filter_sql = " AND DATE(timestamp) >= DATE('now', '-29 days') "

            query = QSqlQuery()
            query.prepare(
                f"""
                SELECT
                    COALESCE(al.timestamp, ''),
                    COALESCE(al.login_session_id, ''),
                    COALESCE(al.daily_session_id, ''),
                    COALESCE(ds.session_date, ''),
                    COALESCE((
                        SELECT lo.timestamp
                        FROM activity_log lo
                        WHERE lo.category = 'login'
                          AND lo.action = 'logout'
                          AND COALESCE(lo.login_session_id, '') = COALESCE(al.login_session_id, '')
                        ORDER BY datetime(lo.timestamp) DESC
                        LIMIT 1
                    ), '')
                FROM activity_log al
                LEFT JOIN daily_session ds ON ds.id = al.daily_session_id
                WHERE al.category = 'login'
                  AND al.action = 'login'
                  AND al.username = ?
                  {date_filter_sql}
                ORDER BY datetime(al.timestamp) DESC
                LIMIT 500
                """
            )
            query.addBindValue(username)

            rows = []
            if query.exec():
                while query.next():
                    raw_timestamp = str(query.value(0) or "").strip()
                    logout_timestamp = str(query.value(4) or "").strip()
                    login_dt = QDateTime.fromString(raw_timestamp, "yyyy-MM-dd HH:mm:ss")
                    if not login_dt.isValid():
                        login_dt = QDateTime.fromString(raw_timestamp, Qt.ISODate)

                    logout_dt = QDateTime.fromString(logout_timestamp, "yyyy-MM-dd HH:mm:ss")
                    if not logout_dt.isValid():
                        logout_dt = QDateTime.fromString(logout_timestamp, Qt.ISODate)

                    if login_dt.isValid():
                        if login_dt.timeSpec() == Qt.LocalTime:
                            login_dt.setTimeSpec(Qt.UTC)
                        login_dt = login_dt.toLocalTime()
                        login_date = login_dt.toString("ddd, dd MMM yyyy")
                        login_time = login_dt.toString("hh:mm AP")
                    else:
                        login_date = raw_timestamp
                        login_time = ""

                    if logout_dt.isValid():
                        if logout_dt.timeSpec() == Qt.LocalTime:
                            logout_dt.setTimeSpec(Qt.UTC)
                        logout_dt = logout_dt.toLocalTime()
                        logout_time = logout_dt.toString("hh:mm AP")
                    else:
                        logout_time = "Active / Unknown"

                    duration_text = "-"
                    if login_dt.isValid() and logout_dt.isValid():
                        total_seconds = max(0, login_dt.secsTo(logout_dt))
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        if hours > 0:
                            duration_text = f"{hours}h {minutes}m"
                        else:
                            duration_text = f"{minutes}m"

                    daily_session_id = str(query.value(2) or "").strip()
                    session_date = str(query.value(3) or "").strip()
                    if daily_session_id and session_date:
                        daily_session_label = f"Session #{daily_session_id} | {session_date}"
                    elif daily_session_id:
                        daily_session_label = f"Session #{daily_session_id}"
                    else:
                        daily_session_label = "-"

                    rows.append({
                        "login_date": login_date,
                        "login_time": login_time,
                        "logout_time": logout_time,
                        "duration": duration_text,
                        "daily_session_label": daily_session_label,
                    })

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

    def refresh_dashboard_alerts(self):
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            return
        self.load_inventory_alerts()

    def _show_session_state_error(self, result, action_label="continue"):
        return DailySession._show_session_state_error(self, result, action_label)

    def _get_strict_active_session_id(self, action_label="continue"):
        return DailySession._get_strict_active_session_id(self, action_label)

    def get_open_session(self):
        return DailySession.get_open_session(self)

    def open_session_dialog(self):
        return DailySession.open_session_dialog(self)

    def get_previous_balance(self):
        return DailySession.get_previous_balance(self)

    def get_cash_expenses(self):
        return DailySession.get_cash_expenses(self)

    def get_session_payment_method_summary(self, methods=None):
        return DailySession.get_session_payment_method_summary(self, methods)

    def close_session_dialog(self, session_data):
        return DailySession.close_session_dialog(self, session_data)

    def get_opening_cash(self):
        return DailySession.get_opening_cash(self)

    def get_current_session_cash_flows(self):
        return DailySession.get_current_session_cash_flows(self)

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

        query = QSqlQuery()
        query.prepare(
            """
            INSERT INTO daily_session (session_date, opening_cash, status)
            VALUES (?, ?, 'open')
            """
        )
        query.addBindValue(session_data["session_date"])
        query.addBindValue(session_data["opening_cash"])

        if not query.exec():
            AppMessageBox.critical(self, "Database Error", f"Could not open daily session.\n\n{query.lastError().text()}")
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

        query = QSqlQuery()
        query.prepare(
            """
            UPDATE daily_session
            SET
                system_cash = ?,
                actual_cash = ?,
                withdrawal = ?,
                cash_difference = ?,
                closed_at = CURRENT_TIMESTAMP,
                status = 'closed'
            WHERE id = ?
            """
        )
        query.addBindValue(result["system_cash"])
        query.addBindValue(result["actual_cash"])
        query.addBindValue(result["withdraw_amount"])
        query.addBindValue(result["cash_difference"])
        query.addBindValue(session["id"])

        if not query.exec():
            AppMessageBox.critical(self, "Database Error", f"Could not close daily session.\n\n{query.lastError().text()}")
            return

        self.refresh_dashboard_alerts()


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

        query = QSqlQuery()
        query.prepare("SELECT password_hash FROM auth WHERE id = ? AND role = 'admin' AND status = 'active' LIMIT 1")
        query.addBindValue(int(user_id))

        if not query.exec() or not query.next():
            AppMessageBox.warning(self, "Verification Failed", "Could not verify admin account.")
            return False

        stored_hash = str(query.value(0) or "")
        if not stored_hash:
            AppMessageBox.warning(self, "Verification Failed", "Stored admin password is missing.")
            return False

        try:
            valid = bcrypt.checkpw(str(password).encode(), stored_hash.encode())
        except Exception:
            valid = False

        if not valid:
            AppMessageBox.warning(self, "Verification Failed", "Invalid admin password.")
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
        health = self.backup_manager.get_backup_health(stale_after_hours=30)
        level = str(health.get("status_level", "warning"))
        text = str(health.get("status_text", ""))
        last_run = str(health.get("last_run_status", "unknown")).upper()

        if level == "ok":
            self.backup_status_badge.setText("OK")
            self.backup_status_badge.setStyleSheet("font-weight:bold; color:#2e7d32;")
        elif level == "critical":
            self.backup_status_badge.setText("ALERT")
            self.backup_status_badge.setStyleSheet("font-weight:bold; color:#b71c1c;")
        else:
            self.backup_status_badge.setText("WARN")
            self.backup_status_badge.setStyleSheet("font-weight:bold; color:#ef6c00;")

        self.backup_meta.setText(f"{text} | Last run: {last_run}")


    def show_backup_status_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Backup Status")
        dialog.resize(1080, 640)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        health = self.backup_manager.get_backup_health(stale_after_hours=30)
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
            rows = []
            for row in self.backup_manager.get_backup_run_logs(limit=100):
                rows.append([
                    str(row.get("run_at", "")),
                    str(row.get("status", "")),
                    str(row.get("trigger_source", "")),
                    str(row.get("backup_file", "")),
                    str(round((float(row.get("backup_size", 0) or 0) / 1024.0), 1)),
                    str(row.get("message", "")),
                ])

            table.setRowCount(len(rows))
            for r, values in enumerate(rows):
                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if c == 1:
                        status = value.lower()
                        if status == "success":
                            item.setForeground(QColor("#2e7d32"))
                        elif status == "failed":
                            item.setForeground(QColor("#b71c1c"))
                        else:
                            item.setForeground(QColor("#ef6c00"))
                    table.setItem(r, c, item)

            restore_rows = []
            for row in self.backup_manager.get_restore_run_logs(limit=50):
                restore_rows.append([
                    str(row.get("run_at", "")),
                    str(row.get("status", "")),
                    str(row.get("backup_file", "")),
                    str(row.get("message", "")),
                ])

            restore_table.setRowCount(len(restore_rows))
            for r, values in enumerate(restore_rows):
                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    if c == 1:
                        s = value.lower()
                        if s == "success":
                            item.setForeground(QColor("#2e7d32"))
                        elif s == "failed":
                            item.setForeground(QColor("#b71c1c"))
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
        self.ensure_reminder_state_table()
        rows = []

        # Payment follow-up reminders (overdue + due soon)
        payment_query = QSqlQuery()
        payment_query.prepare("""
            SELECT
                s.id,
                COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                COALESCE(s.receiveable, 0) AS outstanding,
                DATE(s.due_date) AS due_date,
                CAST(julianday('now', 'localtime') - julianday(s.due_date) AS INTEGER) AS due_delta_days
            FROM sales s
            LEFT JOIN customer c ON c.id = s.customer
            WHERE COALESCE(s.receiveable, 0) > 0
              AND COALESCE(s.writeoff, 0) = 0
              AND s.due_date IS NOT NULL
        """)

        if payment_query.exec():
            while payment_query.next():
                invoice_id = int(payment_query.value(0) or 0)
                customer_name = str(payment_query.value(1) or "")
                outstanding = float(payment_query.value(2) or 0.0)
                due_date = str(payment_query.value(3) or "")
                due_delta = int(payment_query.value(4) or 0)

                if due_delta > 30:
                    priority = "High"
                elif due_delta > 0:
                    priority = "Medium"
                elif due_delta >= -3:
                    priority = "Low"
                else:
                    continue

                if due_delta > 0:
                    message = f"Invoice #{invoice_id} for {customer_name} is overdue by {due_delta} day(s)."
                else:
                    message = f"Invoice #{invoice_id} for {customer_name} is due in {abs(due_delta)} day(s)."

                rows.append({
                    "reminder_key": f"PAYMENT:SALE#{invoice_id}",
                    "type": "Payment",
                    "priority": priority,
                    "entity": customer_name,
                    "reference": f"SALE#{invoice_id}",
                    "due_date": due_date,
                    "message": message,
                    "amount": outstanding,
                })
        else:
            print("Payment reminder query failed:", payment_query.lastError().text())

        # Low stock reminders
        low_stock_query = QSqlQuery()
        low_stock_query.prepare("""
            SELECT
                p.id,
                p.display_name,
                COALESCE(SUM(b.quantity_remaining), 0) AS available_qty,
                MAX(COALESCE(pp.reorder_level, 0)) AS reorder_level
            FROM product p
            LEFT JOIN price_pack pp ON pp.product_id = p.id
            LEFT JOIN batch b ON b.product_id = p.id
            WHERE p.status = 'used'
            GROUP BY p.id, p.display_name
            HAVING COALESCE(SUM(b.quantity_remaining), 0) <= MAX(COALESCE(pp.reorder_level, 0))
            ORDER BY available_qty ASC
            LIMIT 25
        """)

        if low_stock_query.exec():
            while low_stock_query.next():
                product_id = int(low_stock_query.value(0) or 0)
                product_name = str(low_stock_query.value(1) or "")
                available_qty = float(low_stock_query.value(2) or 0.0)
                reorder_level = float(low_stock_query.value(3) or 0.0)
                priority = "High" if available_qty <= 0 else "Medium"
                rows.append({
                    "reminder_key": f"LOW_STOCK:PROD#{product_id}",
                    "type": "Low Stock",
                    "priority": priority,
                    "entity": product_name,
                    "reference": "",
                    "due_date": "",
                    "message": f"Available {available_qty:.0f} vs reorder {reorder_level:.0f}.",
                    "amount": 0.0,
                })
        else:
            print("Low stock reminder query failed:", low_stock_query.lastError().text())

        # Expiry reminders
        expiry_query = QSqlQuery()
        expiry_query.prepare("""
            WITH parsed AS (
                SELECT
                    b.id AS batch_id,
                    p.display_name,
                    COALESCE(b.batch_no, '-') AS batch_no,
                    b.expiry_date,
                    CASE
                        WHEN b.expiry_date LIKE '____-__-__' THEN date(b.expiry_date)
                        WHEN b.expiry_date LIKE '__-__-____'
                            THEN date(substr(b.expiry_date, 7, 4) || '-' || substr(b.expiry_date, 4, 2) || '-' || substr(b.expiry_date, 1, 2))
                        ELSE NULL
                    END AS expiry_norm
                FROM batch b
                JOIN product p ON p.id = b.product_id
                WHERE p.status = 'used'
                  AND b.quantity_remaining > 0
                  AND b.expiry_date IS NOT NULL
            )
            SELECT
                batch_id,
                display_name,
                batch_no,
                expiry_date,
                CAST(julianday(expiry_norm) - julianday(date('now', 'localtime')) AS INTEGER) AS remaining_days
            FROM parsed
            WHERE expiry_norm IS NOT NULL
              AND expiry_norm <= date('now', 'localtime', '+45 days')
            ORDER BY expiry_norm ASC
            LIMIT 25
        """)

        if expiry_query.exec():
            while expiry_query.next():
                batch_id = int(expiry_query.value(0) or 0)
                product_name = str(expiry_query.value(1) or "")
                batch_no = str(expiry_query.value(2) or "")
                expiry_date = str(expiry_query.value(3) or "")
                remaining_days = int(expiry_query.value(4) or 0)

                if remaining_days < 0:
                    priority = "High"
                elif remaining_days <= 15:
                    priority = "Medium"
                else:
                    priority = "Low"

                rows.append({
                    "reminder_key": f"EXPIRY:BATCH#{batch_id}",
                    "type": "Expiry",
                    "priority": priority,
                    "entity": product_name,
                    "reference": f"Batch {batch_no}",
                    "due_date": expiry_date,
                    "message": f"Batch {batch_no} expires in {remaining_days} day(s).",
                    "amount": 0.0,
                })
        else:
            print("Expiry reminder query failed:", expiry_query.lastError().text())

        active_keys = [str(r.get("reminder_key", "")) for r in rows if str(r.get("reminder_key", ""))]
        state_map = self.get_reminder_state_map(active_keys)

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
                now_check = QSqlQuery()
                now_check.prepare("SELECT CASE WHEN datetime('now','localtime') <= datetime(?) THEN 1 ELSE 0 END")
                now_check.addBindValue(snooze_until)
                if now_check.exec() and now_check.next():
                    is_snoozed = int(now_check.value(0) or 0) == 1

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

        self.cleanup_stale_reminder_state(active_keys)

        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        visible_rows.sort(key=lambda r: (priority_order.get(str(r.get("priority")), 9), str(r.get("type", "")), str(r.get("entity", ""))))
        return visible_rows


    def ensure_reminder_state_table(self):
        query = QSqlQuery()
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS reminder_state (
                reminder_key TEXT PRIMARY KEY,
                state TEXT NOT NULL DEFAULT 'open',
                snooze_until TEXT,
                updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """):
            print("reminder_state table create failed:", query.lastError().text())


    def get_reminder_state_map(self, reminder_keys):
        state_map = {}
        keys = [k for k in reminder_keys if k]
        if not keys:
            return state_map

        placeholders = ",".join(["?"] * len(keys))
        query = QSqlQuery()
        query.prepare(f"""
            SELECT reminder_key, state, COALESCE(snooze_until, '')
            FROM reminder_state
            WHERE reminder_key IN ({placeholders})
        """)
        for key in keys:
            query.addBindValue(key)

        if not query.exec():
            print("reminder_state read failed:", query.lastError().text())
            return state_map

        while query.next():
            r_key = str(query.value(0) or "")
            state_map[r_key] = {
                "state": str(query.value(1) or "open"),
                "snooze_until": str(query.value(2) or ""),
            }

        return state_map


    def set_reminder_state(self, reminder_key, state="open", snooze_days=None, clear_snooze=False):
        if not reminder_key:
            return

        query = QSqlQuery()
        if clear_snooze:
            query.prepare("""
                INSERT INTO reminder_state (reminder_key, state, snooze_until, updated_at)
                VALUES (?, ?, NULL, datetime('now','localtime'))
                ON CONFLICT(reminder_key) DO UPDATE SET
                    state = excluded.state,
                    snooze_until = NULL,
                    updated_at = datetime('now','localtime')
            """)
            query.addBindValue(reminder_key)
            query.addBindValue(state)
        elif snooze_days is not None:
            try:
                snooze_days = int(snooze_days)
            except Exception:
                snooze_days = 1
            if snooze_days < 1:
                snooze_days = 1
            query.prepare("""
                INSERT INTO reminder_state (reminder_key, state, snooze_until, updated_at)
                VALUES (?, 'open', datetime('now','localtime', ?), datetime('now','localtime'))
                ON CONFLICT(reminder_key) DO UPDATE SET
                    state = 'open',
                    snooze_until = datetime('now','localtime', ?),
                    updated_at = datetime('now','localtime')
            """)
            modifier = f"+{snooze_days} days"
            query.addBindValue(reminder_key)
            query.addBindValue(modifier)
            query.addBindValue(modifier)
        else:
            query.prepare("""
                INSERT INTO reminder_state (reminder_key, state, snooze_until, updated_at)
                VALUES (?, ?, NULL, datetime('now','localtime'))
                ON CONFLICT(reminder_key) DO UPDATE SET
                    state = excluded.state,
                    snooze_until = NULL,
                    updated_at = datetime('now','localtime')
            """)
            query.addBindValue(reminder_key)
            query.addBindValue(state)

        if not query.exec():
            print("reminder_state update failed:", query.lastError().text())


    def cleanup_stale_reminder_state(self, active_keys):
        keys = [k for k in active_keys if k]
        query = QSqlQuery()
        if not keys:
            query.exec("DELETE FROM reminder_state")
            return

        placeholders = ",".join(["?"] * len(keys))
        sql = f"DELETE FROM reminder_state WHERE reminder_key NOT IN ({placeholders})"
        query.prepare(sql)
        for key in keys:
            query.addBindValue(key)
        if not query.exec():
            print("reminder_state cleanup failed:", query.lastError().text())


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
        rows = []
        query = QSqlQuery()
        query.prepare("""
            SELECT
                p.id,
                p.display_name,
                COALESCE(SUM(b.quantity_remaining), 0) AS available_qty,
                MAX(COALESCE(pp.reorder_level, 0)) AS reorder_level
            FROM product p
            LEFT JOIN price_pack pp
                ON pp.product_id = p.id
            LEFT JOIN batch b
                ON b.product_id = p.id
            WHERE
                p.status = 'used'
            GROUP BY
                p.id, p.display_name
            HAVING
                COALESCE(SUM(b.quantity_remaining), 0) <= MAX(COALESCE(pp.reorder_level, 0))
            ORDER BY
                available_qty ASC,
                p.display_name ASC
            LIMIT 10
        """)

        if not query.exec():
            print("Low stock query failed:", query.lastError().text())
            return

        while query.next():
            rows.append({
                "product_id": int(query.value(0) or 0),
                "product_name": str(query.value(1) or ""),
                "available_qty": float(query.value(2) or 0.0),
                "reorder_level": float(query.value(3) or 0.0),
            })

        self.low_stock_rows = rows
        self.low_stock_count.setText(str(len(rows)))

        critical = sum(1 for r in rows if float(r.get("available_qty", 0)) <= 0)
        if rows:
            self.low_stock_meta.setText(f"Critical: {critical} | Showing top {len(rows)} items")
        else:
            self.low_stock_meta.setText("No low-stock alerts")



    def load_expiry_data(self):
        rows = []
        query = QSqlQuery()
        query.prepare("""
            WITH parsed AS (
                SELECT
                    p.display_name,
                    COALESCE(b.batch_no, '-') AS batch_no,
                    b.expiry_date,
                    CASE
                        WHEN b.expiry_date LIKE '____-__-__' THEN date(b.expiry_date)
                        WHEN b.expiry_date LIKE '__-__-____'
                            THEN date(substr(b.expiry_date, 7, 4) || '-' || substr(b.expiry_date, 4, 2) || '-' || substr(b.expiry_date, 1, 2))
                        ELSE NULL
                    END AS expiry_norm
                FROM batch b
                JOIN product p ON p.id = b.product_id
                WHERE
                    p.status = 'used'
                    AND b.quantity_remaining > 0
                    AND b.expiry_date IS NOT NULL
            )
            SELECT
                display_name,
                batch_no,
                expiry_date,
                CASE
                    WHEN expiry_norm < date('now', 'localtime') THEN 'Expired'
                    WHEN expiry_norm <= date('now', 'localtime', '+180 days') THEN 'Expiring Soon'
                END AS alert_status,
                CAST(julianday(expiry_norm) - julianday(date('now', 'localtime')) AS INTEGER) AS remaining_days
            FROM parsed
            WHERE
                expiry_norm IS NOT NULL
                AND expiry_norm <= date('now', 'localtime', '+180 days')
            ORDER BY
                expiry_norm ASC,
                display_name ASC
            LIMIT 10
        """)

        if not query.exec():
            print("Expiry query failed:", query.lastError().text())
            return

        while query.next():
            rows.append({
                "product_name": str(query.value(0) or ""),
                "batch_no": str(query.value(1) or ""),
                "expiry_date": str(query.value(2) or ""),
                "status": str(query.value(3) or ""),
                "remaining_days": int(query.value(4) or 0),
            })

        self.expiry_rows = rows
        self.expiry_count.setText(str(len(rows)))

        expired = sum(1 for r in rows if str(r.get("status", "")) == "Expired")
        if rows:
            self.expiry_meta.setText(f"Expired: {expired} | Showing top {len(rows)} items")
        else:
            self.expiry_meta.setText("No expiry alerts")


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
        
        
        from zoneinfo import ZoneInfo
        from datetime import datetime

        
        local_offset = datetime.now().astimezone().utcoffset()
        offset_hours = int(local_offset.total_seconds() // 3600)
        offset_str = f"{offset_hours:+d} hours"  # e.g. '+5 hours' or '-4 hours'

        print("Local offset:", offset_str)

        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')

        # Initialize hourly sales dictionary
        hourly_sales = {i: 0 for i in range(24)}

        query = QSqlQuery()
        
        query.prepare("""
            SELECT 
                strftime('%H', datetime(creation_date, :offset)) AS hour,
                COALESCE(SUM(total), 0) AS total_sales
            FROM sales
            WHERE 
                date(datetime(creation_date, :offset)) = date(:today)
            GROUP BY hour
            ORDER BY hour
        """)

        query.bindValue(":offset", offset_str)
        query.bindValue(":today", today)

        print("Today = ", today)

        if query.exec():
            while query.next():
                hour = int(query.value(0))  # '09' → 9
                total = float(query.value(1))
                hourly_sales[hour] = total
                print(f"Hour: {hour}, Total: {total}")
        else:
            print("Query failed:", query.lastError().text())

        return hourly_sales



    
    def get_monthly_sales_data(self):
        
        monthly_sales = {day: 0 for day in range(1, 32)}

        query = QSqlQuery()
        # query.prepare("""
        #     SELECT
        #         day::int,
        #         COALESCE(SUM(total), 0) AS total_sales
        #     FROM
        #         generate_series(1, 31) AS day
        #     LEFT JOIN
        #         sales ON EXTRACT(DAY FROM creation_date) = day
        #             AND date_trunc('month', creation_date) = date_trunc('month', CURRENT_DATE)
        #     GROUP BY day
        #     ORDER BY day;
        # """)
        
        query.prepare("""
            WITH RECURSIVE days(day) AS (
                SELECT 1
                UNION ALL
                SELECT day + 1 FROM days WHERE day < 31
            )
            SELECT
                days.day,
                COALESCE(SUM(s.total), 0) AS total_sales
            FROM
                days
            LEFT JOIN
                sales s
                ON CAST(STRFTIME('%d', s.creation_date) AS INTEGER) = days.day
                AND STRFTIME('%Y-%m', s.creation_date) = STRFTIME('%Y-%m', 'now')
            GROUP BY
                days.day
            ORDER BY
                days.day;
        """)


        if query.exec():
            while query.next():
                day = int(query.value(0))
                total = float(query.value(1))
                monthly_sales[day] = total
        else:
            print("Query failed:", query.lastError().text())

        # Return a list for days 1 to 31
        return [monthly_sales[day] for day in range(1, 32)]



   
