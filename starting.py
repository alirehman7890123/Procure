
import os

# Fix Wayland compositor issue (especially on Chromebooks / Crostini)
if os.environ.get("WAYLAND_DISPLAY"):
    # Wayland detected — but sometimes it's fake or broken
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
else:
    # Force X11 if Wayland isn't available
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

# Fallback if still broken
if not os.environ.get("QT_QPA_PLATFORMTHEME"):
    os.environ["QT_QPA_PLATFORMTHEME"] = "qt6ct"


from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QHBoxLayout, QVBoxLayout, QLabel,QLineEdit

from utilities.database import SQLiteConnectionManager, QSqlDatabase
from utilities.mylogin import MainWindow
import bcrypt
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtSql import QSqlQuery
from PySide6.QtCore import QDate, QSettings, QTimer

import shutil, subprocess

def check_xcb_support():
    print("checking for missing libraries")
    missing = []
    for lib in ["libxcb-cursor.so.0", "libxkbcommon-x11.so.0"]:
        if not shutil.which("ldd"): continue
        try:
            result = subprocess.run(["ldd", f"/usr/lib/x86_64-linux-gnu/qt6/plugins/platforms/libqxcb.so"], capture_output=True, text=True)
            if lib in result.stdout and "not found" in result.stdout:
                missing.append(lib)
        except FileNotFoundError:
            pass
    if missing:
        print("⚠️ Missing XCB libraries:", ", ".join(missing))
        print("Run:")
        print("sudo apt install libxcb-cursor0 libxkbcommon-x11-0")



