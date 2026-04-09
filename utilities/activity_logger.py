from PySide6.QtWidgets import QApplication
from PySide6.QtSql import QSqlQuery


def log_activity(category, action, entity_type, entity_id, note,
                 previous_value=None, new_value=None):
    """
    Insert a row into activity_log.  Always silent — a failure here must never
    block or roll back the calling business transaction.

    Args:
        category      : 'price' | 'stock' | 'sales' | 'purchase' | 'login' | ...
        action        : 'price_updated' | 'stock_adjusted' | 'login' | ...
        entity_type   : 'product' | 'batch' | 'sale' | 'user' | ...
        entity_id     : integer PK of the affected record (or None)
        note          : human-readable sentence describing the event
        previous_value: old value as plain text  (or None)
        new_value     : new value as plain text  (or None)
    """
    try:
        app = QApplication.instance()
        username = (app.property("username") or "") if app else ""
        user_id = (app.property("user_id")) if app else None
        login_session_id = (app.property("login_session_id") or "") if app else ""

        # Resolve open daily session (best-effort — NULL is fine)
        session_query = QSqlQuery()
        session_query.exec("SELECT id FROM daily_session WHERE status = 'open' ORDER BY id DESC LIMIT 1")
        daily_session_id = None
        if session_query.next():
            daily_session_id = session_query.value(0)

        query = QSqlQuery()
        query.prepare("""
            INSERT INTO activity_log (
                login_session_id, daily_session_id, user_id, username,
                category, action, entity_type, entity_id,
                note, previous_value, new_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        query.addBindValue(login_session_id)
        query.addBindValue(daily_session_id)
        query.addBindValue(user_id)
        query.addBindValue(username)
        query.addBindValue(category)
        query.addBindValue(action)
        query.addBindValue(entity_type)
        query.addBindValue(entity_id)
        query.addBindValue(note)
        query.addBindValue(previous_value)
        query.addBindValue(new_value)

        if not query.exec():
            print("[activity_logger] Insert failed (non-blocking):", query.lastError().text())

    except Exception as exc:
        print("[activity_logger] Exception (non-blocking):", exc)
