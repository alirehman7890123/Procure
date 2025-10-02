# from PySide6.QtSql import QSqlDatabase
# from PySide6.QtCore import QObject

# class PostgresConnectionManager(QObject):
    
#     def __init__(self, host='localhost', port=5432):
#         super().__init__()
#         self.db = QSqlDatabase.addDatabase("QPSQL")
#         self.db.setHostName(host)
#         self.db.setDatabaseName('procuredb')
#         self.db.setUserName('myuser')
#         self.db.setPassword('mypass')
#         self.db.setPort(port)
        
#     def open(self):
#         if not self.db.open():
#             raise Exception(f"Database connection failed: {self.db.lastError().text()}")
#         print("Database connection opened.")
#         return self.db

#     def close(self):
#         print("Closing database connection...")
#         self.db.close()
#         # QSqlDatabase.removeDatabase(self.connection_name)
#         # print("Database connection removed.")



import os
import sys
import shutil
import datetime
from PySide6.QtSql import QSqlDatabase
from PySide6.QtCore import QObject


class SQLiteConnectionManager(QObject):
    def __init__(self, app_name="MyApp"):
        super().__init__()
        self.app_name = app_name
        self.db_path = self.get_database_path()
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(self.db_path)

    def get_database_path(self):
        """Return OS-appropriate location for storing the SQLite DB."""
        if sys.platform.startswith("win"):
            base_dir = os.getenv("APPDATA")
        elif sys.platform == "darwin":  # macOS
            base_dir = os.path.expanduser("~/Library/Application Support")
        else:  # Linux and others
            base_dir = os.path.expanduser("~/.local/share")

        app_dir = os.path.join(base_dir, self.app_name)
        os.makedirs(app_dir, exist_ok=True)  # ensure folder exists
        return os.path.join(app_dir, "procuredb.sqlite")

    def open(self):
        if not self.db.open():
            raise Exception(f"Database connection failed: {self.db.lastError().text()}")
        print(f"Database opened at {self.db_path}")
        return self.db

    def close(self):
        print("Closing database connection...")
        self.db.close()

    def backup(self, backup_dir=None):
        """Create a timestamped backup of the database."""
        if not os.path.exists(self.db_path):
            raise Exception("No database file found to backup.")

        if backup_dir is None:
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")

        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"procuredb_backup_{timestamp}.sqlite")

        shutil.copy2(self.db_path, backup_file)
        print(f"Backup created: {backup_file}")
        return backup_file


