
from PySide6.QtWidgets import QWidget, QPushButton, QGridLayout, QLabel, QToolTip, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt,QDate
from PySide6.QtSql import  QSqlQuery
from PySide6.QtGui import QCursor
from datetime import date
import pyqtgraph as pg
import sys
from utilities.stylus import load_stylesheets



class MainReportsPage(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        
        
        print("Showing Reports")

        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        heading = QLabel("Reports", objectName='myheading')
        self.transactionlist = QPushButton('Reports List', objectName='supplierlist')
        self.transactionlist.setCursor(Qt.PointingHandCursor)

        layout.addWidget(heading, 0,0)
        layout.addWidget(self.transactionlist, 0,2)

        today_sale_label = QLabel("Today's Sale - By Hour")
        layout.addWidget(today_sale_label, 1, 0)
        
        # Plot widget
        plot_widget = pg.PlotWidget()
        layout.setContentsMargins(30, 30, 30, 30)  # left, top, right, bottom margins around all widgets in the layout
        layout.setSpacing(10)  # space between widgets

        plot_widget.setStyleSheet("""
            background-color: #f0f0f0;      /* light gray background */
            border: 2px solid #3498db;     /* blue border */
        """)


        layout.addWidget(plot_widget, 2, 0, 1, 3)

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
        layout.addWidget(monthly_sale_label, 4, 0)

        
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
        
        layout.addWidget(monthly_plot, 5, 0, 1, 3)
        

        # Spacer and CSS
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer, 13, 0)

        self.setStyleSheet(load_stylesheets())
        
        
        self.setLayout(layout)




    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Showing Reports page")
        
        self.get_hourly_sales_data()
        self.get_monthly_sales_data()




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
        query.prepare("""
            SELECT
                day::int,
                COALESCE(SUM(total), 0) AS total_sales
            FROM
                generate_series(1, 31) AS day
            LEFT JOIN
                sales ON EXTRACT(DAY FROM creation_date) = day
                    AND date_trunc('month', creation_date) = date_trunc('month', CURRENT_DATE)
            GROUP BY day
            ORDER BY day;
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


