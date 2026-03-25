from PySide6.QtWidgets import QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QGridLayout, QPushButton, QLabel, QDialog, QComboBox, QFrame, QSpacerItem
from PySide6.QtCore import Qt, QFile, QDate, Signal, QTimer
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





class DailySession(QWidget):
    
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # main vertical layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Daily Sessions", objectName="SectionTitle")
        self.dashboard_btn = QPushButton("See Dashboard", objectName="TopRightButton")
        self.dashboard_btn.setCursor(Qt.PointingHandCursor)
        self.dashboard_btn.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.dashboard_btn)
        
        
        self.layout.addLayout(header_layout)
        
        
        
        self.add_current_session_section()
        
        self.update_session_buttons()
        
        
        # push content to top
        self.layout.addStretch()
        
        # set stylesheets
        self.setStyleSheet(load_stylesheets())
        





    def get_open_session(self):

        query = QSqlQuery()
        query.prepare("""
            SELECT 
                id,
                session_date,
                opening_cash,
                opened_at,
                system_cash,
                actual_cash,
                withdrawal,
                cash_difference,
                status
            FROM daily_session
            WHERE status = 'open'
            LIMIT 1
        """)

        if query.exec() and query.next():

            session_data = {
                "id": query.value(0),
                "session_date": query.value(1),
                "opening_cash": query.value(2),
                "opened_at": query.value(3),
                "system_cash": query.value(4),
                "actual_cash": query.value(5),
                "withdrawal": query.value(6),
                "cash_difference": query.value(7),
                "status": query.value(8),
            }

            return session_data

        return None


    
    def open_session_dialog(self):
        
        

        dialog = QDialog(self)
        dialog.setWindowTitle("Open Daily Session")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        heading = QLabel("Open Daily Session")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("font-size:16px; font-weight:bold;")
        layout.addWidget(heading)

        form = QGridLayout()

        date_edit = QLineEdit()
        date_edit.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        date_edit.setReadOnly(True)

        carry_forward_edit = QLineEdit()
        carry_forward_edit.setReadOnly(True)
        carry_forward_edit.setText(str(self.get_previous_balance() or 0))

        added_cash_edit = QLineEdit()
        added_cash_edit.setPlaceholderText("Enter added cash")
        added_cash_edit.setText("0")

        opening_cash_edit = QLineEdit()
        opening_cash_edit.setReadOnly(True)

        def update_opening():
            try:
                carry = float(carry_forward_edit.text() or 0)
                added = float(added_cash_edit.text() or 0)
                opening_cash_edit.setText(str(carry + added))
            except ValueError:
                opening_cash_edit.setText("0")

        added_cash_edit.textChanged.connect(update_opening)
        update_opening()

        form.addWidget(QLabel("Date"), 0, 0)
        form.addWidget(date_edit, 0, 1)

        form.addWidget(QLabel("Carry Forward"), 1, 0)
        form.addWidget(carry_forward_edit, 1, 1)

        form.addWidget(QLabel("Added Cash"), 2, 0)
        form.addWidget(added_cash_edit, 2, 1)

        form.addWidget(QLabel("Opening Cash"), 3, 0)
        form.addWidget(opening_cash_edit, 3, 1)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        open_btn = QPushButton("Open Session")
        cancel_btn = QPushButton("Cancel")

        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        

        cancel_btn.clicked.connect(dialog.reject)

        def handle_open():
            try:
                float(added_cash_edit.text() or 0)
                float(opening_cash_edit.text() or 0)
                dialog.accept()
            except ValueError:
                return

        open_btn.clicked.connect(handle_open)

        if dialog.exec() == QDialog.Accepted:
            return {
                "session_date": date_edit.text().strip(),
                "carry_forward": float(carry_forward_edit.text() or 0),
                "added_cash": float(added_cash_edit.text() or 0),
                "opening_cash": float(opening_cash_edit.text() or 0),
            }

        return None

    
    
    
    
    def get_previous_balance(self):

        query = QSqlQuery()
        query.prepare("""
            SELECT 
                actual_cash, withdraw_amount
            FROM daily_session
            WHERE status = 'closed'
            ORDER BY id DESC
            LIMIT 1
        """)

        if query.exec() and query.next():
            
            actual_cash = query.value(0) or 0
            withdraw_amount = query.value(1) or 0
            
            return max(0, actual_cash - withdraw_amount)

        return 0
    
    
    
    def get_cash_expenses(self):

        cash_expenses = 0.0

        query = QSqlQuery()
        query.prepare("""
            SELECT COALESCE(SUM(e.amount), 0)
            FROM expense e
            JOIN daily_session s ON e.session_id = s.id
            WHERE s.status = 'open'
            AND e.payment_method = 'Cash'
        """)

        if query.exec() and query.next():
            cash_expenses = float(query.value(0) or 0)

        return cash_expenses
    
    
    def close_session_dialog(self, session_data):
        
        # You should calculate system_cash before this
        session_id, inflows, outflows = self.get_current_session_cash_flows()
        print("Session Data is: ", session_id, inflows, outflows)
        
        
        # get opening cash
        opening_cash = self.get_opening_cash()
        
        
        # get expenses
        cash_expenses = self.get_cash_expenses()
        
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Close Daily Session")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        heading = QLabel("Close Daily Session")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("font-size:16px; font-weight:bold;")
        layout.addWidget(heading)

        form = QGridLayout()

        opening_cash_edit = QLineEdit()
        opening_cash_edit.setReadOnly(True)
        opening_cash_edit.setText(str(session_data.get("opening_cash", 0)))

        system_cash_edit = QLineEdit()
        system_cash_edit.setReadOnly(True)
        system_cash_edit.setText(str(session_data.get("system_cash", 0)))

        actual_cash_edit = QLineEdit()
        actual_cash_edit.setPlaceholderText("Enter counted cash")

        withdraw_edit = QLineEdit()
        withdraw_edit.setPlaceholderText("Enter withdraw amount")
        withdraw_edit.setText("0")

        difference_edit = QLineEdit()
        difference_edit.setReadOnly(True)

        def update_difference():
            try:
                system = float(system_cash_edit.text() or 0)
                actual = float(actual_cash_edit.text() or 0)
                diff = actual - system
                difference_edit.setText(str(diff))
            except:
                difference_edit.setText("0")

        actual_cash_edit.textChanged.connect(update_difference)
        update_difference()

        form.addWidget(QLabel("Opening Cash"), 0, 0)
        form.addWidget(opening_cash_edit, 0, 1)

        form.addWidget(QLabel("System Cash"), 1, 0)
        form.addWidget(system_cash_edit, 1, 1)

        form.addWidget(QLabel("Actual Cash"), 2, 0)
        form.addWidget(actual_cash_edit, 2, 1)

        form.addWidget(QLabel("Withdraw Amount"), 3, 0)
        form.addWidget(withdraw_edit, 3, 1)

        form.addWidget(QLabel("Difference"), 4, 0)
        form.addWidget(difference_edit, 4, 1)

        layout.addLayout(form)
        
        
        opening_cash_edit.setText(str(opening_cash))
        
        # calculate system cash
        system_cash = opening_cash + inflows - outflows - cash_expenses
        
        system_cash_edit.setText(str(system_cash))

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close Session")
        cancel_btn = QPushButton("Cancel")

        btn_layout.addWidget(close_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        cancel_btn.clicked.connect(dialog.reject)

        def handle_close():
            try:
                float(actual_cash_edit.text() or 0)
                float(withdraw_edit.text() or 0)
                dialog.accept()
            except ValueError:
                return

        close_btn.clicked.connect(handle_close)

        if dialog.exec() == QDialog.Accepted:
            return {
                "system_cash": float(system_cash),
                "actual_cash": float(actual_cash_edit.text() or 0),
                "withdraw_amount": float(withdraw_edit.text() or 0),
                "cash_difference": float(difference_edit.text() or 0),
            }

        return None  
        
        
    
    def get_opening_cash(self):
        
        opening_cash = 0.0

        query = QSqlQuery()
        query.prepare("""
            SELECT opening_cash
            FROM daily_session
            WHERE status = 'open'
            ORDER BY id DESC
            LIMIT 1
        """)

        if query.exec() and query.next():
            opening_cash = float(query.value(0) or 0)

        return opening_cash    
        
        
        
    def handle_open_session(self):

        print("Handling the opening of session")
        session_data = self.open_session_dialog()

        if not session_data:
            return

        query = QSqlQuery()
        query.prepare("""
            INSERT INTO daily_session (
                session_date,
                opening_cash,
                status
            )
            VALUES (?, ?, 'open')
        """)
        query.addBindValue(session_data["session_date"])
        query.addBindValue(session_data["opening_cash"])

        if not query.exec():
            print("Error opening session:", query.lastError().text())
            return

        self.update_session_buttons()    
        print("Session opened successfully")
        
    
    def handle_close_session(self):

        session = self.get_open_session()
        
        if not session:
            return
        

        result = self.close_session_dialog(session)

        if not result:
            return

        query = QSqlQuery()
        query.prepare("""
            UPDATE daily_session
            SET 
                system_cash = ?,
                actual_cash = ?,
                withdrawal = ?,
                cash_difference = ?,
                closed_at = CURRENT_TIMESTAMP,
                status = 'closed'
            WHERE id = ?
        """)

        query.addBindValue(result["system_cash"])
        query.addBindValue(result["actual_cash"])
        query.addBindValue(result["withdraw_amount"])
        query.addBindValue(result["cash_difference"])
        query.addBindValue(session["id"])

        if not query.exec():
            print("Error closing session:", query.lastError().text())
            return

        self.update_session_buttons()
    
    
    
    def add_current_session_section(self):
        
        # ---------------------------
        # Session Section Frame
        # ---------------------------
        session_frame = QFrame()
        session_frame.setObjectName("sectionCard")

        session_layout = QVBoxLayout(session_frame)
        session_layout.setContentsMargins(5, 10, 5, 10)
        session_layout.setSpacing(8)

        # Top Row Layout
        top_row = QHBoxLayout()
        top_row.setSpacing(15)

        self.session_msg = QLabel("")
        self.open_session = QPushButton("Open Day", objectName="TopRightButton")
        self.close_session = QPushButton("Close Day", objectName="TopRightButton")
        
        
        self.open_session.clicked.connect(self.handle_open_session)
        self.close_session.clicked.connect(self.handle_close_session)
        
        # Add widgets
        top_row.addWidget(self.session_msg, 10)
        top_row.addWidget(self.open_session, 1)
        top_row.addWidget(self.close_session, 1)
        
        
        spacer = QLabel()
        top_row.addWidget(spacer)
           
        session_layout.addLayout(top_row)

        # Add frame to main layout
        self.layout.addWidget(session_frame)
        
        
        
        
    
    def update_session_buttons(self):

        session = self.get_open_session()

        if session:  # session is open
            self.open_session.hide()
            self.close_session.show()
            self.session_msg.setText("Session is OPEN")
        else:        # no open session
            self.open_session.show()
            self.close_session.hide()
            self.session_msg.setText("No active session")
    
    
    
    

    def get_current_session_cash_flows(self):
        
        session_id = None
        inflows = 0.0
        outflows = 0.0

        # Get current open session
        session_query = QSqlQuery()
        session_query.prepare("""
            SELECT id
            FROM daily_session
            WHERE status = 'open'
            ORDER BY id DESC
            LIMIT 1
        """)

        if not (session_query.exec() and session_query.next()):
            return None, 0.0, 0.0

        session_id = int(session_query.value(0))

        def fetch_sums(table_name):
            query = QSqlQuery()
            query.prepare(f"""
                SELECT
                    COALESCE(SUM(received), 0),
                    COALESCE(SUM(paid), 0)
                FROM {table_name}
                WHERE session_id = ?
                AND payment_method = 'Cash'
            """)
            query.addBindValue(session_id)

            if query.exec() and query.next():
                received = float(query.value(0) or 0)
                paid = float(query.value(1) or 0)
                return received, paid

            return 0.0, 0.0

        customer_received, customer_paid = fetch_sums("customer_transaction")
        supplier_received, supplier_paid = fetch_sums("supplier_transaction")

        inflows = customer_received + supplier_received
        outflows = customer_paid + supplier_paid

        return session_id, inflows, outflows







