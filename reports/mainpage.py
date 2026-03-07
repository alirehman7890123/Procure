
from PySide6.QtWidgets import QWidget, QPushButton, QComboBox, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt,QDate
from PySide6.QtSql import  QSqlQuery
from PySide6.QtGui import QCursor
from datetime import date
from functools import partial
import pyqtgraph as pg
import sys
from utilities.stylus import load_stylesheets
from reports import report_service


class MainReportsPage(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        
        
        # main vertical layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Sales Reports", objectName="SectionTitle")
        
        duration_combo = QComboBox()
        duration_combo.addItems(['Today', 'Past Week', 'Past Month', 'Past Year', 'All'])
        
        duration_combo.currentIndexChanged.connect(self.on_duration_changed)
        
        
        duration_combo.setCursor(Qt.PointingHandCursor)
        duration_combo.setFixedWidth(200)
        
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(duration_combo)
        
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
        
        
        
        card_row = QHBoxLayout()
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        sales_card = QWidget()
        sales_card.setObjectName("card")
        sales_card.setMinimumWidth(250)
        sales_card.setFixedHeight(150)
        sales_card.setStyleSheet("background-color: #004c00; border-radius: 5px; color: #fff;")
        
        sales_card.setSizePolicy(policy)
        
        sales_card_layout = QVBoxLayout(sales_card)
        
        
        
        sales_card_title = QLabel("Total Sales")
        sales_card_title.setObjectName("cardTitle")
        sales_card_title.setStyleSheet("font-size: 16px;")
        
        self.sales_card_data = QLabel("0.00")
        self.sales_card_data.setObjectName("cardData")
        self.sales_card_data.setStyleSheet("font-size: 40px; margin-bottom: 15px;")
        
        sales_card_layout.addWidget(sales_card_title)
        sales_card_layout.addWidget(self.sales_card_data)


        card2 = QWidget()
        
        card2.setObjectName("card")
        card2.setMinimumWidth(250)
        card2.setFixedHeight(150)
        card2.setStyleSheet("background-color: #004c00; border-radius: 5px; color: #fff;")
        card2.setSizePolicy(policy)
        
        card2_layout = QVBoxLayout(card2)
        
        card2_title = QLabel("Purchase Info")
        card2_title.setObjectName("cardTitle")
        card2_title.setStyleSheet("font-size: 16px;")
        
        self.card2_data = QLabel("0.00")
        self.card2_data.setObjectName("cardData")
        self.card2_data.setStyleSheet("font-size: 40px; margin-bottom: 15px;")
        
        card2_layout.addWidget(card2_title)
        card2_layout.addWidget(self.card2_data)
        
        
        
        card3 = QWidget()
        
        card3.setObjectName("card")
        card3.setMinimumWidth(250)
        card3.setFixedHeight(150)
        card3.setStyleSheet("background-color: #004c00; border-radius: 5px; color: #fff;")
        card3.setSizePolicy(policy)
        
        card3_layout = QVBoxLayout(card3)
        
        card3_title = QLabel("Expenses")
        card3_title.setObjectName("cardTitle")
        card3_title.setStyleSheet("font-size: 16px;")
        
        self.card3_data = QLabel("0.00")
        self.card3_data.setObjectName("cardData")
        self.card3_data.setStyleSheet("font-size: 40px; margin-bottom: 15px;")
        
        card3_layout.addWidget(card3_title)
        card3_layout.addWidget(self.card3_data)
        
        card_row.addWidget(sales_card, 1)
        card_row.addWidget(card2, 1)
        card_row.addWidget(card3, 1)
        
        card_row.setAlignment(Qt.AlignLeft)
        self.layout.addLayout(card_row)
        
        self.layout.addSpacing(20)
        
        
        
        
        # revenue card
        revenue_card = self.create_revenue_card()
        self.layout.addWidget(revenue_card)
        
        
        # subheading for stock
        stock_heading = QLabel('Stock Information', objectName="SectionTitle")
        self.layout.addWidget(stock_heading)
        
        
        stock_row = QHBoxLayout()
        
        # stock-cost card
        stock_cost_card = self.create_stock_cost_card()
        stock_row.addWidget(stock_cost_card)
        
        # low and expired count
        stock_count_card = self.create_stock_count_card()
        stock_row.addWidget(stock_count_card)
        
        self.layout.addLayout(stock_row)
        
        
        
        
        supplier_dues_label = QLabel('Supplier Dues', objectName="SectionTitle")
       
        supplier_card = self.create_supplier_card()
        self.layout.addWidget(supplier_dues_label)
        self.layout.addWidget(supplier_card)
        
        
        
        
        
        customer_dues_label = QLabel('Customer Dues', objectName="SectionTitle")
        
        customer_card = self.create_customer_card()
        self.layout.addWidget(customer_dues_label)
        self.layout.addWidget(customer_card)
        
        
        
        
        
        self.layout.addStretch()
        
        self.setStyleSheet(load_stylesheets())
        
        # print("Showing Reports")

        # layout = QGridLayout()
        # layout.setContentsMargins(0,0,0,0)
        # layout.setSpacing(0)

        # heading = QLabel("Reports", objectName='myheading')
        # self.transactionlist = QPushButton('Reports List', objectName='supplierlist')
        # self.transactionlist.setCursor(Qt.PointingHandCursor)

        # layout.addWidget(heading, 0,0)
        # layout.addWidget(self.transactionlist, 0,2)

        # today_sale_label = QLabel("Today's Sale - By Hour")
        # layout.addWidget(today_sale_label, 1, 0)
        
        # # Plot widget
        # plot_widget = pg.PlotWidget()
        # layout.setContentsMargins(30, 30, 30, 30)  # left, top, right, bottom margins around all widgets in the layout
        # layout.setSpacing(10)  # space between widgets

        # plot_widget.setStyleSheet("""
        #     background-color: #f0f0f0;      /* light gray background */
        #     border: 2px solid #3498db;     /* blue border */
        # """)


        # layout.addWidget(plot_widget, 2, 0, 1, 3)

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
        # layout.addWidget(monthly_sale_label, 4, 0)

        
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
        
        # layout.addWidget(monthly_plot, 5, 0, 1, 3)
        

        # # Spacer and CSS
        # spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # layout.addItem(spacer, 13, 0)

        # self.setStyleSheet(load_stylesheets())
        
        
        # self.setLayout(layout)



    def create_stock_cost_card(self):
        
        # Create the card container
        card = QFrame()
        
        # Apply Brown Background and Rounded Corners
        card.setStyleSheet("""
            QFrame {
                background-color: #420000; /* SaddleBrown */
                border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        
        
        
        card_layout = QVBoxLayout(card)
        
        
        first_line_layout = QHBoxLayout()
        
        estimate_label = QLabel("Estimate Opening Stock Cost")
        self.estimate_cost = QLabel()
        
        first_line_layout.addWidget(estimate_label, 3)
        first_line_layout.addWidget(self.estimate_cost, 1)
        
        card_layout.addLayout(first_line_layout)
        
        
        second_line_layout = QHBoxLayout()
        
        known_stock_cost = QLabel("Known Stock Cost")
        self.known_stock_cost_data = QLabel()
        
        second_line_layout.addWidget(known_stock_cost, 3)
        second_line_layout.addWidget(self.known_stock_cost_data, 1)
        
        card_layout.addLayout(second_line_layout)
        
        # insert data
        
        opening_cost = report_service.ReportService().get_opening_estimate_amount()
        self.estimate_cost.setText(f"{opening_cost:,.2f}")
        
        purchased_cost = report_service.ReportService().get_total_purchase_amount()
        self.known_stock_cost_data.setText(f"{purchased_cost:.2f}")
        
        
        return card
    
    
    
    
    def create_stock_count_card(self):
        # Create the card container
        card = QFrame()
        
        # Apply Brown Background and Rounded Corners
        card.setStyleSheet("""
            QFrame {
                background-color: #420000; /* SaddleBrown */
                border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        
        
        card_layout = QVBoxLayout(card)
        
        
        first_line_layout = QHBoxLayout()
        
        expiry_count_label = QLabel("Near Expiry Count")
        self.expiry_count = QPushButton()
        self.expiry_count.setStyleSheet("color: #333; background-color: #ccc;")
        
        self.expiry_count.clicked.connect(self.show_near_expiry_dialog)
        
        
        first_line_layout.addWidget(expiry_count_label, 3)
        first_line_layout.addWidget(self.expiry_count, 1)
        
        card_layout.addLayout(first_line_layout)
        
        
        second_line_layout = QHBoxLayout()
        
        low_stock_count_label = QLabel("Low Stock Count")
        self.low_stock_count = QPushButton()
        self.low_stock_count.setStyleSheet("color: #333; background-color: #ccc;")
        
        self.low_stock_count.clicked.connect(self.show_low_stock_dialog)
        
        second_line_layout.addWidget(low_stock_count_label, 3)
        second_line_layout.addWidget(self.low_stock_count, 1)
        
        card_layout.addLayout(second_line_layout)
        
        
        # insert data
        count = report_service.ReportService().get_stock_count_alerts()

        near_expiry = count['near_expiry_batches']
        low_stock = count['low_stock_products']
        
        self.expiry_count.setText(f"{near_expiry:.2f}")
        self.low_stock_count.setText(f"{low_stock:.2f}")
        
        
        return card
    
    
    
    
    def create_supplier_card(self):
        # Create the card container
        card = QFrame()
        
        # Apply Brown Background and Rounded Corners
        card.setStyleSheet("""
            QFrame {
                background-color: #003e4c;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        
        # 2. Create the VBoxLayout for the 2 lines of info
        card_layout = QHBoxLayout(card)
        
        pay_label = QLabel(f'You have to PAY')
        self.supplier_payable = QLabel()
        
        spacer_label = QLabel()
        
        receive_label = QLabel(f'You have to RECEIVE')
        self.supplier_receivable = QLabel()
        
        
        card_layout.addWidget(pay_label, 3)
        card_layout.addWidget(self.supplier_payable, 1)
        
        card_layout.addWidget(spacer_label, 4)
        
        card_layout.addWidget(receive_label, 3)
        card_layout.addWidget(self.supplier_receivable, 1)
        
        
        payable, receiveable = report_service.ReportService().get_supplier_balances()

        self.supplier_payable.setText(f"{payable:,.2f}")
        self.supplier_receivable.setText(f"{receiveable:,.2f}")

        
        return card
    
    
    
    def create_customer_card(self):
        # Create the card container
        card = QFrame()
        
        
        card.setStyleSheet("""
            QFrame {
                background-color: #4c0033;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        
        # 2. Create the VBoxLayout for the 2 lines of info
        card_layout = QHBoxLayout(card)
        
        pay_label = QLabel(f'You have to PAY')
        self.customer_payable = QLabel()
        
        spacer_label = QLabel()
        
        receive_label = QLabel(f'You have to RECEIVE')
        self.customer_receivable = QLabel()
        
        
        card_layout.addWidget(pay_label, 3)
        card_layout.addWidget(self.customer_payable, 1)

        card_layout.addWidget(spacer_label, 4)

        card_layout.addWidget(receive_label, 3)
        card_layout.addWidget(self.customer_receivable, 1)
        
        receivable, payable = report_service.ReportService().get_customer_balances()


        self.customer_payable.setText(f"{payable:,.2f}")
        self.customer_receivable.setText(f"{receivable:,.2f}")
        
        
        
        
        return card
    
    
    
    def create_revenue_card(self):
        
        
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #004e00;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
        """)
    

        card_layout = QHBoxLayout(card)
        
        known_revenue_label = QLabel("Known Revenue : ")
        self.known_revenue_data = QLabel()
        
        profit_label = QLabel("Known Profit: ")
        self.profit_data = QLabel()
        
        unknown_revenue_label = QLabel("Opening Stock Revenue: ")
        self.unknown_revenue_data = QLabel()
        
        
        
        card_layout.addWidget(known_revenue_label, 3)
        card_layout.addWidget(self.known_revenue_data, 1)
        
        spacer_label_1 = QLabel()
        card_layout.addWidget(spacer_label_1, 1)
        
        card_layout.addWidget(profit_label, 2)
        card_layout.addWidget(self.profit_data, 1)
        
        spacer_label_1 = QLabel()
        card_layout.addWidget(spacer_label_1, 1)
    
        card_layout.addWidget(unknown_revenue_label, 3)
        card_layout.addWidget(self.unknown_revenue_data, 1)
        
        
        
        revenue_known, total_cogs, gross_profit, revenue_unknown = report_service.ReportService().get_detailed_revenue("today")

        self.known_revenue_data.setText(f"{revenue_known:.2f}")
        self.profit_data.setText(f"{gross_profit:.2f}")
        self.unknown_revenue_data.setText(f"{revenue_unknown:.2f}")
    

        return card
    
    
    
    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Showing Reports page")
        
        
        
        
        

        
        
        
    

    def get_today_data(self):
        
        print("Going to Populate Summary Totals for today")
        today = QDate.currentDate().toString("yyyy-MM-dd")
        totals = report_service.ReportService().get_summary_totals(today, today)
        
        self.sales_card_data.setText(str(round(totals["sales"], 2)))
        self.card2_data.setText(str(round(totals["purchase"], 2)))
        self.card3_data.setText(str(round(totals["expense"], 2)))
        
    
    
    def get_past_seven_days_data(self):
        
        print("Going to Populate Summary Totals for past 7 days")
        today = QDate.currentDate()
        seven_days_ago = today.addDays(-6)  # Include today, so -6
        date_from = seven_days_ago.toString("yyyy-MM-dd")
        date_to = today.toString("yyyy-MM-dd")

        totals = report_service.ReportService().get_summary_totals(date_from, date_to)
        
        print("Totals for past 7 days:", totals)

        self.sales_card_data.setText(str(round(totals["sales"], 2)))
        self.card2_data.setText(str(round(totals["purchase"], 2)))
        self.card3_data.setText(str(round(totals["expense"], 2)))
    
    
        
        


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




    def on_duration_changed(self, index):
        # Map combo box selection to your method's duration parameter
        duration_map = {
            0: "today",
            1: "week",
            2: "month",
            3: "year",
            4: "all",
        }
        duration_key = duration_map.get(index, "today")

        total_sales, total_invoices = report_service.ReportService().get_sales_summary(duration_key)
        self.sales_card_data.setText(f"{total_sales:.2f}")
        # self.card1_bottom.setText(f"{total_invoices} Sales Invoice(s) ")
        
        
        total_purchase, invoice_count = report_service.ReportService().get_purchase_summary(duration_key)
        self.card2_data.setText(f"{total_purchase:.2f}")
        # self.card2_bottom.setText(f"{invoice_count} Purchase Invoice(s) ")
        
        
        total_expenses, num_records = report_service.ReportService().get_expense_summary(duration_key)
        self.card3_data.setText(f"{total_expenses:.2f}")
        # self.card3_bottom.setText(f"{num_records} Expense(s) ")
        

        
        revenue_known, total_cogs, gross_profit, revenue_unknown = report_service.ReportService().get_detailed_revenue(duration_key)

        self.known_revenue_data.setText(f"{revenue_known:.2f}")
        self.profit_data.setText(f"{gross_profit:.2f}")
        self.unknown_revenue_data.setText(f"{revenue_unknown:.2f}")






    def show_near_expiry_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
        from PySide6.QtCore import Qt
        from PySide6.QtSql import QSqlQuery
        from PySide6.QtGui import QColor

        dialog = QDialog(self)
        dialog.setWindowTitle("Near Expiry Batches (Next 60 Days)")
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Product", "Batch No", "Expiry Date", "Days Left", "Qty Remaining"
        ])
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)

        query = QSqlQuery()

        sql = """
            SELECT 
                p.display_name,
                b.batch_no,
                b.expiry_date,
                CASE 
                    WHEN b.expiry_date IS NOT NULL 
                    THEN CAST(julianday(b.expiry_date) - julianday('now') AS INTEGER)
                    ELSE NULL
                END AS days_left,
                b.quantity_remaining
            FROM batch b
            JOIN product p ON p.id = b.product_id
            WHERE b.quantity_remaining > 0
            AND (
                b.expiry_date IS NULL
                OR DATE(b.expiry_date) <= DATE('now', '+60 days')
            )
            ORDER BY 
                CASE WHEN b.expiry_date IS NULL THEN 1 ELSE 0 END,
                b.expiry_date ASC
        """

        if not query.exec(sql):
            print("Near expiry query failed:", query.lastError().text())
            dialog.exec()
            return

        rows = []
        while query.next():
            rows.append([
                query.value(0),  # product
                query.value(1),  # batch
                query.value(2),  # expiry
                query.value(3),  # days_left
                query.value(4),  # qty
            ])

        table.setRowCount(len(rows))

        for row_index, row_data in enumerate(rows):
            for col_index, value in enumerate(row_data):
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

            # Highlight if expiry exists AND < 30 days
            # days_left = row_data[3]
            
            # if days_left is not None and days_left < 30:
            #     for col in range(table.columnCount()):
            #         table.item(row_index, col).setBackground(QColor("yellow"))

        table.resizeColumnsToContents()
        dialog.exec()






    def show_low_stock_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
        from PySide6.QtCore import Qt
        from PySide6.QtSql import QSqlQuery

        dialog = QDialog(self)
        dialog.setWindowTitle("Out of Stock Products")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([
            "Product", "Current Stock"
        ])
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)

        query = QSqlQuery()

        sql = """
            SELECT 
                p.display_name,
                IFNULL(SUM(b.quantity_remaining), 0) AS total_stock
            FROM product p
            LEFT JOIN batch b ON b.product_id = p.id
            GROUP BY p.id
            HAVING total_stock = 0
            ORDER BY p.display_name ASC
        """

        if not query.exec(sql):
            print("Low stock query failed:", query.lastError().text())
            dialog.exec()
            return

        rows = []
        while query.next():
            rows.append([
                query.value(0),
                query.value(1)
            ])

        table.setRowCount(len(rows))

        for row_index, row_data in enumerate(rows):
            for col_index, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row_index, col_index, item)

        table.resizeColumnsToContents()
        dialog.exec()




