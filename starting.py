
import os
import csv
import sys
import sqlite3
import secrets
import time

def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


master_products_file = resource_path("master_products.csv")
manufacturers_file = resource_path("manufacturers.csv")


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


from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QFileDialog, QFrame, QSizePolicy
from PySide6.QtGui import QPixmap

from utilities.database import SQLiteConnectionManager, QSqlDatabase
from utilities.app_messagebox import install_messagebox_theme
from utilities.dialog_scrolling import install_dialog_scrolling
from utilities.mylogin import MainWindow
import bcrypt
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtSql import QSqlQuery
from PySide6.QtCore import QDate, QSettings, QTimer, Qt

import shutil, subprocess
import uuid

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

    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_SECONDS = 300


    def __init__(self):

        super().__init__()
        install_messagebox_theme()
        install_dialog_scrolling()
        self.settings = QSettings("procure", "procure_medics")  # unique identifiers
        self._login_attempt_state = {}
        
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
        companyinfo_layout.setContentsMargins(44, 42, 44, 42)
        companyinfo_layout.setSpacing(18)
        companyinfo.setMinimumWidth(600)
        companyinfo.setStyleSheet("""
            background-color: #163B5C;
            color: #EAF3FB;
        """)

        companyinfo_layout.addStretch(1)
        
        
        
        authinfo = QWidget()
        auth_layout = QVBoxLayout()
        self.auth_layout = auth_layout
        authinfo.setLayout(auth_layout)
        auth_layout.setContentsMargins(56, max(32, int(height * 0.10)), 56, 44)
        auth_layout.setSpacing(0)
        authinfo.setMinimumWidth(600)
        authinfo.setStyleSheet("background-color: #F5F8FB;")

        login_card = QFrame()
        login_card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
                border-radius: 8px;
            }
        """)
        login_card.setMinimumWidth(520)
        login_card.setMaximumWidth(680)

        login_card_layout = QVBoxLayout(login_card)
        login_card_layout.setContentsMargins(38, 34, 38, 30)
        login_card_layout.setSpacing(14)

        login_eyebrow = QLabel("Welcome back")
        login_eyebrow.setStyleSheet("font-size: 12px; font-weight: 700; color: #5D7D95; font-family: 'montserrat'; padding-left: 0;")

        loginheading = QLabel('Login to Continue')
        loginheading.setStyleSheet("font-size: 26px; font-weight: 700; color: #18374D; padding-left: 0; font-family: 'montserrat';")

        field_style = """
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #fbfcfd;
                color: #333;
                font-size: 14px;
                font-weight: 700;
                font-family: 'montserrat';
            }
            QLineEdit:focus {
                border-bottom: 1px solid #2F5D7C;
                background-color: #EEF5FA;
            }
        """

        self.username = QLineEdit()
        self.username.setPlaceholderText('Username')
        self.username.setStyleSheet(field_style)

        self.password = QLineEdit()
        self.password.setPlaceholderText('Password')
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet(field_style)

        login_button = QPushButton('Login')
        login_button.setCursor(Qt.PointingHandCursor)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #2F5D7C;
                color: #ffffff;
                border: 1px solid #2a506b;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 700;
                padding: 4px 10px;
                font-family: 'montserrat';
            }
            QPushButton:hover {
                background-color: #244A62;
                border: 1px solid #2a506b;
            }
            QPushButton:pressed {
                background-color: #163B5C;
                border: 1px solid #23465d;
            }
        """)
        login_button.clicked.connect(lambda: self.log_in(self.username, self.password))

        helper_text = QLabel("Use your assigned Procure credentials to continue.")
        helper_text.setWordWrap(True)
        helper_text.setStyleSheet(
            "font-size: 12px; color: #6B7F8F; font-weight: 600; font-family: 'montserrat'; padding-left: 0;"
        )

        trust_block = QFrame()
        trust_block.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        trust_block.setStyleSheet("""
            QFrame {
                background-color: #F7FAFC;
                border: 1px solid #D9E4EC;
                border-radius: 6px;
            }
            QLabel {
                background: transparent;
                border: none;
                padding: 0;
            }
        """)
        trust_layout = QVBoxLayout(trust_block)
        trust_layout.setContentsMargins(18, 16, 18, 16)
        trust_layout.setSpacing(10)

        trust_title = QLabel("Secure Operational Access")
        trust_title.setWordWrap(True)
        trust_title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        trust_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        trust_title.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #18374D; font-family: 'montserrat'; padding-left: 0; margin: 0;"
        )
        trust_copy = QLabel(
            "You are signing in to a live business workspace where inventory, purchasing, sales, and financial records are managed with accountability."
        )
        trust_copy.setWordWrap(True)
        trust_copy.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        trust_copy.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        trust_copy.setStyleSheet(
            "background: transparent; border: none; color: #5E7384; font-size: 12px; font-weight: 500; font-family: 'montserrat'; padding: 0; margin: 0;"
        )
        self.trust_copy_text = trust_copy

        trust_layout.addWidget(trust_title)
        trust_layout.addWidget(trust_copy)

        login_card_layout.addWidget(login_eyebrow)
        login_card_layout.addWidget(loginheading)
        login_card_layout.addSpacing(4)
        login_card_layout.addWidget(self.username)
        login_card_layout.addWidget(self.password)
        login_card_layout.addSpacing(12)
        login_card_layout.addWidget(login_button)
        login_card_layout.addWidget(helper_text)
        login_card_layout.addSpacing(0)
        login_card_layout.addWidget(trust_block)

        auth_layout.addWidget(login_card, 0, Qt.AlignHCenter | Qt.AlignTop)
        auth_layout.addStretch(1)
        
        central_layout.addWidget(companyinfo, 1)
        central_layout.addWidget(authinfo, 1)
        

        self.load_username()
        QTimer.singleShot(0, self.password.setFocus)
        
        self.connection = SQLiteConnectionManager('ProcureApp')
        self.backup_manager = self.connection

        if not self.ensure_startup_database_ready():
            QTimer.singleShot(0, QApplication.instance().quit)
            self.setCentralWidget(central_widget)
            return

        self.create_auth_table()

        self.setCentralWidget(central_widget)

    def resizeEvent(self, event):
        top_margin = max(32, int(self.height() * 0.10))
        left_margin, _, right_margin, bottom_margin = self.auth_layout.getContentsMargins()
        self.auth_layout.setContentsMargins(left_margin, top_margin, right_margin, bottom_margin)
        super().resizeEvent(event)

    def load_username(self):
        last_user = self.settings.value("last_username", "")
        self.username.setText(last_user)

    def _attempt_key(self, username):
        return (username or "").strip().lower()

    def _lockout_remaining(self, username):
        key = self._attempt_key(username)
        if not key:
            return 0

        state = self._login_attempt_state.get(key)
        if not state:
            return 0

        locked_until = float(state.get("locked_until", 0.0) or 0.0)
        remaining = int(locked_until - time.time())
        if remaining <= 0:
            state["locked_until"] = 0.0
            state["attempts"] = 0
            return 0
        return remaining

    def _record_failed_attempt(self, username):
        key = self._attempt_key(username)
        if not key:
            return

        state = self._login_attempt_state.setdefault(key, {"attempts": 0, "locked_until": 0.0})
        state["attempts"] = int(state.get("attempts", 0)) + 1

        if state["attempts"] >= self.MAX_LOGIN_ATTEMPTS:
            state["locked_until"] = time.time() + self.LOGIN_LOCKOUT_SECONDS
            state["attempts"] = 0

    def _clear_attempt_state(self, username):
        key = self._attempt_key(username)
        if key:
            self._login_attempt_state.pop(key, None)


    def ensure_startup_database_ready(self):
        try:
            self.connection.open()
        except Exception as exc:
            return self.open_recovery_mode(f"Could not open database: {str(exc)}")

        healthy, reason = self.check_current_database_health()
        if healthy:
            return True

        return self.open_recovery_mode(reason)


    def check_current_database_health(self):
        db_path = self.connection.db_path
        if not os.path.exists(db_path):
            return False, "Database file is missing."

        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            cur.execute("PRAGMA integrity_check")
            result = cur.fetchone()
            integrity = str((result[0] if result else "") or "")
            if integrity.lower() != "ok":
                return False, f"Database integrity check failed: {integrity}"

            cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='auth' LIMIT 1")
            has_auth = cur.fetchone() is not None
            if not has_auth:
                return False, "Authentication table is missing."

            return True, ""
        except Exception as exc:
            return False, f"Database health check failed: {str(exc)}"
        finally:
            if conn is not None:
                conn.close()


    def get_available_backup_files(self):
        backup_dir = self.backup_manager.get_backup_dir()
        if not os.path.isdir(backup_dir):
            return []

        files = []
        for name in os.listdir(backup_dir):
            if name.startswith("procuredb_backup_") and name.endswith(".sqlite"):
                path = os.path.join(backup_dir, name)
                try:
                    files.append((os.path.getmtime(path), path))
                except OSError:
                    continue

        files.sort(reverse=True)
        return [path for _, path in files]


    def attempt_restore_file(self, backup_file):
        try:
            self.backup_manager.restore_from_backup(
                backup_file=backup_file,
                create_pre_restore_backup=False,
            )
            self.connection.open()
            AppMessageBox.information(self, "Recovery", "Database restore completed. Login is available now.")
            return True
        except Exception as exc:
            AppMessageBox.critical(self, "Restore Failed", str(exc))
            return False


    def open_recovery_mode(self, reason):
        while True:
            msg = QMessageBox(self)
            msg.setWindowTitle("Recovery Mode")
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Database is not ready for normal login.")
            msg.setInformativeText(
                f"Reason: {reason}\n\n"
                "Choose a recovery option to continue."
            )

            latest_btn = msg.addButton("Restore Latest Backup", QMessageBox.AcceptRole)
            select_btn = msg.addButton("Restore Selected Backup...", QMessageBox.ActionRole)
            fresh_btn = msg.addButton("Create Fresh Login Table", QMessageBox.DestructiveRole)
            exit_btn = msg.addButton("Exit App", QMessageBox.RejectRole)

            msg.exec()
            clicked = msg.clickedButton()

            if clicked == latest_btn:
                backups = self.get_available_backup_files()
                if not backups:
                    AppMessageBox.warning(self, "No Backup", "No backup files were found.")
                    continue
                if self.attempt_restore_file(backups[0]):
                    return True
                continue

            if clicked == select_btn:
                backup_file, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Backup File",
                    self.backup_manager.get_backup_dir(),
                    "SQLite Backup (*.sqlite)",
                )
                if not backup_file:
                    continue
                if self.attempt_restore_file(backup_file):
                    return True
                continue

            if clicked == fresh_btn:
                try:
                    self.connection.open()
                    if self.create_auth_table():
                        AppMessageBox.information(self, "Recovery", "Fresh login table created. You can log in now.")
                        return True
                except Exception as exc:
                    AppMessageBox.critical(self, "Recovery Failed", str(exc))
                continue

            if clicked == exit_btn:
                return False
        
    

    
    
    
    
    
    
    
        
    def log_in(self, username, password):
        
        username = username.text()
        password = password.text()

        remaining = self._lockout_remaining(username)
        if remaining > 0:
            minutes = max(1, (remaining + 59) // 60)
            AppMessageBox.critical(
                None,
                'Login Locked',
                f'Too many failed attempts. Try again in about {minutes} minute(s).'
            )
            self.password.clear()
            self.password.setFocus()
            return
        
        if username == '' or password == '':
            AppMessageBox.critical(None,'Login Failed', 'Username or Password Cannot be Empty')
        else:
            
            if self.authenticate_user(username, password):
                self._clear_attempt_state(username)
                
                print("User Logged In")
                
                self.settings.setValue("last_username", username)
                
                
                
                
                
                
                # Setting username 
                QApplication.instance().setProperty("username", username)
                QApplication.instance().setProperty("login_session_id", str(uuid.uuid4()))
                
                self.initialize_database()

                seed_summary = getattr(self, "_startup_seed_summary", None) or {}
                if seed_summary:
                    summary_lines = []
                    if seed_summary.get("manufacturers"):
                        summary_lines.append(f"Manufacturers imported: {seed_summary['manufacturers']}")
                    if seed_summary.get("products"):
                        summary_lines.append(f"Products imported: {seed_summary['products']}")
                    AppMessageBox.information(
                        None,
                        "Catalog Imported",
                        "Bundled startup catalog was imported successfully.\n\n" + "\n".join(summary_lines),
                    )

                try:
                    from utilities.activity_logger import log_activity
                    log_activity(
                        category="login",
                        action="login",
                        entity_type="user",
                        entity_id=QApplication.instance().property("user_id"),
                        note=f"{username} signed in to the system."
                    )
                except Exception as e:
                    print("Login audit log failed (non-blocking):", e)
                
                # Create Business
                
                
                

                
                
                window = MainWindow()
                window.show()
                
                self.close()
                
            else:
                self._record_failed_attempt(username)
                
                print("Try Again...")
                AppMessageBox.critical(None ,'Login Failed', 'Login Failed, Try Again...')
                self.username.clear()
                self.password.clear()
                self.username.setFocus()
            
    
    
    def table_exists(self, table_name):
        
        query = QSqlQuery()
        query.prepare("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
        """)
        query.addBindValue(table_name)

        if not query.exec():
            print("table_exists error:", query.lastError().text())
            return False

        return query.next()

    
    def required_tables_exist(self):
        self.create_expense_table()
        required_tables = [
            "expense",
            "supplier_transaction",
            "supplier",
            "manufacturer",
            "product",
            "batch",
            "sales",
            "purchase",
            "daily_session",
        ]

        for table_name in required_tables:
            if not self.table_exists(table_name):
                return False

        return True
    
    def create_schema_tables(self):
        table_builders = [
            self.create_daily_session_table,
            self.create_supplier_table,
            self.create_rep_table,
            self.create_discount_group_table,
            self.create_tax_group_table,
            self.create_manufacturer_table,
            self.create_product_table,
            self.create_batch_table,
            self.create_price_pack_table,
            self.create_price_changes_table,
            self.create_inventory_adjustment_table,
            self.create_accounting_settings_table,
            self.create_business_table,
            self.create_purchase_table,
            self.create_purchaseitem_table,
            self.create_purchase_order_table,
            self.create_purchase_order_line_table,
            self.create_goods_receipt_table,
            self.create_goods_receipt_line_table,
            self.create_sales_table,
            self.create_salesitem_table,
            self.create_sold_batch_table,
            self.create_employee_table,
            self.create_customer_table,
            self.create_supplier_transaction_table,
            self.create_customer_transaction_table,
            self.create_purchase_return_table,
            self.create_purchase_return_item_table,
            self.create_salesreturn_table,
            self.create_salesreturn_item_table,
            self.create_expense_table,
            self.create_holdsale_table,
            self.create_holdsale_items_table,
            self.create_activity_log_table,
        ]

        for builder in table_builders:
            if builder() is False:
                return False
        return True

           
            
    def initialize_database(self):
        self._startup_seed_summary = None
        
        if self.required_tables_exist():
            print("Tables already exist. Skipping creation.")
            self.create_discount_group_table()
            self.create_tax_group_table()
            self.create_purchase_order_table()
            self.create_purchase_order_line_table()
            self.create_goods_receipt_table()
            self.create_goods_receipt_line_table()
            self.create_price_pack_table()
            self.create_price_changes_table()
            self.create_activity_log_table()
            self.seed_discount_group_table()
            self.seed_tax_group_table()
            self.create_customer_table()
            self.apply_runtime_schema_migrations()
            self._startup_seed_summary = self.ensure_catalog_seeded()
            return

        print("First run detected. Creating tables...")
        if not self.create_schema_tables():
            return

        self.seed_discount_group_table()
        self.seed_tax_group_table()
        self._startup_seed_summary = self.ensure_catalog_seeded()
        
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

    def _sqlite_column_names(self, conn, table_name):
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        return {str(row[1]) for row in cur.fetchall()}

    def _table_row_count(self, table_name):
        query = QSqlQuery()
        if not query.exec(f"SELECT COUNT(*) FROM {table_name}"):
            print(f"Failed to count rows in {table_name}: {query.lastError().text()}")
            return None
        if not query.next():
            return None
        return int(query.value(0) or 0)

    def ensure_catalog_seeded(self):
        seeded = {}

        manufacturer_count = self._table_row_count("manufacturer")
        if manufacturer_count == 0:
            print("Manufacturer table is empty. Seeding from bundled CSV.")
            imported = self.populate_manufacturers_from_csv()
            if imported:
                seeded["manufacturers"] = imported

        product_count = self._table_row_count("product")
        if product_count == 0:
            print("Product table is empty. Seeding from bundled CSV.")
            imported = self.populate_products_from_csv()
            if imported:
                seeded["products"] = imported

        return seeded

    def _ensure_sqlite_column(self, conn, table_name, column_name, column_sql):
        columns = self._sqlite_column_names(conn, table_name)
        if column_name in columns:
            return False
        cur = conn.cursor()
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")
        return True

    def apply_runtime_schema_migrations(self):
        """
        Keep existing installs aligned with the final schema expected by the app.
        These are intentionally small, additive migrations only.
        """
        db_path = getattr(self.connection, "db_path", None)
        if not db_path or not os.path.exists(db_path):
            return

        conn = None
        try:
            conn = sqlite3.connect(db_path)
            changed = []

            if self._ensure_sqlite_column(conn, "purchase", "due_date", "DATE"):
                changed.append("purchase.due_date")

            if self._ensure_sqlite_column(conn, "purchase", "session_id", "INTEGER"):
                changed.append("purchase.session_id")

            if self._ensure_sqlite_column(conn, "purchase", "cn_adjustment", "DECIMAL(10,2) DEFAULT 0.00"):
                changed.append("purchase.cn_adjustment")

            if self._ensure_sqlite_column(conn, "purchase_order", "session_id", "INTEGER"):
                changed.append("purchase_order.session_id")

            if self._ensure_sqlite_column(conn, "goods_receipt", "session_id", "INTEGER"):
                changed.append("goods_receipt.session_id")

            if self._ensure_sqlite_column(conn, "supplier_transaction", "session_id", "INTEGER"):
                changed.append("supplier_transaction.session_id")

            if self._ensure_sqlite_column(conn, "supplier_transaction", "payment_method", "TEXT"):
                changed.append("supplier_transaction.payment_method")

            if self._ensure_sqlite_column(conn, "supplier_transaction", "bank_name", "TEXT"):
                changed.append("supplier_transaction.bank_name")

            if self._ensure_sqlite_column(conn, "supplier_transaction", "account_no", "TEXT"):
                changed.append("supplier_transaction.account_no")

            if self._ensure_sqlite_column(conn, "supplier_transaction", "transaction_mode", "TEXT"):
                changed.append("supplier_transaction.transaction_mode")

            if self._ensure_sqlite_column(conn, "supplier_transaction", "wallet_provider", "TEXT"):
                changed.append("supplier_transaction.wallet_provider")

            if self._ensure_sqlite_column(conn, "supplier_transaction", "wallet_no", "TEXT"):
                changed.append("supplier_transaction.wallet_no")

            if self._ensure_sqlite_column(conn, "supplier_transaction", "payment_reference", "TEXT"):
                changed.append("supplier_transaction.payment_reference")

            if changed:
                conn.commit()
                print("Applied runtime schema migrations:", ", ".join(changed))
            else:
                conn.commit()
                print("Runtime schema migrations: no changes needed.")
        except Exception as exc:
            if conn is not None:
                conn.rollback()
            print("Runtime schema migration failed:", str(exc))
        finally:
            if conn is not None:
                conn.close()
    
    
    
    
        
    def authenticate_user(self, username, password):
        
        query = QSqlQuery()
        query.prepare("SELECT id, password_hash, role FROM auth WHERE username = ? AND status = 'active'")
        query.addBindValue(username)

        if not query.exec():
            print("Error While Fetching Credentials", query.lastError().text())
            return False

        if query.next():
            user_id = query.value(0)
            stored_hash = query.value(1)
            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                role = query.value(2)
                QApplication.instance().setProperty("user_role", role)
                QApplication.instance().setProperty("user_id", int(user_id))
                return True
            else:
                return False
            
        
        return False

    
    
    

    def seed_manufacturer_table(self):
        
        file_path = os.path.join(os.path.dirname(__file__), "manufacturers.csv")

        if not os.path.exists(file_path):
            print("manufacturers.csv not found - skipping manufacturer seed.")
            return True

        # Skip if data already exists
        check_query = QSqlQuery()
        if not check_query.exec("SELECT COUNT(*) FROM manufacturer"):
            AppMessageBox.critical(None, "Error", f"Manufacturer count check failed: {check_query.lastError().text()}")
            return False

        check_query.next()
        if int(check_query.value(0) or 0) > 0:
            print("Manufacturer table already has data - skipping seed.")
            return True

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.critical(None, "Error", "Could not start manufacturer seed transaction.")
            return False

        query = QSqlQuery()

        try:
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    manufacturer_id = row.get("Manufacturer_ID", "").strip()
                    manufacturer_name = row.get("Manufacturer_Name", "").strip()

                    if not manufacturer_name:
                        continue

                    query.prepare("""
                        INSERT INTO manufacturer (id, name)
                        VALUES (?, ?)
                    """)
                    query.addBindValue(int(manufacturer_id) if manufacturer_id else None)
                    query.addBindValue(manufacturer_name)

                    if not query.exec():
                        raise Exception(query.lastError().text())

            if not db.commit():
                raise Exception("Failed to commit manufacturer seed.")

            print("Manufacturer table seeded successfully.")
            return True

        except Exception as e:
            db.rollback()
            AppMessageBox.critical(None, "Error", f"Manufacturer seed failed: {str(e)}")
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
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'auth' created successfully.")
        
        
        
        query.exec("SELECT COUNT(*) FROM auth")
        
        if query.next() and query.value(0) == 0:
            
            # Insert default user
            query.prepare("""
                    INSERT INTO auth (firstname, lastname, email, username, password_hash, salt, role, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """)
                
            password = os.environ.get("MEDIC_DEFAULT_ADMIN_PASSWORD")
            generated_password = False
            if not password:
                # Generate a one-time bootstrap password when no explicit seed is provided.
                password = secrets.token_urlsafe(12)
                generated_password = True
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
                if generated_password:
                    QMessageBox.information(
                        None,
                        "Default Admin Credentials",
                        (
                            "A bootstrap admin account has been created.\n"
                            "Username: admin\n"
                            f"Temporary Password: {password}\n\n"
                            "Please sign in and change this password immediately."
                        ),
                    )
            
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
            AppMessageBox.critical(
                None,
                "Error",
                f"Table creation failed: {query.lastError().text()}"
            )
            return False

        print("Table 'Accounting Settings' ready.")
        return True
            
        

    
    
    def create_daily_session_table(self):

        query = QSqlQuery()

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS daily_session (
                
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                session_date TEXT NOT NULL,

                opening_cash REAL NOT NULL,
                opening_note TEXT,

                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                system_cash REAL,
                actual_cash REAL,
                withdrawal REAL DEFAULT 0,
                cash_difference REAL,

                closing_note TEXT,
                closed_at TIMESTAMP,

                status TEXT DEFAULT 'open'
            )
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        # Ensure database-level integrity: at most one open session can exist.
        if not query.exec("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_daily_session_single_open
            ON daily_session(status)
            WHERE status = 'open'
        """):
            AppMessageBox.critical(None, "Error", f"Index creation failed: {query.lastError().text()}")
            return False

        # Defensive triggers for compatibility with older SQLite engines or edge writes.
        if not query.exec("""
            CREATE TRIGGER IF NOT EXISTS trg_daily_session_single_open_insert
            BEFORE INSERT ON daily_session
            WHEN NEW.status = 'open'
             AND EXISTS (SELECT 1 FROM daily_session WHERE status = 'open')
            BEGIN
                SELECT RAISE(ABORT, 'Only one open daily session is allowed.');
            END;
        """):
            AppMessageBox.critical(None, "Error", f"Trigger creation failed: {query.lastError().text()}")
            return False

        if not query.exec("""
            CREATE TRIGGER IF NOT EXISTS trg_daily_session_single_open_update
            BEFORE UPDATE OF status ON daily_session
            WHEN NEW.status = 'open'
             AND EXISTS (
                SELECT 1
                FROM daily_session
                WHERE status = 'open'
                  AND id <> NEW.id
             )
            BEGIN
                SELECT RAISE(ABORT, 'Only one open daily session is allowed.');
            END;
        """):
            AppMessageBox.critical(None, "Error", f"Trigger creation failed: {query.lastError().text()}")
            return False

        return True
    
    
        
        
        

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
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'employee' ready.")
        return True




    
        
        
        
        
    def create_customer_table(self):
        
        query = QSqlQuery()
        print("Creating Customer Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS customer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                email TEXT,
                status TEXT DEFAULT 'active',
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payable REAL DEFAULT 0.00,
                receiveable REAL DEFAULT 0.00,
                credit_limit REAL DEFAULT 0.00,
                discount_group_id INTEGER,
                tax_group_id INTEGER
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'customer' ready.")
        return True

    def create_discount_group_table(self):
        query = QSqlQuery()
        print("Creating Discount Group Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS discount_group (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                discount_percent REAL DEFAULT 0.00,
                status TEXT DEFAULT 'active',
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """):
            AppMessageBox.critical(None, "Error", f"Discount group table creation failed: {query.lastError().text()}")
            return False

        print("Table 'discount_group' ready.")
        return True

    def create_tax_group_table(self):
        query = QSqlQuery()
        print("Creating Tax Group Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS tax_group (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                tax_percent REAL DEFAULT 0.00,
                status TEXT DEFAULT 'active',
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """):
            AppMessageBox.critical(None, "Error", f"Tax group table creation failed: {query.lastError().text()}")
            return False

        print("Table 'tax_group' ready.")
        return True

    def seed_discount_group_table(self):
        query = QSqlQuery()
        query.prepare("""
            INSERT OR IGNORE INTO discount_group (name, discount_percent, status)
            VALUES (?, ?, 'active')
        """)
        query.addBindValue("No Discount")
        query.addBindValue(0.0)
        if not query.exec():
            print("Discount group seed failed:", query.lastError().text())

    def seed_tax_group_table(self):
        query = QSqlQuery()
        query.prepare("""
            INSERT OR IGNORE INTO tax_group (name, tax_percent, status)
            VALUES (?, ?, 'active')
        """)
        query.addBindValue("No Tax")
        query.addBindValue(0.0)
        if not query.exec():
            print("Tax group seed failed:", query.lastError().text())
 
 
 
        
    
    def create_rep_table(self):
        
        query = QSqlQuery()
        print("Creating Rep Table")

        # Check if table exists
        if not query.exec("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name='rep';
        """):
            AppMessageBox.critical(None, "Error", f"Table check failed: {query.lastError().text()}")
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
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'rep' created successfully.")
        return True
 
    
    
    
    
    def create_manufacturer_table(self):

        query = QSqlQuery()
        print("Creating Manufacturer Table")

        # Check if table exists
        if not query.exec("""
            SELECT EXISTS (
                SELECT 1
                FROM sqlite_master
                WHERE type='table'
                AND name='manufacturer'
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table check failed: {query.lastError().text()}")
            return False

        query.next()
        table_exists = query.value(0)

        if table_exists:
            print("Table 'manufacturer' already exists - skipping creation.")
            return True

        # Create table
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS manufacturer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'manufacturer' created successfully.")

        # Create index for faster search
        if not query.exec("""
            CREATE INDEX IF NOT EXISTS idx_manufacturer_name
            ON manufacturer(name);
        """):
            AppMessageBox.critical(None, "Error", f"Index creation failed: {query.lastError().text()}")
            return False

        print("Index created successfully (manufacturer name).")

        return self.populate_manufacturers_from_csv()
        



    def populate_manufacturers_from_csv(self, file_path = resource_path("manufacturers.csv")):
        
        if not os.path.exists(file_path):
            print(f"Manufacturer file not found: {file_path}")
            return 0

        db = QSqlDatabase.database()

        if not db.transaction():
            print("Failed to start manufacturer transaction.")
            return 0

        query = QSqlQuery(db)
        query.prepare("""
            INSERT OR IGNORE INTO manufacturer (name)
            VALUES (?)
        """)

        imported_count = 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip()

                    if not name:
                        continue

                    query.addBindValue(name)

                    if not query.exec():
                        raise Exception(query.lastError().text())

                    imported_count += max(0, int(query.numRowsAffected() or 0))

            if not db.commit():
                raise Exception("Failed to commit manufacturer transaction.")

            print(f"Manufacturers imported successfully: {imported_count}")
            return imported_count

        except Exception as e:
            db.rollback()
            print("Manufacturer import failed:", str(e))
            return 0
        
        
       
        import csv




    def build_display_name(self, brand: str, form: str, strength: str) -> str:
        
        parts = []

        if brand:
            parts.append(str(brand).strip())

        if form:
            parts.append(str(form).strip())

        if strength:
            parts.append(str(strength).strip())

        return " ".join(parts)


    def populate_products_from_csv(self, file_path = resource_path("master_products.csv")):
        
        if not os.path.exists(file_path):
            print(f"Product file not found: {file_path}")
            return 0

        db = QSqlDatabase.database()

        if not db.transaction():
            print("Failed to start product transaction.")
            return 0

        query = QSqlQuery(db)
        query.prepare("""
            INSERT INTO product (
                display_name,
                code,
                reg_no,
                generic_name,
                brand,
                form,
                strength,
                packing,
                manufacturer_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        price_query = QSqlQuery(db)
        price_query.prepare("""
            INSERT INTO price_pack (
                product_id,
                pack_size,
                pack_price
            )
            VALUES (?, ?, ?)
        """)

        imported_count = 0

        try:
            with open(file_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)

                next(reader, None)  # skip header

                for row in reader:
                    if not row or len(row) < 8:
                        continue

                    reg_no = row[0].strip()
                    brand = row[1].strip()
                    generic_name = row[2].strip()
                    form = row[3].strip()
                    strength = row[4].strip()
                    packing = row[5].strip()
                    size = row[6].strip()
                    manufacturer_id = row[7].strip()

                    display_name = self.build_display_name(brand, form, strength)

                    pack_size = int(size) if size else 1
                    manufacturer_id = int(manufacturer_id) if manufacturer_id else None

                    query.addBindValue(display_name)
                    query.addBindValue(None)  # code
                    query.addBindValue(reg_no)
                    query.addBindValue(generic_name)
                    query.addBindValue(brand)
                    query.addBindValue(form)
                    query.addBindValue(strength)
                    query.addBindValue(packing)
                    query.addBindValue(manufacturer_id)

                    if not query.exec():
                        raise Exception(query.lastError().text())

                    product_id = query.lastInsertId()

                    price_query.addBindValue(product_id)
                    price_query.addBindValue(pack_size)
                    price_query.addBindValue(0)

                    if not price_query.exec():
                        raise Exception(price_query.lastError().text())

                    imported_count += 1

            if not db.commit():
                raise Exception("Failed to commit product transaction.")

            print(f"Products imported successfully: {imported_count}")
            return imported_count

        except Exception as e:
            db.rollback()
            print("Product import failed:", str(e))
            return 0
        
    
    def create_product_table(self):
    
        query = QSqlQuery()
        print("Creating Product Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS product (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,              -- e.g. "Panadol Tab 10mg"
                code TEXT UNIQUE,                        -- barcode / internal code
                reg_no TEXT,                             -- optional registration number
                generic_name TEXT,                       -- e.g. Paracetamol
                brand TEXT NOT NULL,                     -- e.g. Panadol
                form TEXT,                               -- e.g. Tab
                strength TEXT,                           -- e.g. 10mg
                packing TEXT,                            -- e.g. 10x10s
                manufacturer_id INTEGER,                 -- FK to manufacturer table
                discount_group_id INTEGER,
                tax_group_id INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manufacturer_id) REFERENCES manufacturer(id),
                FOREIGN KEY (discount_group_id) REFERENCES discount_group(id),
                FOREIGN KEY (tax_group_id) REFERENCES tax_group(id)
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'product' created successfully.")

        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_product_display_name   ON product(display_name)",
            "CREATE INDEX IF NOT EXISTS idx_product_code           ON product(code)",
            "CREATE INDEX IF NOT EXISTS idx_product_brand          ON product(brand)",
            "CREATE INDEX IF NOT EXISTS idx_product_generic_name   ON product(generic_name)",
            "CREATE INDEX IF NOT EXISTS idx_product_form           ON product(form)",
            "CREATE INDEX IF NOT EXISTS idx_product_strength       ON product(strength)",
            "CREATE INDEX IF NOT EXISTS idx_product_manufacturer   ON product(manufacturer_id)"
        ]

        for index_query in indexes:
            if not query.exec(index_query):
                AppMessageBox.critical(None, "Error", f"Index creation failed: {query.lastError().text()}")
                return False

        print("Indexes created successfully.")
        return True


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
                reorder_level INTEGER DEFAULT 0,
                is_default BOOLEAN DEFAULT 1
            );

        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'price_pack' created successfully.")
        return True


    def create_price_changes_table(self):
        
        query = QSqlQuery()
        print("Creating price_changes Table")

        # Create table if it doesn't exist
        if not query.exec("""
           
            CREATE TABLE IF NOT EXISTS price_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                previous_price REAL NOT NULL,
                new_price REAL NOT NULL,
                source TEXT DEFAULT 'unknown',
                user_id INTEGER,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (product_id) REFERENCES product(id),
                FOREIGN KEY (user_id) REFERENCES auth(id)
            );

        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'price_changes' created successfully.")
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
                purchaseitem_id INTEGER,
                total_received INTEGER NOT NULL,
                paid_qty INTEGER NOT NULL,
                quantity_remaining INTEGER NOT NULL,
                unit_cost REAL,                      -- NULL allowed (opening stock)
                source TEXT,                         -- 'opening', 'purchase'
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (product_id) REFERENCES product(id),
                FOREIGN KEY (purchaseitem_id) REFERENCES purchaseitem(id)
            
            
            
            );

        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
                qty INTEGER NOT NULL,         -- always positive difference
                adjustment_type TEXT NOT NULL DEFAULT 'deduction',
                old_qty INTEGER NOT NULL,
                new_qty INTEGER NOT NULL,
                reason TEXT NOT NULL,         -- 'expired', 'damaged', 'lost', etc.
                note TEXT,                    -- optional human explanation
                adjusted_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (batch_id) REFERENCES batch(id),
                FOREIGN KEY (adjusted_by) REFERENCES auth(id),
                CHECK (adjustment_type IN ('deduction', 'addition')),
                CHECK (qty >= 0),
                CHECK (old_qty >= 0),
                CHECK (new_qty >= 0)
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'inventory_adjustment' created successfully.")
        return True


    def create_activity_log_table(self):

        query = QSqlQuery()
        print("Creating activity_log Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                login_session_id  TEXT,
                daily_session_id  INTEGER,
                timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id           INTEGER,
                username          TEXT,
                category          TEXT NOT NULL,
                action            TEXT NOT NULL,
                entity_type       TEXT,
                entity_id         INTEGER,
                note              TEXT,
                previous_value    TEXT,
                new_value         TEXT,
                FOREIGN KEY (daily_session_id) REFERENCES daily_session(id),
                FOREIGN KEY (user_id) REFERENCES auth(id)
            );
        """):
            print("activity_log table creation failed:", query.lastError().text())
            return False

        print("Table 'activity_log' created successfully.")
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
                receivable DECIMAL(10,2) NOT NULL,
                due_date DATE,
                session_id INTEGER NOT NULL,
                
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier) REFERENCES supplier(id) ON DELETE RESTRICT,
                FOREIGN KEY (rep) REFERENCES rep(id) ON DELETE RESTRICT,
                FOREIGN KEY (session_id) REFERENCES daily_session(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
                session_id INTEGER NOT NULL,
                
                payment_method TEXT,
                bank_name TEXT,
                account_no TEXT,
                transaction_mode TEXT,
                wallet_provider TEXT,
                wallet_no TEXT,
                payment_reference TEXT,

                FOREIGN KEY (supplier) REFERENCES supplier(id) ON DELETE RESTRICT,
                FOREIGN KEY (rep) REFERENCES rep(id) ON DELETE RESTRICT,
                FOREIGN KEY (ref) REFERENCES purchase(id) ON DELETE RESTRICT,
                FOREIGN KEY (return_ref) REFERENCES purchase_return(id) ON DELETE RESTRICT,
                FOREIGN KEY (session_id) REFERENCES daily_session(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
                
                payment_method TEXT,
                bank_name TEXT,
                account_no TEXT,
                transaction_mode TEXT,
                wallet_provider TEXT,
                wallet_no TEXT,
                payment_reference TEXT,

                salesman INTEGER,
                note TEXT,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id INTEGER NOT NULL,

                FOREIGN KEY (customer) REFERENCES customer(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesman) REFERENCES employee(id) ON DELETE RESTRICT,
                FOREIGN KEY (ref) REFERENCES sales(id) ON DELETE RESTRICT,
                FOREIGN KEY (return_ref) REFERENCES salesreturn(id) ON DELETE RESTRICT,
                FOREIGN KEY (session_id) REFERENCES daily_session(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
                landing_cost DECIMAL(10,2),  -- Total cost per unit including proportional header fees (taxes, discounts)
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (purchase) REFERENCES purchase(id) ON DELETE RESTRICT,
                FOREIGN KEY (product) REFERENCES product(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
                session_id INTEGER NOT NULL,

                FOREIGN KEY (supplier) REFERENCES supplier(id) ON DELETE RESTRICT,
                FOREIGN KEY (rep) REFERENCES rep(id) ON DELETE RESTRICT,
                FOREIGN KEY (session_id) REFERENCES daily_session(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
                due_date DATE,
                session_id INTEGER NOT NULL,
                
                FOREIGN KEY (customer) REFERENCES customer(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesman) REFERENCES auth(id) ON DELETE RESTRICT,
                FOREIGN KEY (session_id) REFERENCES daily_session(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
                discount_amount REAL DEFAULT 0.00,
                tax_amount REAL DEFAULT 0.00,
                discount_input_mode TEXT DEFAULT 'percent',
                default_discount_group_id INTEGER,
                default_tax_group_id INTEGER,
                discount_group_id INTEGER,
                tax_group_id INTEGER,
                discount_source TEXT DEFAULT 'manual_override',
                tax_source TEXT DEFAULT 'manual_override',
                line_total REAL NOT NULL,
                
                line_weight DECIMAL(10,2) NOT NULL,
                effective_line_total DECIMAL(10,2) NOT NULL,
                
                
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sales_id) REFERENCES sales(id) ON DELETE RESTRICT,
                FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT,
                FOREIGN KEY (default_discount_group_id) REFERENCES discount_group(id) ON DELETE RESTRICT,
                FOREIGN KEY (default_tax_group_id) REFERENCES tax_group(id) ON DELETE RESTRICT,
                FOREIGN KEY (discount_group_id) REFERENCES discount_group(id) ON DELETE RESTRICT,
                FOREIGN KEY (tax_group_id) REFERENCES tax_group(id) ON DELETE RESTRICT
            );
        """):
            
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'sold_batch' created successfully.")
        return True
    
    
    
    
    def create_holdsale_table(self):
        query = QSqlQuery()
        print("Creating holdsale Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS holdsale (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer INTEGER,
                salesman INTEGER,
                status TEXT,
                subtotal REAL DEFAULT 0.00,
                discount_amount REAL DEFAULT 0.00,
                taxable_amount REAL DEFAULT 0.00,
                tax_amount REAL DEFAULT 0.00,
                additional_charges REAL DEFAULT 0.00,
                final_amount REAL DEFAULT 0.00,
                received_amount REAL DEFAULT 0.00,
                remaining_amount REAL DEFAULT 0.00,
                payment_method TEXT,
                due_date DATE,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer) REFERENCES customer(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesman) REFERENCES employee(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'holdsale' created successfully.")
        return True
   
        
        
    
    def create_holdsale_items_table(self):
        query = QSqlQuery()
        print("Creating holditems Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS holditems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                holdsale INTEGER NOT NULL,
                product INTEGER NOT NULL,
                qty INTEGER NOT NULL,
                unitrate DECIMAL(10,2) NOT NULL,
                discount DECIMAL(10,2) NOT NULL,
                discountamount DECIMAL(10,2) NOT NULL,
                tax REAL DEFAULT 0.00,
                taxamount REAL DEFAULT 0.00,
                discount_input_mode TEXT DEFAULT 'percent',
                total DECIMAL(10,2) NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (holdsale) REFERENCES holdsale(id) ON DELETE RESTRICT,
                FOREIGN KEY (product) REFERENCES product(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
                session_id INTEGER NOT NULL,
                
                
                FOREIGN KEY (customer) REFERENCES customer(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesman) REFERENCES employee(id) ON DELETE RESTRICT,
                FOREIGN KEY (salesorder) REFERENCES sales(id) ON DELETE RESTRICT,
                FOREIGN KEY (session_id) REFERENCES daily_session(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
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
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id INTEGER NOT NULL,
                
                payment_method TEXT,
                bank_name TEXT,
                account_no TEXT,
                transaction_mode TEXT,
                wallet_provider TEXT,
                wallet_no TEXT,
                payment_reference TEXT,
                
                user_id INTEGER,
                
                FOREIGN KEY (user_id) REFERENCES auth(id) ON DELETE RESTRICT,
                FOREIGN KEY (session_id) REFERENCES daily_session(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'expense' created successfully.")
        return True

    
    
    

    def create_purchase_order_table(self):
        query = QSqlQuery()
        print("Creating Purchase Order Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS purchase_order (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT UNIQUE NOT NULL,
                supplier INTEGER NOT NULL,
                po_date TEXT NOT NULL,
                expected_delivery_date TEXT,
                status TEXT DEFAULT 'draft',
                total_value DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                notes TEXT,
                session_id INTEGER,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (supplier) REFERENCES supplier(id) ON DELETE RESTRICT,
                FOREIGN KEY (session_id) REFERENCES daily_session(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'purchase_order' created successfully.")
        return True


    def create_purchase_order_line_table(self):
        query = QSqlQuery()
        print("Creating Purchase Order Line Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS purchase_order_line (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id INTEGER NOT NULL,
                product INTEGER NOT NULL,
                qty_ordered INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (po_id) REFERENCES purchase_order(id) ON DELETE RESTRICT,
                FOREIGN KEY (product) REFERENCES product(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'purchase_order_line' created successfully.")
        return True


    def create_goods_receipt_table(self):
        query = QSqlQuery()
        print("Creating Goods Receipt Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS goods_receipt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grn_number TEXT UNIQUE NOT NULL,
                po_id INTEGER NOT NULL,
                grn_date TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                total_value DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                header_discount DECIMAL(10,2) DEFAULT 0.00,  -- Header-level discount applied to all lines
                header_tax DECIMAL(10,2) DEFAULT 0.00,        -- Header-level tax applied to all lines
                discount DECIMAL(10,2) DEFAULT 0.00,
                tax_236g DECIMAL(10,2) DEFAULT 0.00,
                tax_236h DECIMAL(10,2) DEFAULT 0.00,
                salestax DECIMAL(10,2) DEFAULT 0.00,
                cn_adjustment DECIMAL(10,2) DEFAULT 0.00,
                taxable DECIMAL(10,2) DEFAULT 0.00,
                netamount DECIMAL(10,2) DEFAULT 0.00,
                notes TEXT,
                session_id INTEGER,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (po_id) REFERENCES purchase_order(id) ON DELETE RESTRICT,
                FOREIGN KEY (session_id) REFERENCES daily_session(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'goods_receipt' created successfully.")
        return True


    def create_goods_receipt_line_table(self):
        query = QSqlQuery()
        print("Creating Goods Receipt Line Table")

        if not query.exec("""
            CREATE TABLE IF NOT EXISTS goods_receipt_line (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grn_id INTEGER NOT NULL,
                po_line_id INTEGER NOT NULL,
                qty_received INTEGER NOT NULL,
                unit_price_received DECIMAL(10,2) NOT NULL,
                total_received DECIMAL(10,2) NOT NULL,
                
                batch_no TEXT,                       -- Manufacturer lot/batch number (optional)
                expiry_date DATE,                    -- Expiry date (optional)
                discount DECIMAL(10,2) DEFAULT 0.00,  -- Line-item discount amount
                tax DECIMAL(10,2) DEFAULT 0.00,        -- Line-item tax amount
                landing_cost DECIMAL(10,2),  -- Total cost per unit including proportional header fees
                
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (grn_id) REFERENCES goods_receipt(id) ON DELETE RESTRICT,
                FOREIGN KEY (po_line_id) REFERENCES purchase_order_line(id) ON DELETE RESTRICT
            );
        """):
            AppMessageBox.critical(None, "Error", f"Table creation failed: {query.lastError().text()}")
            return False

        print("Table 'goods_receipt_line' created successfully.")
        return True

    

from utilities.license import ensure_valid_license
from utilities.app_messagebox import AppMessageBox

if __name__ == '__main__':

    app = QApplication([])

    if not ensure_valid_license():
        sys.exit(0)

    window = AuthWindow()
    window.show()

    sys.exit(app.exec())
    
    
    
