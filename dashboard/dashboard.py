from PySide6.QtWidgets import QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QPushButton, QLabel, QFrame, QComboBox, QSpacerItem
from PySide6.QtCore import Qt, QFile, QDate, Signal
import sys, os
from PySide6.QtSql import QSqlQuery, QSqlDatabase
from PySide6.QtCore import QDate
from functools import partial
from utilities import mylogin
import pyqtgraph as pg


import os
import sys


def resource_path(relative_path):
    """Return the absolute path to a resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS  # PyInstaller extracts files here
    except AttributeError:
        base_path = os.path.abspath(".")  # running from source
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





class DashboardWidget(QWidget):
    
    
    sales_page_signal = Signal()
    product_page_signal = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # main vertical layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Business Dashboard", objectName="SectionTitle")
        # self.supplierlist = QPushButton("Date / Time", objectName="TopRightButton")
        # self.supplierlist.setCursor(Qt.PointingHandCursor)
        # self.supplierlist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        # header_layout.addWidget(self.supplierlist)
        
        
        self.create_sale = QPushButton("Create New Sale", objectName="TopRightButton")
        self.create_sale.setCursor(Qt.PointingHandCursor)
        self.create_sale.setFixedWidth(150)
        self.create_sale.clicked.connect(partial(self.sales_page_signal.emit))
        
        self.product_btn = QPushButton("View Products", objectName="TopRightButton")
        self.product_btn.setCursor(Qt.PointingHandCursor)
        self.product_btn.setFixedWidth(150)
        self.product_btn.clicked.connect(partial(self.product_page_signal.emit))

        header_layout.addWidget(self.create_sale, 0, Qt.AlignRight)
        header_layout.addWidget(self.product_btn, 0, Qt.AlignRight)

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

        

        today_sale_label = QLabel("Today's Sale - By Hour")
        self.layout.addWidget(today_sale_label)
        
        # Plot widget
        plot_widget = pg.PlotWidget()
        self.layout.setContentsMargins(30, 30, 30, 30)  # left, top, right, bottom margins around all widgets in the layout
        self.layout.setSpacing(20)  # space between widgets

        plot_widget.setStyleSheet("""
            background-color: #f0f0f0;      /* light gray background */
            border: 2px solid #3498db;     /* blue border */
        """)


        self.layout.addWidget(plot_widget)

        # Get sales data and plot
        hourly_sales = self.get_hourly_sales_data()
        hours = list(range(24))
        hour_sales = [hourly_sales.get(h, 0) for h in hours]
        

        # bg = pg.BarGraphItem(x=hours, height=sales, width=0.6, brush='skyblue')
        from datetime import datetime
        # Create a PlotDataItem (line plot) with markers
        plot_widget.plot(hours, hour_sales,  pen=pg.mkPen('#e74c3c', width=2), symbol='o', symbolSize=8, symbolBrush='b')
        hour_labels = []
        for i in range(24):
            if i == 0:
                label = "12am"
            elif i == 12:
                label = "12pm"
            else:
                label = str(i % 12)
            hour_labels.append((i, label))

        plot_widget.getAxis('bottom').setTicks([hour_labels])
        plot_widget.setXRange(0, 23)
        
        # plot_widget.addItem(bg)

        plot_widget.setLabel('left', 'Total Sales')
        plot_widget.setLabel('bottom', 'Hour of Day')
        plot_widget.setTitle("Hourly Sales Today")
        plot_widget.setBackground("w")
        plot_widget.showGrid(x=True, y=True)
        
        
        #################################################
        ####            Monthly Sales         ###########
        
        monthly_sale_label = QLabel("Monthly Sale - By Day")
        self.layout.addWidget(monthly_sale_label)

        
        days = list(range(1, 32))  # Days 1 to 31
        monthly_sales = self.get_monthly_sales_data()
        month_sales = [monthly_sales[day - 1] for day in range(1, 32)]
        
        print("Days:", len(days))
        print("Sales:", len(month_sales))

        
        # Plot widget
        monthly_plot = pg.PlotWidget()
        monthly_plot.setStyleSheet("""
            background-color: #f0f0f0;      /* light gray background */
            border: 2px solid #3498db;     /* blue border */
        """)
        
        
        # Create a PlotDataItem (line plot) with markers
        monthly_plot.plot(days, month_sales,  pen=pg.mkPen("#000000", width=2), symbol='o', symbolSize=8, symbolBrush='b')
        monthly_plot.getAxis('bottom').setTicks([[(i, str(i)) for i in range(1, 32)]])
        monthly_plot.setXRange(0, 31)

    
        # monthly_plot.addItem(bg)

        monthly_plot.setLabel('left', 'Daily Sales')
        monthly_plot.setLabel('bottom', 'Day')
        monthly_plot.setTitle("Monthly Sales")
        monthly_plot.setBackground("w")
        monthly_plot.showGrid(x=True, y=True)
        
        self.layout.addWidget(monthly_plot)
        

        # Spacer and CSS
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)

        
        
       
        
        # set stylesheets
        self.setStyleSheet(load_stylesheets())
        




    def showEvent(self, event):
        
        print("Showing Dashboard Widget")
        
        super().showEvent(event)
        
        
        

    
    
    
 



        
        
        
    
    
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



        
        
        