class AuthWindow(QMainWindow):


    def __init__(self):

        super().__init__()
        self.settings = QSettings("procure", "procure_medics")  # unique identifiers
        
        check_xcb_support()
        
        self.close()
        
        self.setWindowTitle('ProCure Medical - Login')
        screen_geometry = QApplication.primaryScreen().geometry()
        
        width = screen_geometry.width()
        height = screen_geometry.height()

        self.setGeometry(0,0, width, height)
        self.setStyleSheet('color: #333;')

        central_widget = QWidget()
        central_layout = QHBoxLayout()
        central_widget.setLayout(central_layout)
        central_layout.setContentsMargins(0,0,0,0)
        central_layout.setSpacing(0)
        
        
        companyinfo = QWidget()
        companyinfo_layout = QVBoxLayout()
        companyinfo.setLayout(companyinfo_layout)
        companyinfo_layout.setContentsMargins(0,0,0,0)
        companyinfo_layout.setSpacing(0)
        companyinfo.setMinimumWidth(600)
        
        companyinfo.setStyleSheet("background-color: #000755;") 
        
        
        
        authinfo = QWidget()
        auth_layout = QVBoxLayout()
        authinfo.setLayout(auth_layout)
        auth_layout.setContentsMargins(60,100,50,30)
        auth_layout.setSpacing(0)
        authinfo.setMinimumWidth(600)
        
        authinfo.setStyleSheet("background-color: #fff;")
        
        loginheading = QLabel('Login to Continue')
        loginheading.setStyleSheet("font-size: 20px; font-weight: 500; margin-bottom: 50px;")
        
        
        self.username = QLineEdit()
        self.username.setPlaceholderText('Username')
        self.username.setStyleSheet('width: 300px; padding: 5px 8px; margin-bottom: 20px;')
        
        

        self.password = QLineEdit()
        self.password.setPlaceholderText('Password')
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet('width: 300px; padding: 5px 8px; margin-bottom: 30px;')


        login_button = QPushButton('Login')
        button_styles = """
        
        
            QPushButton {
                padding: 15px 0;
                background-color: #000755;
                padding-left: 30px; 
                font-family: roboto;
                border:2px solid #333;
                color: #999; 
                font-weight: 300; 
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #fff;
                color: #4B0082;
                font-weight: 600;
                
            }
            QPushButton:pressed {
                background-color: #000755;
                color: #fff;
            }
            
        """
        
        login_button.setStyleSheet(button_styles)
        login_button.clicked.connect(lambda: self.log_in(self.username, self.password))
        
        
        auth_layout.addWidget(loginheading)
        auth_layout.addWidget(self.username)
        auth_layout.addWidget(self.password)
        auth_layout.addWidget(login_button)
        
        
        
        auth_layout.addStretch()
        
        central_layout.addWidget(companyinfo)
        central_layout.addWidget(authinfo)
        

        self.load_username()
        QTimer.singleShot(0, self.password.setFocus)
        
        connection = SQLiteConnectionManager('ProcureApp')
        connection.open()
        
        self.create_auth_table()

        self.setCentralWidget(central_widget)
        
    
    def load_username(self):
        last_user = self.settings.value("last_username", "")
        self.username.setText(last_user)
        
    

    def update_batch_status(self):
        
        today = QDate.currentDate()

        query = QSqlQuery()
        # Get all batches with expiry dates
        if not query.exec("SELECT id, expiry FROM batch"):
            print("Query failed:", query.lastError().text())
            return

        while query.next():
            batch_id = query.value(0)
            expiry = query.value(1)  # QDate if DB driver supports, else string

            if isinstance(expiry, str):
                expiry = QDate.fromString(expiry, "yyyy-MM-dd")  # adjust format

            # Calculate days difference
            days_left = today.daysTo(expiry)

            if days_left < 0:
                status = "expired"
            elif days_left <= 30:
                status = "near-expiry"
            else:
                status = "valid"

            # Update status in DB
            update_query = QSqlQuery()
            update_query.prepare("UPDATE batch SET status = ? WHERE id = ?")
            update_query.addBindValue(status)
            update_query.addBindValue(batch_id)

            if not update_query.exec():
                print(f"Failed to update batch {batch_id}: {update_query.lastError().text()}")

    
    
    
    
    
    
    
        
    def log_in(self, username, password):
        
        username = username.text()
        password = password.text()
        
        print(username, password)
        
        if username == '' or password == '':
            QMessageBox.critical(None,'Login Failed', 'Username or Password Cannot be Empty')
        else:
            
            if self.authenticate_user(username, password):
                
                print("User Logged In")
                
                self.settings.setValue("last_username", username)
                
                db = QSqlDatabase.database()
                db.transaction()

                try:
                    self.ensure_additional_charges_column()
                    db.commit()
                except Exception as e:
                    db.rollback()
                    print("Migration failed:", e)
                
                
                # Checking Products Expiry Status
                self.update_batch_status()
                
                # Setting username 
                QApplication.instance().setProperty("username", username)
                
                
                self.create_supplier_table()
                self.create_rep_table()
                
                self.create_product_table()
                self.create_batch_table()
                self.create_price_pack_table()
                
                self.create_inventory_adjustment_table()
                self.create_accounting_settings_table()
                
                self.create_business_table()
                self.create_purchase_table()
                self.create_purchaseitem_table()
                self.create_sales_table()
                self.create_salesitem_table()
                self.create_sold_batch_table()
                self.create_employee_table()
                self.create_customer_table()
                self.create_supplier_transaction_table()
                self.create_customer_transaction_table()
                self.create_purchase_return_table()
                self.create_purchase_return_item_table()
                self.create_salesreturn_table()
                self.create_salesreturn_item_table()
                self.create_expense_table()
                self.create_holdsale_table()
                self.create_holdsale_items_table()
                
                
                # Create Business
                
                print("Inserting Business Record - Empty Now")
                
                business_query = QSqlQuery()
                business_query.prepare(""" 
                                       INSERT INTO business(businessname, address, contact, email, website, license, ntn) 
                                       VALUES(?, ?, ?, ?, ?, ?, ?)
                                       """ )
                
                business_query.addBindValue("")
                business_query.addBindValue("")
                business_query.addBindValue("")
                business_query.addBindValue("")
                business_query.addBindValue("")
                business_query.addBindValue("")
                business_query.addBindValue("")
                
                
                
                if business_query.exec():
                    print("Business Record created")
                else:
                    print("Business Creation Failed")
                    print(business_query.lastError().text())
                

                
                
                window = MainWindow()
                window.show()
                
                self.close()
                
            else:
                
                print("Try Again...")
                QMessageBox.critical(None ,'Login Failed', 'Login Failed, Try Again...')
                self.username.clear()
                self.password.clear()
                self.username.setFocus()
            
            
            
            
            
            
            
        
    def authenticate_user(self, username, password):
        
        query = QSqlQuery()
        query.prepare("SELECT password_hash, role FROM auth WHERE username = ? AND status = 'active'")
        query.addBindValue(username)

        if not query.exec():
            print("Error While Fetching Credentials", query.lastError().text())
            return False

        if query.next():
            
            stored_hash = query.value(0)
            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                role = query.value(1)
                QApplication.instance().setProperty("user_role", role)
                return True
            else:
                return False
            
        
        return False

            
    
    
    def create_auth_table(self):
        
        
        query = QSqlQuery()
        print("Creating Auth Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS auth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firstname TEXT,
                lastname TEXT,
                email TEXT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT,
                role TEXT,
                status TEXT DEFAULT 'active'
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'auth' created successfully.")
        
        
        
        query.exec("SELECT COUNT(*) FROM auth")
        
        if query.next() and query.value(0) == 0:
            
            # Insert default user
            query.prepare("""
                    INSERT INTO auth (firstname, lastname, email, username, password_hash, salt, role, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """)
                
            password = 'admin'
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode(), salt).decode()
            
            query.addBindValue("Default")
            query.addBindValue("Admin")
            query.addBindValue("admin@example.com")
            query.addBindValue("admin")
            query.addBindValue(password_hash)  # use your own hash function
            query.addBindValue(salt.decode())
            query.addBindValue("admin")
            query.addBindValue("active")
                
            if not query.exec():
                print("Insert failed:", query.lastError().text())
            else:
                print("Default Admin User Created....")
            
        return True
            
    
    
    def create_accounting_settings_table(self):

        query = QSqlQuery()
        print("Creating Accounting Settings Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS accounting_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),

                opening_inventory_value REAL DEFAULT 0,
                opening_inventory_set_at TIMESTAMP,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
        """):
            QMessageBox.critical(
                None,
                "Error",
                f"Table creation failed: {query.lastError().text()}"
            )
            return False

        print("Table 'Accounting Settings' ready.")
        return True
            
        

    
    
    
    
    def ensure_additional_charges_column(self):
        
        check_query = QSqlQuery()
        check_query.exec("PRAGMA table_info(sales)")

        columns = []
        while check_query.next():
            column_name = check_query.value(1)  # 1 = column name
            columns.append(column_name)

        if "additional_charges" not in columns:
            print("Adding new column 'additional_charges'...")
            alter_query = QSqlQuery()
            alter_query.exec("ALTER TABLE sales ADD COLUMN additional_charges FLOAT DEFAULT 0;")
        else:
            print("Column 'additional_charges' already exists, skipping.")


        
        
        

    def create_supplier_table(self):
        
        query = QSqlQuery()
        print("Creating Supplier Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS supplier (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                email TEXT,
                website TEXT,
                address TEXT,
                status TEXT DEFAULT 'active',
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reg_no TEXT UNIQUE,
                payable REAL DEFAULT 0.00,
                receiveable REAL DEFAULT 0.00
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'supplier' ready.")
        return True
 
     
     
       
    def create_business_table(self):
        
        query = QSqlQuery()
        print("Creating Business Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS business (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                businessname TEXT NOT NULL,
                address TEXT,
                contact TEXT,
                email TEXT,
                website TEXT,
                license TEXT UNIQUE,
                ntn TEXT UNIQUE,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'business' ready.")
        return True
 
        


    
    
    def create_employee_table(self):
        
        query = QSqlQuery()
        print("Creating Employee Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS employee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                email TEXT,
                address TEXT,
                badge TEXT UNIQUE,
                role TEXT,
                status TEXT DEFAULT 'active',
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'employee' ready.")
        return True


        
        
    def create_customer_table(self):
        
        query = QSqlQuery()
        print("Creating Customer Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS customer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                email TEXT,
                status TEXT DEFAULT 'active',
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payable REAL DEFAULT 0.00,
                receiveable REAL DEFAULT 0.00
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'customer' ready.")
        return True
 
 
 
        
    
    def create_rep_table(self):
        
        query = QSqlQuery()
        print("Creating Rep Table")

        # Check if table exists
        if not query.exec("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name='rep';
        """):
            QMessageBox.critical(None, "Error", f"Table check failed: {query.lastError().text()}")
            return False

        table_exists = query.next()

        if table_exists:
            print("Table 'rep' already exists - skipping creation.")
            return True

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS rep (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                supplier_id INTEGER NOT NULL,
                contact TEXT,
                status TEXT DEFAULT 'active',
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'rep' created successfully.")
        return True
 
      
        

    def create_product_table(self):
        
        query = QSqlQuery()
        print("Creating Product Table")

        # Check if table exists
        if not query.exec("""
            SELECT EXISTS (
                SELECT 1 
                FROM sqlite_master 
                WHERE type='table' 
                AND name='product'
            );
        """):
            QMessageBox.critical(None, "Error", f"Table check failed: {query.lastError().text()}")
            return False

        query.next()
        table_exists = query.value(0)

        if table_exists:
            print("Table 'product' already exists - skipping creation.")
            return True

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS product (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,          -- "Paracetamol 500mg Tablet (10)"
                code TEXT UNIQUE,                    -- optional, barcode / internal
                generic_name TEXT,                   -- optional
                brand TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False
        
        

        print("Table 'product' created successfully.")
        # Create indexes for faster search
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_product_name   ON product(display_name)",
            "CREATE INDEX IF NOT EXISTS idx_product_code   ON product(code)",
            "CREATE INDEX IF NOT EXISTS idx_product_brand  ON product(brand)"
        ]

        for index_query in indexes:
            if not query.exec(index_query):
                QMessageBox.critical(None, "Error", f"Index creation failed: {query.lastError().text()}")

        print("Indexes created successfully (display_name, code, brand).")

        


    def create_price_pack_table(self):
        
        query = QSqlQuery()
        print("Creating price_pack Table")

        # Create table if it doesn't exist
        if not query.exec("""
           
            CREATE TABLE IF NOT EXISTS price_pack (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                pack_size INTEGER NOT NULL,      -- e.g. 5 tablets
                pack_price REAL NOT NULL,        -- e.g. 50
                unit_price REAL GENERATED ALWAYS AS (pack_price / pack_size),
                is_default BOOLEAN DEFAULT 1
            );

        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'price_pack' created successfully.")
        return True

        
        
        
    def create_batch_table(self):
        
        query = QSqlQuery()
        print("Creating Batch Table")

        # Create table if it doesn't exist
        if not query.exec("""
            
            CREATE TABLE IF NOT EXISTS batch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_no TEXT,                       -- optional (manufacturer lot)
                expiry_date DATE,                    -- optional
                product_id INTEGER NOT NULL,
                total_received INTEGER NOT NULL,
                paid_qty INTEGER NOT NULL,
                quantity_remaining INTEGER NOT NULL,
                unit_cost REAL,                      -- NULL allowed (opening stock)
                source TEXT,                         -- 'opening', 'purchase'
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (product_id) REFERENCES product(id)
            );

        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'batch' created successfully.")
        return True

        
    
    
    def create_inventory_adjustment_table(self):
        
        query = QSqlQuery()
        print("Creating inventory_adjustment Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS inventory_adjustment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                qty INTEGER NOT NULL,         -- always positive
                reason TEXT NOT NULL,         -- 'expired', 'damaged', 'lost', etc.
                note TEXT,                    -- optional human explanation
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (batch_id) REFERENCES batch(id)
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'inventory_adjustment' created successfully.")
        return True

        
        
    
    def create_purchase_table(self):
        
        query = QSqlQuery()
        print("Creating Purchase Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS purchase (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                supplier INTEGER NOT NULL,
                rep INTEGER,
                sellerinvoice TEXT(100) NOT NULL,
                
                subtotal DECIMAL(10,2) NOT NULL,
                discount DECIMAL(10,2) NOT NULL,
                
                tax_236g DECIMAL(10,2) NOT NULL,
                tax_236h DECIMAL(10,2) NOT NULL,
                salestax DECIMAL(10,2) NOT NULL,
                
                netamount DECIMAL(10,2) NOT NULL,
                cn_adjustment DECIMAL(10,2) NOT NULL,
                
                total DECIMAL(10,2) NOT NULL,
                paid DECIMAL(10,2) NOT NULL,
                remaining DECIMAL(10,2) NOT NULL,
                writeoff DECIMAL(10,2) NOT NULL,
                
                payable DECIMAL(10,2) NOT NULL,
                receiveable DECIMAL(10,2) NOT NULL,
                
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier) REFERENCES supplier(id) ON DELETE RESTRICT,
                FOREIGN KEY (rep) REFERENCES rep(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'purchase' created successfully.")
        return True

        

     
    def create_supplier_transaction_table(self):
        
        query = QSqlQuery()
        print("Creating Supplier Transaction Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS supplier_transaction (
                
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier INTEGER NOT NULL,
                transaction_type TEXT(50) NOT NULL,
                ref INTEGER,
                return_ref INTEGER,

                payable_before DECIMAL(10,2) DEFAULT 0.00,
                due_amount DECIMAL(10,2) DEFAULT 0.00,
                paid DECIMAL(10,2) DEFAULT 0.00,
                remaining_due DECIMAL(10,2) DEFAULT 0.00,
                payable_after DECIMAL(10,2) DEFAULT 0.00,

                receiveable_before DECIMAL(10,2) DEFAULT 0.00,
                receiveable_now DECIMAL(10,2) DEFAULT 0.00,
                received DECIMAL(10,2) DEFAULT 0.00,
                remaining_now DECIMAL(10,2) DEFAULT 0.00,
                receiveable_after DECIMAL(10,2) DEFAULT 0.00,

                rep INTEGER,
                note TEXT(500),
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (supplier) REFERENCES supplier(id) ON DELETE RESTRICT,
                FOREIGN KEY (rep) REFERENCES rep(id) ON DELETE RESTRICT,
                FOREIGN KEY (ref) REFERENCES purchase(id) ON DELETE RESTRICT,
                FOREIGN KEY (return_ref) REFERENCES purchase_return(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'supplier_transaction' created successfully.")
        return True

       
    
    
    def create_customer_transaction_table(self):
        
        query = QSqlQuery()
        print("Creating Customer Transaction Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS customer_transaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer INTEGER,
                transaction_type TEXT(50) NOT NULL,
                ref INTEGER,
                return_ref INTEGER,

                payable_before DECIMAL(10,2) DEFAULT 0.00,
                due_amount DECIMAL(10,2) DEFAULT 0.00,
                paid DECIMAL(10,2) DEFAULT 0.00,
                remaining_due DECIMAL(10,2) DEFAULT 0.00,
                payable_after DECIMAL(10,2) DEFAULT 0.00,

                receiveable_before DECIMAL(10,2) DEFAULT 0.00,
                receiveable_now DECIMAL(10,2) DEFAULT 0.00,
                received DECIMAL(10,2) DEFAULT 0.00,
                remaining_now DECIMAL(10,2) DEFAULT 0.00,
                receiveable_after DECIMAL(10,2) DEFAULT 0.00,

                salesman INTEGER,
                note TEXT,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (customer) REFERENCES customer(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesman) REFERENCES employee(id) ON DELETE RESTRICT,
                FOREIGN KEY (ref) REFERENCES sales(id) ON DELETE RESTRICT,
                FOREIGN KEY (return_ref) REFERENCES salesreturn(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'customer_transaction' created successfully.")
        return True

        
        
        
    def create_purchaseitem_table(self):
        query = QSqlQuery()
        print("Creating Purchase Item Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS purchaseitem (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase INTEGER NOT NULL,
                product INTEGER NOT NULL,
                qty INTEGER NOT NULL,
                bonus INTEGER NOT NULL,
                rate DECIMAL(10,2) NOT NULL,
                discount DECIMAL(10,2) NOT NULL,
                tax DECIMAL(10,2) NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (purchase) REFERENCES purchase(id) ON DELETE RESTRICT,
                FOREIGN KEY (product) REFERENCES product(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'purchaseitem' created successfully.")
        return True

    
     
    
    def create_purchase_return_table(self):
        query = QSqlQuery()
        print("Creating Purchase Return Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS purchase_return (
                
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier INTEGER NOT NULL,
                rep INTEGER NOT NULL,
                subtotal DECIMAL(10,2) NOT NULL,
                roundoff DECIMAL(10,2) NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                received DECIMAL(10,2) NOT NULL,
                remaining DECIMAL(10,2) NOT NULL,
                writeoff DECIMAL(10,2) NOT NULL,
                payable DECIMAL(10,2) NOT NULL,
                receiveable DECIMAL(10,2) NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (supplier) REFERENCES supplier(id) ON DELETE RESTRICT,
                FOREIGN KEY (rep) REFERENCES rep(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'purchase_return' created successfully.")
        return True

    
    
    
    def create_purchase_return_item_table(self):
        query = QSqlQuery()
        print("Creating Purchase Return Item Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS purchase_return_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_return INTEGER NOT NULL,
                product INTEGER NOT NULL,
                batch TEXT NOT NULL,
                purchased INTEGER NOT NULL,
                returned INTEGER NOT NULL,
                rate REAL NOT NULL,
                total REAL NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (purchase_return) REFERENCES purchase_return(id) ON DELETE RESTRICT,
                FOREIGN KEY (product) REFERENCES product(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'purchase_return_item' created successfully.")
        return True

     
     
     
    def create_sales_table(self):
        
        query = QSqlQuery()
        print("Creating Sales Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer INTEGER,
                salesman INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                discount REAL NOT NULL,
                taxable REAL NOT NULL,
                tax REAL NOT NULL,
                net_amount REAL NOT NULL,
                additional_charges REAL NOT NULL,
                total REAL NOT NULL,
                received REAL NOT NULL,
                remaining REAL NOT NULL,
                writeoff REAL NOT NULL,
                payable REAL NOT NULL,
                receiveable REAL NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer) REFERENCES customer(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesman) REFERENCES auth(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'sales' created successfully.")
        return True
   
    
    
     
    def create_salesitem_table(self):
        query = QSqlQuery()
        print("Creating salesitem Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS salesitem (
                
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sales_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                qty_sold INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                discount REAL NOT NULL,
                tax REAL NOT NULL,
                line_total REAL NOT NULL,
                
                line_weight DECIMAL(10,2) NOT NULL,
                effective_line_total DECIMAL(10,2) NOT NULL,
                
                
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sales_id) REFERENCES sales(id) ON DELETE RESTRICT,
                FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT
            );
        """):
            
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'salesitem' created successfully.")
        return True
 
    
    
    def create_sold_batch_table(self):
        
        query = QSqlQuery()
        print("Creating Sold Batch Table")

        # Create table if it doesn't exist
        if not query.exec("""
            
            CREATE TABLE IF NOT EXISTS sold_batch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_item_id INTEGER NOT NULL, 
                batch_id INTEGER NOT NULL, 
                qty_taken INTEGER NOT NULL,
                qty_returned INTEGER DEFAULT 0,
                unit_cost REAL,                      -- NULL allowed
                line_cost REAL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (sale_item_id) REFERENCES salesitem(id)
            );

        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'sold_batch' created successfully.")
        return True
    
    
    
    
    def create_holdsale_table(self):
        query = QSqlQuery()
        print("Creating holdsale Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS holdsale (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer INTEGER,
                salesman INTEGER,
                status TEXT,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer) REFERENCES customer(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesman) REFERENCES employee(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'holdsale' created successfully.")
        return True
   
        
        
    
    def create_holdsale_items_table(self):
        query = QSqlQuery()
        print("Creating holditems Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS holditems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                holdsale INTEGER NOT NULL,
                product INTEGER NOT NULL,
                qty INTEGER NOT NULL,
                unitrate DECIMAL(10,2) NOT NULL,
                discount DECIMAL(10,2) NOT NULL,
                discountamount DECIMAL(10,2) NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (holdsale) REFERENCES holdsale(id) ON DELETE RESTRICT,
                FOREIGN KEY (product) REFERENCES product(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'holditems' created successfully.")
        return True

        
        
           
    def create_salesreturn_table(self):
        query = QSqlQuery()
        print("Creating salesreturn Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS salesreturn (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                salesorder INTEGER NOT NULL,
                customer INTEGER,
                salesman INTEGER NOT NULL,
                subtotal DECIMAL(10,2) NOT NULL,
                roundoff DECIMAL(10,2) NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                paid DECIMAL(10,2) NOT NULL,
                remaining DECIMAL(10,2) NOT NULL,
                writeoff DECIMAL(10,2) NOT NULL,
                payable DECIMAL(10,2) NOT NULL,
                receiveable DECIMAL(10,2) NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer) REFERENCES customer(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesman) REFERENCES employee(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesorder) REFERENCES sales(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'salesreturn' created successfully.")
        return True

    
    
    
    def create_salesreturn_item_table(self):
        query = QSqlQuery()
        print("Creating salesreturn_item Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS salesreturn_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                salesreturn INTEGER NOT NULL,
                salesitem_id INTEGER NOT NULL,
                product INTEGER NOT NULL,
                sold INTEGER NOT NULL,
                returned INTEGER NOT NULL,
                rate DECIMAL(10,2) NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (salesreturn) REFERENCES salesreturn(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesitem_id) REFERENCES salesitem(id) ON DELETE RESTRICT,
                FOREIGN KEY (product) REFERENCES product(id) ON DELETE RESTRICT
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'salesreturn_item' created successfully.")
        return True



    
    def create_expense_table(self):
        query = QSqlQuery()
        print("Creating expense Table")

        # Create table if it doesn't exist
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS expense (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                note TEXT NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """):
            QMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'expense' created successfully.")
        return True

    
    
    

from utilities.license import LicenseDialog

if __name__ == '__main__':

    app = QApplication([])
    
    window = AuthWindow()
    window.show()
    
    license_dialog = LicenseDialog()
    
    app.exec()
    
    
    
