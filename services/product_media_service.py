import mimetypes
import os
import shutil
from datetime import datetime

from PySide6.QtSql import QSqlQuery

try:
    from medic.utilities.database import SQLiteConnectionManager
except ModuleNotFoundError:
    from utilities.database import SQLiteConnectionManager


def _new_query():
    return QSqlQuery()


def ensure_product_media_schema():
    query = _new_query()
    required_columns = {
        "media_original_filename": "TEXT",
        "media_stored_filename": "TEXT",
        "media_relative_path": "TEXT",
        "media_mime_type": "TEXT",
    }

    existing = set()
    if not query.exec("PRAGMA table_info(product)"):
        raise Exception(f"Product schema check failed: {query.lastError().text()}")
    while query.next():
        existing.add(str(query.value(1) or "").strip().lower())

    for column_name, column_sql in required_columns.items():
        if column_name.lower() in existing:
            continue
        if not query.exec(f"ALTER TABLE product ADD COLUMN {column_name} {column_sql}"):
            raise Exception(f"Product media migration failed for {column_name}: {query.lastError().text()}")

    return True


def get_product_media_dir():
    manager = SQLiteConnectionManager("ProcureApp")
    media_dir = manager.get_product_media_storage_dir()
    _migrate_legacy_product_media(media_dir)
    return media_dir


def _get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_legacy_product_media_dir():
    return os.path.join(_get_project_root(), "storage", "product_media")


def _migrate_legacy_product_media(target_dir):
    legacy_dir = _get_legacy_product_media_dir()
    if not os.path.isdir(legacy_dir):
        return
    for name in os.listdir(legacy_dir):
        source_path = os.path.join(legacy_dir, name)
        target_path = os.path.join(target_dir, name)
        if not os.path.isfile(source_path) or os.path.exists(target_path):
            continue
        try:
            shutil.copy2(source_path, target_path)
        except OSError:
            continue


def save_product_media(source_path, *, product_id):
    source_path = str(source_path or "").strip()
    if not source_path:
        return None
    if not os.path.exists(source_path):
        raise Exception("Selected product media file could not be found.")

    media_dir = get_product_media_dir()
    original_filename = os.path.basename(source_path)
    _, extension = os.path.splitext(original_filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stored_filename = f"product_{int(product_id)}_{timestamp}{extension.lower()}"
    destination_path = os.path.join(media_dir, stored_filename)
    shutil.copy2(source_path, destination_path)

    mime_type = mimetypes.guess_type(original_filename)[0] or ""
    relative_path = os.path.join("product_media", stored_filename)
    return {
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "relative_path": relative_path,
        "mime_type": mime_type,
        "absolute_path": destination_path,
    }


def update_product_media_fields(*, product_id, media_info):
    query = _new_query()
    query.prepare(
        """
        UPDATE product
        SET
            media_original_filename = ?,
            media_stored_filename = ?,
            media_relative_path = ?,
            media_mime_type = ?
        WHERE id = ?
        """
    )
    query.addBindValue((media_info or {}).get("original_filename") or None)
    query.addBindValue((media_info or {}).get("stored_filename") or None)
    query.addBindValue((media_info or {}).get("relative_path") or None)
    query.addBindValue((media_info or {}).get("mime_type") or None)
    query.addBindValue(product_id)
    if not query.exec():
        raise Exception(f"Failed to save product media fields: {query.lastError().text()}")
    return True


def clear_product_media_fields(*, product_id):
    query = _new_query()
    query.prepare(
        """
        UPDATE product
        SET
            media_original_filename = NULL,
            media_stored_filename = NULL,
            media_relative_path = NULL,
            media_mime_type = NULL
        WHERE id = ?
        """
    )
    query.addBindValue(product_id)
    if not query.exec():
        raise Exception(f"Failed to clear product media fields: {query.lastError().text()}")
    return True


def fetch_product_media(product_id):
    ensure_product_media_schema()
    query = _new_query()
    query.prepare(
        """
        SELECT
            COALESCE(media_original_filename, ''),
            COALESCE(media_stored_filename, ''),
            COALESCE(media_relative_path, ''),
            COALESCE(media_mime_type, '')
        FROM product
        WHERE id = ?
        LIMIT 1
        """
    )
    query.addBindValue(product_id)
    if not query.exec() or not query.next():
        return None

    relative_path = str(query.value(2) or "").strip()
    if not relative_path:
        return None

    media_root = get_product_media_dir()
    if relative_path.startswith("storage/") or relative_path.startswith("storage\\"):
        absolute_path = os.path.normpath(os.path.join(_get_project_root(), relative_path))
        if not os.path.exists(absolute_path):
            absolute_path = os.path.join(media_root, os.path.basename(relative_path))
    else:
        absolute_path = os.path.normpath(os.path.join(os.path.dirname(media_root), relative_path))

    return {
        "original_filename": str(query.value(0) or "").strip(),
        "stored_filename": str(query.value(1) or "").strip(),
        "relative_path": relative_path,
        "mime_type": str(query.value(3) or "").strip(),
        "absolute_path": absolute_path,
    }
