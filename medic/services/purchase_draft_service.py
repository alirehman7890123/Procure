import json

from PySide6.QtSql import QSqlDatabase, QSqlQuery


def _new_query():
    return QSqlQuery()


def _to_int(value):
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value, default=0.0):
    try:
        if value in (None, ""):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def save_purchase_draft(header_payload, item_rows, *, draft_id=None):
    db = QSqlDatabase.database()
    started_transaction = db.transaction()

    try:
        encoded_header = json.dumps(dict(header_payload or {}))
        encoded_payment = json.dumps(dict((header_payload or {}).get("payment_data") or {}))

        draft_query = _new_query()
        if draft_id:
            draft_query.prepare(
                """
                UPDATE purchase_draft
                SET supplier = ?, rep = ?, sellerinvoice = ?, draft_data = ?, payment_data = ?,
                    user_id = ?, session_id = ?, status = 'active', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """
            )
            draft_query.addBindValue(_to_int((header_payload or {}).get("supplier")))
            draft_query.addBindValue(_to_int((header_payload or {}).get("rep")))
            draft_query.addBindValue((header_payload or {}).get("sellerinvoice") or None)
            draft_query.addBindValue(encoded_header)
            draft_query.addBindValue(encoded_payment)
            draft_query.addBindValue(_to_int((header_payload or {}).get("user_id")))
            draft_query.addBindValue(_to_int((header_payload or {}).get("session_id")))
            draft_query.addBindValue(_to_int(draft_id))
        else:
            draft_query.prepare(
                """
                INSERT INTO purchase_draft (
                    supplier, rep, sellerinvoice, draft_data, payment_data, user_id, session_id, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
                """
            )
            draft_query.addBindValue(_to_int((header_payload or {}).get("supplier")))
            draft_query.addBindValue(_to_int((header_payload or {}).get("rep")))
            draft_query.addBindValue((header_payload or {}).get("sellerinvoice") or None)
            draft_query.addBindValue(encoded_header)
            draft_query.addBindValue(encoded_payment)
            draft_query.addBindValue(_to_int((header_payload or {}).get("user_id")))
            draft_query.addBindValue(_to_int((header_payload or {}).get("session_id")))

        if not draft_query.exec():
            raise Exception(f"Failed to save purchase draft header: {draft_query.lastError().text()}")

        if not draft_id:
            draft_id = _to_int(draft_query.lastInsertId())
            if not draft_id:
                raise Exception("Purchase draft saved but no draft ID was returned.")

        delete_items_query = _new_query()
        delete_items_query.prepare("DELETE FROM purchase_draft_item WHERE draft_id = ?")
        delete_items_query.addBindValue(draft_id)
        if not delete_items_query.exec():
            raise Exception(f"Failed to clear previous purchase draft rows: {delete_items_query.lastError().text()}")

        for index, row in enumerate(item_rows or [], start=1):
            item_query = _new_query()
            item_query.prepare(
                """
                INSERT INTO purchase_draft_item (
                    draft_id, line_no, product, product_name, batch, expiry,
                    qty, bonus, rate, discount, tax, total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            )
            item_query.addBindValue(draft_id)
            item_query.addBindValue(index)
            item_query.addBindValue(_to_int(row.get("product")))
            item_query.addBindValue(row.get("product_name") or None)
            item_query.addBindValue(row.get("batch") or None)
            item_query.addBindValue(row.get("expiry") or None)
            item_query.addBindValue(_to_int(row.get("qty")))
            item_query.addBindValue(_to_int(row.get("bonus")))
            item_query.addBindValue(_to_float(row.get("rate"), 0.0))
            item_query.addBindValue(_to_float(row.get("discount"), 0.0))
            item_query.addBindValue(_to_float(row.get("tax"), 0.0))
            item_query.addBindValue(_to_float(row.get("total"), 0.0))
            if not item_query.exec():
                raise Exception(f"Failed to save purchase draft row {index}: {item_query.lastError().text()}")

        if started_transaction and not db.commit():
            raise Exception("Failed to commit purchase draft save.")

        return draft_id

    except Exception:
        if started_transaction:
            db.rollback()
        raise


def load_latest_purchase_draft(*, user_id=None, session_id=None):
    query = _new_query()

    filters = ["status = 'active'"]
    binds = []

    if user_id not in (None, ""):
        filters.append("user_id = ?")
        binds.append(_to_int(user_id))

    if session_id not in (None, ""):
        filters.append("session_id = ?")
        binds.append(_to_int(session_id))

    query.prepare(
        f"""
        SELECT id, supplier, rep, sellerinvoice, draft_data, payment_data, user_id, session_id
        FROM purchase_draft
        WHERE {' AND '.join(filters)}
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """
    )
    for value in binds:
        query.addBindValue(value)

    if not query.exec():
        raise Exception(f"Failed to load purchase draft header: {query.lastError().text()}")

    if not query.next():
        return None

    draft_id = _to_int(query.value(0))
    draft_data = json.loads(str(query.value(4) or "{}"))
    payment_data = json.loads(str(query.value(5) or "{}"))

    item_query = _new_query()
    item_query.prepare(
        """
        SELECT line_no, product, product_name, batch, expiry, qty, bonus, rate, discount, tax, total
        FROM purchase_draft_item
        WHERE draft_id = ?
        ORDER BY line_no ASC, id ASC
        """
    )
    item_query.addBindValue(draft_id)
    if not item_query.exec():
        raise Exception(f"Failed to load purchase draft rows: {item_query.lastError().text()}")

    rows = []
    while item_query.next():
        rows.append(
            {
                "line_no": _to_int(item_query.value(0)) or 0,
                "product": _to_int(item_query.value(1)),
                "product_name": str(item_query.value(2) or ""),
                "batch": str(item_query.value(3) or ""),
                "expiry": str(item_query.value(4) or ""),
                "qty": _to_int(item_query.value(5)) or 0,
                "bonus": _to_int(item_query.value(6)) or 0,
                "rate": _to_float(item_query.value(7), 0.0),
                "discount": _to_float(item_query.value(8), 0.0),
                "tax": _to_float(item_query.value(9), 0.0),
                "total": _to_float(item_query.value(10), 0.0),
            }
        )

    draft_data["payment_data"] = payment_data
    return {
        "id": draft_id,
        "header": draft_data,
        "rows": rows,
    }


def delete_purchase_draft(draft_id):
    if draft_id in (None, ""):
        return False

    db = QSqlDatabase.database()
    started_transaction = db.transaction()

    try:
        delete_items_query = _new_query()
        delete_items_query.prepare("DELETE FROM purchase_draft_item WHERE draft_id = ?")
        delete_items_query.addBindValue(_to_int(draft_id))
        if not delete_items_query.exec():
            raise Exception(f"Failed to delete purchase draft rows: {delete_items_query.lastError().text()}")

        delete_header_query = _new_query()
        delete_header_query.prepare("DELETE FROM purchase_draft WHERE id = ?")
        delete_header_query.addBindValue(_to_int(draft_id))
        if not delete_header_query.exec():
            raise Exception(f"Failed to delete purchase draft header: {delete_header_query.lastError().text()}")

        if started_transaction and not db.commit():
            raise Exception("Failed to commit purchase draft delete.")

        return True

    except Exception:
        if started_transaction:
            db.rollback()
        raise
