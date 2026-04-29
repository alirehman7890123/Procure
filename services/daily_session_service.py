from PySide6.QtSql import QSqlQuery

try:
    from medic.utilities.session_service import get_active_session_id
except ModuleNotFoundError:
    from utilities.session_service import get_active_session_id


def _new_query():
    return QSqlQuery()


def get_open_session(session_id=None):
    if session_id is None:
        session_id = get_active_session_id(strict=True)
    if session_id is None:
        return None

    query = _new_query()
    query.prepare(
        """
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
        WHERE id = ?
        """
    )
    query.addBindValue(int(session_id))

    if query.exec() and query.next():
        return {
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
    return None


def get_previous_balance():
    query = _new_query()
    query.prepare(
        """
        SELECT actual_cash, withdrawal
        FROM daily_session
        WHERE status = 'closed'
        ORDER BY id DESC
        LIMIT 1
        """
    )
    if query.exec() and query.next():
        actual_cash = float(query.value(0) or 0.0)
        withdrawal = float(query.value(1) or 0.0)
        return max(0.0, actual_cash - withdrawal)
    return 0.0


def get_cash_expenses(session_id=None):
    if session_id is None:
        session_id = get_active_session_id(strict=True)
    if session_id is None:
        return 0.0

    query = _new_query()
    query.prepare(
        """
        SELECT COALESCE(SUM(e.amount), 0)
        FROM expense e
        WHERE e.session_id = ?
          AND e.payment_method = 'Cash'
        """
    )
    query.addBindValue(int(session_id))

    if query.exec() and query.next():
        return float(query.value(0) or 0.0)
    return 0.0


def get_session_payment_method_summary(session_id=None, methods=None):
    if session_id is None:
        session_id = get_active_session_id(strict=True)
    if session_id is None:
        return {}

    method_names = methods or ["Bank Transfer", "EasyPaisa", "JazzCash"]
    summary = {
        method: {"received": 0.0, "paid": 0.0, "expense": 0.0, "net": 0.0}
        for method in method_names
    }

    def accumulate_transaction_table(table_name):
        for method in method_names:
            query = _new_query()
            query.prepare(
                f"""
                SELECT
                    COALESCE(SUM(received), 0),
                    COALESCE(SUM(paid), 0)
                FROM {table_name}
                WHERE session_id = ?
                  AND payment_method = ?
                """
            )
            query.addBindValue(int(session_id))
            query.addBindValue(method)
            if query.exec() and query.next():
                summary[method]["received"] += float(query.value(0) or 0.0)
                summary[method]["paid"] += float(query.value(1) or 0.0)

    accumulate_transaction_table("customer_transaction")
    accumulate_transaction_table("supplier_transaction")

    for method in method_names:
        query = _new_query()
        query.prepare(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM expense
            WHERE session_id = ?
              AND payment_method = ?
            """
        )
        query.addBindValue(int(session_id))
        query.addBindValue(method)
        if query.exec() and query.next():
            summary[method]["expense"] = float(query.value(0) or 0.0)

        summary[method]["net"] = (
            summary[method]["received"]
            - summary[method]["paid"]
            - summary[method]["expense"]
        )

    return summary


def get_opening_cash(session_id=None):
    session = get_open_session(session_id=session_id)
    if not session:
        return 0.0
    return float(session.get("opening_cash") or 0.0)


def get_current_session_cash_flows(session_id=None):
    if session_id is None:
        session_id = get_active_session_id(strict=True)
    if session_id is None:
        return None, 0.0, 0.0

    def fetch_sums(table_name):
        query = _new_query()
        query.prepare(
            f"""
            SELECT
                COALESCE(SUM(received), 0),
                COALESCE(SUM(paid), 0)
            FROM {table_name}
            WHERE session_id = ?
              AND payment_method = 'Cash'
            """
        )
        query.addBindValue(int(session_id))
        if query.exec() and query.next():
            return float(query.value(0) or 0.0), float(query.value(1) or 0.0)
        return 0.0, 0.0

    customer_received, customer_paid = fetch_sums("customer_transaction")
    supplier_received, supplier_paid = fetch_sums("supplier_transaction")
    return session_id, customer_received + supplier_received, customer_paid + supplier_paid


def open_daily_session(*, session_date, opening_cash):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO daily_session (session_date, opening_cash, status)
        VALUES (?, ?, 'open')
        """
    )
    query.addBindValue(str(session_date or "").strip())
    query.addBindValue(float(opening_cash or 0.0))

    if not query.exec():
        raise Exception(query.lastError().text())


def close_daily_session(*, session_id, system_cash, actual_cash, withdrawal, cash_difference):
    query = _new_query()
    query.prepare(
        """
        UPDATE daily_session
        SET
            system_cash = ?,
            actual_cash = ?,
            withdrawal = ?,
            cash_difference = ?,
            closed_at = CURRENT_TIMESTAMP,
            status = 'closed'
        WHERE id = ?
        """
    )
    query.addBindValue(float(system_cash or 0.0))
    query.addBindValue(float(actual_cash or 0.0))
    query.addBindValue(float(withdrawal or 0.0))
    query.addBindValue(float(cash_difference or 0.0))
    query.addBindValue(int(session_id))

    if not query.exec():
        raise Exception(query.lastError().text())


def fetch_session_history(*, limit=10, status_filter="all", date_from=None, date_to=None):
    query = _new_query()
    sql = """
        SELECT
            id,
            COALESCE(session_date, ''),
            COALESCE(opened_at, ''),
            COALESCE(opening_cash, 0),
            COALESCE(system_cash, 0),
            COALESCE(actual_cash, 0),
            COALESCE(withdrawal, 0),
            COALESCE(cash_difference, 0),
            COALESCE(status, ''),
            COALESCE(closed_at, '')
        FROM daily_session
    """
    where_clauses = []
    bind_values = []

    normalized_status = str(status_filter or "all").strip().lower()
    if normalized_status in {"open", "closed"}:
        where_clauses.append("LOWER(COALESCE(status, '')) = ?")
        bind_values.append(normalized_status)
    if date_from:
        where_clauses.append("DATE(COALESCE(session_date, opened_at, closed_at)) >= ?")
        bind_values.append(str(date_from))
    if date_to:
        where_clauses.append("DATE(COALESCE(session_date, opened_at, closed_at)) <= ?")
        bind_values.append(str(date_to))

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
    sql += " ORDER BY id DESC LIMIT ?"

    query.prepare(sql)
    for value in bind_values:
        query.addBindValue(value)
    query.addBindValue(int(limit))

    if not query.exec():
        raise Exception(query.lastError().text())

    rows = []
    while query.next():
        row = []
        for col in range(10):
            value = query.value(col)
            if 3 <= col <= 7:
                try:
                    row.append(f"{float(value or 0):.2f}")
                except Exception:
                    row.append("0.00")
            else:
                row.append(str(value or ""))
        rows.append(row)
    return rows
