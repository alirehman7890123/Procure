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
import datetime
import sqlite3
import shutil
from PySide6.QtSql import QSqlDatabase
from PySide6.QtCore import QObject


class SQLiteConnectionManager(QObject):
    def __init__(self, app_name="MyApp"):
        super().__init__()
        self.app_name = app_name
        self.db_path = self.get_database_path()
        self.ops_db_path = os.path.join(os.path.dirname(self.db_path), "procure_ops.sqlite")
        if QSqlDatabase.contains("qt_sql_default_connection"):
            self.db = QSqlDatabase.database("qt_sql_default_connection")
            if not self.db.databaseName():
                self.db.setDatabaseName(self.db_path)
        else:
            self.db = QSqlDatabase.addDatabase("QSQLITE")
            self.db.setDatabaseName(self.db_path)

    def get_database_path(self):
        """Return OS-appropriate location for storing the SQLite DB."""
        app_dir = self.get_app_data_dir()
        return os.path.join(app_dir, "procuredb.sqlite")

    def get_app_data_dir(self):
        if sys.platform.startswith("win"):
            base_dir = os.getenv("APPDATA")
        elif sys.platform == "darwin":  # macOS
            base_dir = os.path.expanduser("~/Library/Application Support")
        else:  # Linux and others
            base_dir = os.path.expanduser("~/.local/share")

        app_dir = os.path.join(base_dir, self.app_name)
        os.makedirs(app_dir, exist_ok=True)  # ensure folder exists
        return app_dir

    def get_prescription_storage_dir(self):
        path = os.path.join(self.get_app_data_dir(), "prescriptions")
        os.makedirs(path, exist_ok=True)
        return path

    def get_product_media_storage_dir(self):
        path = os.path.join(self.get_app_data_dir(), "product_media")
        os.makedirs(path, exist_ok=True)
        return path

    def _get_backup_assets_dir(self, backup_file):
        backup_file = str(backup_file or "").strip()
        if not backup_file:
            return ""
        if backup_file.endswith(".sqlite"):
            return backup_file[:-7] + "_assets"
        return backup_file + "_assets"

    def _copy_prescription_assets_to_backup(self, backup_file):
        source_dir = self.get_prescription_storage_dir()
        target_root = self._get_backup_assets_dir(backup_file)
        if not target_root:
            return

        if os.path.isdir(target_root):
            shutil.rmtree(target_root, ignore_errors=True)

        target_dir = os.path.join(target_root, "prescriptions")
        if not os.path.isdir(source_dir):
            return

        os.makedirs(target_root, exist_ok=True)
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)

    def _copy_product_media_assets_to_backup(self, backup_file):
        source_dir = self.get_product_media_storage_dir()
        target_root = self._get_backup_assets_dir(backup_file)
        if not target_root:
            return

        target_dir = os.path.join(target_root, "product_media")
        if not os.path.isdir(source_dir):
            return

        os.makedirs(target_root, exist_ok=True)
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)

    def _restore_prescription_assets_from_backup(self, backup_file):
        backup_assets_root = self._get_backup_assets_dir(backup_file)
        backup_prescriptions = os.path.join(backup_assets_root, "prescriptions")
        target_dir = self.get_prescription_storage_dir()

        if os.path.isdir(target_dir):
            shutil.rmtree(target_dir, ignore_errors=True)
        os.makedirs(target_dir, exist_ok=True)

        if os.path.isdir(backup_prescriptions):
            shutil.copytree(backup_prescriptions, target_dir, dirs_exist_ok=True)

    def _restore_product_media_assets_from_backup(self, backup_file):
        backup_assets_root = self._get_backup_assets_dir(backup_file)
        backup_media = os.path.join(backup_assets_root, "product_media")
        target_dir = self.get_product_media_storage_dir()

        if os.path.isdir(target_dir):
            shutil.rmtree(target_dir, ignore_errors=True)
        os.makedirs(target_dir, exist_ok=True)

        if os.path.isdir(backup_media):
            shutil.copytree(backup_media, target_dir, dirs_exist_ok=True)

    def open(self):
        if not self.db.open():
            raise Exception(f"Database connection failed: {self.db.lastError().text()}")
        print(f"Database opened at {self.db_path}")
        return self.db

    def close(self):
        print("Closing database connection...")
        self.db.close()

    def get_backup_dir(self, backup_dir=None):
        if backup_dir:
            return backup_dir
        return os.path.join(os.path.dirname(self.db_path), "backups")

    def _ops_conn(self):
        os.makedirs(os.path.dirname(self.ops_db_path), exist_ok=True)
        return sqlite3.connect(self.ops_db_path)

    def ensure_backup_tables(self):
        conn = None
        try:
            conn = self._ops_conn()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS backup_run_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                    status TEXT NOT NULL,
                    trigger_source TEXT NOT NULL,
                    backup_file TEXT,
                    backup_size INTEGER,
                    message TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS restore_run_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                    status TEXT NOT NULL,
                    backup_file TEXT,
                    message TEXT
                )
            """)
            conn.commit()
        except Exception as exc:
            print("ensure backup/restore log tables failed:", str(exc))
        finally:
            if conn is not None:
                conn.close()

    def log_backup_run(self, status, trigger_source, backup_file=None, backup_size=None, message=""):
        self.ensure_backup_tables()
        conn = None
        try:
            conn = self._ops_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO backup_run_log (
                    run_at, status, trigger_source, backup_file, backup_size, message
                ) VALUES (
                    datetime('now','localtime'), ?, ?, ?, ?, ?
                )
                """,
                (
                    str(status or "failed"),
                    str(trigger_source or "manual"),
                    str(backup_file or ""),
                    int(backup_size or 0),
                    str(message or ""),
                ),
            )
            conn.commit()
        except Exception as exc:
            print("backup_run_log insert failed:", str(exc))
        finally:
            if conn is not None:
                conn.close()

    def log_restore_run(self, status, backup_file=None, message=""):
        self.ensure_backup_tables()
        conn = None
        try:
            conn = self._ops_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO restore_run_log (
                    run_at, status, backup_file, message
                ) VALUES (
                    datetime('now','localtime'), ?, ?, ?
                )
                """,
                (
                    str(status or "failed"),
                    str(backup_file or ""),
                    str(message or ""),
                ),
            )
            conn.commit()
        except Exception as exc:
            print("restore_run_log insert failed:", str(exc))
        finally:
            if conn is not None:
                conn.close()

    def validate_backup_file(self, backup_file):
        result = {
            "ok": False,
            "message": "",
            "table_count": 0,
            "required_tables_found": 0,
            "required_tables_total": 3,
        }

        backup_file = str(backup_file or "").strip()
        if not backup_file:
            result["message"] = "Backup file path is empty."
            return result

        if not os.path.exists(backup_file):
            result["message"] = "Backup file does not exist."
            return result

        conn = None
        try:
            conn = sqlite3.connect(backup_file)
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check")
            integrity = cur.fetchone()
            integrity_text = str((integrity[0] if integrity else "") or "")
            if integrity_text.lower() != "ok":
                result["message"] = f"Integrity check failed: {integrity_text}"
                return result

            cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            result["table_count"] = int((cur.fetchone() or [0])[0] or 0)

            required = ["product", "sales", "batch"]
            found = 0
            for table_name in required:
                cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (table_name,))
                if cur.fetchone():
                    found += 1

            result["required_tables_found"] = found
            if found != len(required):
                result["message"] = "Backup is missing required core tables."
                return result

            result["ok"] = True
            result["message"] = "Backup file is valid."
            return result

        except Exception as exc:
            result["message"] = f"Validation failed: {str(exc)}"
            return result
        finally:
            if conn is not None:
                conn.close()

    def restore_from_backup(self, backup_file, create_pre_restore_backup=True):
        backup_file = str(backup_file or "").strip()
        if not backup_file:
            raise Exception("No backup file selected for restore.")

        validation = self.validate_backup_file(backup_file)
        if not validation.get("ok"):
            msg = str(validation.get("message") or "Backup validation failed")
            self.log_restore_run(status="failed", backup_file=backup_file, message=msg)
            raise Exception(msg)

        pre_restore_file = ""
        pre_restore_warning = ""
        if create_pre_restore_backup:
            try:
                pre_restore_file = self.backup(trigger_source="pre_restore")
            except Exception as exc:
                # Best effort only: do not block restore if current DB is already damaged.
                pre_restore_warning = f"Pre-restore backup failed: {str(exc)}"

        qt_db = QSqlDatabase.database("qt_sql_default_connection")
        was_open = qt_db.isValid() and qt_db.isOpen()
        if was_open:
            qt_db.close()

        source_conn = None
        target_conn = None
        corrupt_snapshot = ""
        try:
            # Move current file out of the way first; malformed DB can fail when opened as restore target.
            if os.path.exists(self.db_path):
                stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                corrupt_snapshot = f"{self.db_path}.pre_restore_{stamp}.bak"
                os.replace(self.db_path, corrupt_snapshot)

            source_conn = sqlite3.connect(backup_file)
            target_conn = sqlite3.connect(self.db_path)

            # Create a fresh target from selected backup.
            source_conn.backup(target_conn)
            self._restore_prescription_assets_from_backup(backup_file)
            self._restore_product_media_assets_from_backup(backup_file)

            success_msg = f"Restore completed. Pre-restore backup: {pre_restore_file}"
            if pre_restore_warning:
                success_msg = f"{success_msg}. {pre_restore_warning}"

            self.log_restore_run(
                status="success",
                backup_file=backup_file,
                message=success_msg,
            )

            # Keep only one previous snapshot for forensic fallback; optional cleanup can be added later.
        except Exception as exc:
            # Attempt rollback to previous file if we already moved it away.
            try:
                if corrupt_snapshot and os.path.exists(corrupt_snapshot) and not os.path.exists(self.db_path):
                    os.replace(corrupt_snapshot, self.db_path)
            except Exception:
                pass
            self.log_restore_run(status="failed", backup_file=backup_file, message=str(exc))
            raise
        finally:
            if target_conn is not None:
                target_conn.close()
            if source_conn is not None:
                source_conn.close()

        if qt_db.isValid():
            if not qt_db.open():
                raise Exception(f"Restore done, but reopening DB failed: {qt_db.lastError().text()}")

    def prune_backup_files(self, backup_dir=None, keep_last=14):
        backup_dir = self.get_backup_dir(backup_dir)
        if not os.path.isdir(backup_dir):
            return 0

        files = []
        for name in os.listdir(backup_dir):
            if name.startswith("procuredb_backup_") and name.endswith(".sqlite"):
                path = os.path.join(backup_dir, name)
                try:
                    files.append((os.path.getmtime(path), path))
                except OSError:
                    continue

        files.sort(reverse=True)
        to_delete = files[int(max(keep_last, 0)):]

        deleted = 0
        for _, path in to_delete:
            try:
                os.remove(path)
                assets_dir = self._get_backup_assets_dir(path)
                if assets_dir and os.path.isdir(assets_dir):
                    shutil.rmtree(assets_dir, ignore_errors=True)
                deleted += 1
            except OSError:
                continue
        return deleted

    def get_backup_health(self, stale_after_hours=30):
        self.ensure_backup_tables()

        summary = {
            "last_success_at": "",
            "last_success_file": "",
            "last_success_size": 0,
            "last_run_status": "unknown",
            "last_run_message": "",
            "hours_since_success": None,
            "status_level": "warning",
            "status_text": "No successful backup yet.",
        }

        conn = None
        try:
            conn = self._ops_conn()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT status, COALESCE(message, '')
                FROM backup_run_log
                ORDER BY datetime(run_at) DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if row:
                summary["last_run_status"] = str(row[0] or "unknown")
                summary["last_run_message"] = str(row[1] or "")

            cur.execute(
                """
                SELECT
                    run_at,
                    COALESCE(backup_file, ''),
                    COALESCE(backup_size, 0),
                    CAST((julianday('now','localtime') - julianday(run_at)) * 24 AS INTEGER)
                FROM backup_run_log
                WHERE status = 'success'
                ORDER BY datetime(run_at) DESC
                LIMIT 1
                """
            )
            row2 = cur.fetchone()
            if row2:
                summary["last_success_at"] = str(row2[0] or "")
                summary["last_success_file"] = str(row2[1] or "")
                summary["last_success_size"] = int(row2[2] or 0)
                summary["hours_since_success"] = int(row2[3] or 0)
        except Exception as exc:
            print("get_backup_health failed:", str(exc))
        finally:
            if conn is not None:
                conn.close()

        hours = summary.get("hours_since_success")
        if hours is None:
            summary["status_level"] = "critical"
            summary["status_text"] = "No successful backup yet."
        elif hours >= int(stale_after_hours):
            summary["status_level"] = "critical"
            summary["status_text"] = f"Last successful backup is {hours} hour(s) old."
        elif hours >= 24:
            summary["status_level"] = "warning"
            summary["status_text"] = f"Last successful backup is {hours} hour(s) old."
        else:
            summary["status_level"] = "ok"
            summary["status_text"] = f"Last successful backup {hours} hour(s) ago."

        return summary

    def should_run_scheduled_backup(self, interval_hours=24):
        self.ensure_backup_tables()
        interval_hours = max(int(interval_hours or 24), 1)
        conn = None
        try:
            conn = self._ops_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT CAST((julianday('now','localtime') - julianday(run_at)) * 24 AS INTEGER)
                FROM backup_run_log
                WHERE status = 'success'
                ORDER BY datetime(run_at) DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if not row:
                return True
            elapsed = int(row[0] or 0)
            return elapsed >= interval_hours
        except Exception:
            return True
        finally:
            if conn is not None:
                conn.close()

    def get_backup_run_logs(self, limit=100):
        self.ensure_backup_tables()
        limit = max(int(limit or 100), 1)
        rows = []
        conn = None
        try:
            conn = self._ops_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    run_at,
                    COALESCE(status, ''),
                    COALESCE(trigger_source, ''),
                    COALESCE(backup_file, ''),
                    COALESCE(backup_size, 0),
                    COALESCE(message, '')
                FROM backup_run_log
                ORDER BY datetime(run_at) DESC
                LIMIT ?
                """,
                (limit,),
            )
            for row in cur.fetchall():
                rows.append({
                    "run_at": str(row[0] or ""),
                    "status": str(row[1] or ""),
                    "trigger_source": str(row[2] or ""),
                    "backup_file": str(row[3] or ""),
                    "backup_size": int(row[4] or 0),
                    "message": str(row[5] or ""),
                })
        except Exception as exc:
            print("get_backup_run_logs failed:", str(exc))
        finally:
            if conn is not None:
                conn.close()
        return rows

    def get_restore_run_logs(self, limit=50):
        self.ensure_backup_tables()
        limit = max(int(limit or 50), 1)
        rows = []
        conn = None
        try:
            conn = self._ops_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    run_at,
                    COALESCE(status, ''),
                    COALESCE(backup_file, ''),
                    COALESCE(message, '')
                FROM restore_run_log
                ORDER BY datetime(run_at) DESC
                LIMIT ?
                """,
                (limit,),
            )
            for row in cur.fetchall():
                rows.append({
                    "run_at": str(row[0] or ""),
                    "status": str(row[1] or ""),
                    "backup_file": str(row[2] or ""),
                    "message": str(row[3] or ""),
                })
        except Exception as exc:
            print("get_restore_run_logs failed:", str(exc))
        finally:
            if conn is not None:
                conn.close()
        return rows

    def run_scheduled_backup(self, backup_dir=None, interval_hours=24, keep_last=14):
        if not self.should_run_scheduled_backup(interval_hours=interval_hours):
            return None

        try:
            backup_file = self.backup(backup_dir=backup_dir, trigger_source="scheduled")
            self.prune_backup_files(backup_dir=backup_dir, keep_last=keep_last)
            return backup_file
        except Exception as exc:
            self.log_backup_run(
                status="failed",
                trigger_source="scheduled",
                backup_file="",
                backup_size=0,
                message=str(exc),
            )
            raise

    def backup(self, backup_dir=None, trigger_source="manual"):
        """Create a timestamped backup of the database and attachment assets."""
        if not os.path.exists(self.db_path):
            raise Exception("No database file found to backup.")

        self.ensure_backup_tables()

        backup_dir = self.get_backup_dir(backup_dir)

        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"procuredb_backup_{timestamp}.sqlite")

        source_conn = None
        backup_conn = None
        try:
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_file)
            source_conn.backup(backup_conn)
        finally:
            if backup_conn is not None:
                backup_conn.close()
            if source_conn is not None:
                source_conn.close()

        self._copy_prescription_assets_to_backup(backup_file)
        self._copy_product_media_assets_to_backup(backup_file)

        backup_size = 0
        try:
            backup_size = os.path.getsize(backup_file)
        except OSError:
            backup_size = 0

        self.log_backup_run(
            status="success",
            trigger_source=trigger_source,
            backup_file=backup_file,
            backup_size=backup_size,
            message="",
        )

        print(f"Backup created: {backup_file}")
        return backup_file
