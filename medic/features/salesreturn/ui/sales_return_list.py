from PySide6.QtWidgets import QWidget, QComboBox, QGridLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal, QDate
from functools import partial

from medic.services.return_read_service import fetch_sales_return_list_rows
from medic.utilities.stylus import load_stylesheets
from medic.utilities.table_helpers import centered_cell_widget, style_table_action_button




class SalesReturnListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        layout = QVBoxLayout(self)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)


        heading = QLabel("Sales Return List", objectName='SectionTitle')
        self.addSalesReturn = QPushButton('Add Sales Return', objectName='TopRightButton')
        self.addSalesReturn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        grid_layout.addWidget(heading, 0,0)
        grid_layout.addWidget(self.addSalesReturn, 0,2)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setAlignment(self.addSalesReturn, Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(grid_widget)

        

        self.table = QTableWidget()
        
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Id", "Customer", "Sales Man", "Date", "Detail"
        ])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.setColumnWidths(table, [0.1, 0.4, 0.3, 0.2, 0.2]) 

        self.table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setFixedHeight(30)

        header.setStyleSheet("""
                background-color: #333;
                color: white;              
                font-weight: 600;
            
        """)

        
        layout.addWidget(self.table)
        self.setLayout(layout)

        
        self.setStyleSheet(load_stylesheets())



    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_sales_into_table()
        



    def load_sales_into_table(self):
        rows = fetch_sales_return_list_rows()
        self.table.setRowCount(0)

        for row, data in enumerate(rows):
            self.table.insertRow(row)
            return_id = data["id"]
            self.table.setItem(row, 0, QTableWidgetItem(str(return_id)))
            self.table.setItem(row, 1, QTableWidgetItem(data["customer_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["salesman_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(data["creation_date"]))

            detail = style_table_action_button(QPushButton('Details'))
            self.table.setCellWidget(row, 4, centered_cell_widget(detail))
            detail.clicked.connect(partial(self.detailpagesignal.emit, return_id))
        




            
        
