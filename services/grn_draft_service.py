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


def save_grn_draft(header_payload, item_rows, *, draft_id=None):
    db = QSqlDatabase.database()
    started_transaction = db.transaction()

    try:
        encoded_header = json.dumps(dict(header_payload or {}))
        encoded_payment = json.dumps(dict((header_payload or {}).get("payment_data") or {}))

        query = _new_query()
        if draft_id:
            query.prepare(
                """
                UPDATE grn_draft
                SET po_id = ?, supplier = ?, rep = ?, grn_number = ?, grn_date = ?,
                    draft_data = ?, payment_data = ?, user_id = ?, session_id = ?,
                    status = 'active', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """
            )
            query.addBindValue(_to_int((header_payload or {}).get("po_id")))
            query.addBindValue(_to_int((header_payload or {}).get("supplier")))
            query.addBindValue(_to_int((header_payload or {}).get("rep")))
            query.addBindValue((header_payload or {}).get("grn_number") or None)
            query.addBindValue((header_payload or {}).get("grn_date") or None)
            query.addBindValue(encoded_header)
            query.addBindValue(encoded_payment)
            query.addBindValue(_to_int((header_payload or {}).get("user_id")))
            query.addBindValue(_to_int((header_payload or {}).get("session_id")))
            query.addBindValue(_to_int(draft_id))
        else:
            query.prepare(
                """
                INSERT INTO grn_draft (
                    po_id, supplier, rep, grn_number, grn_date, draft_data, payment_data, user_id, session_id, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
                """
            )
            query.addBindValue(_to_int((header_payload or {}).get("po_id")))
            query.addBindValue(_to_int((header_payload or {}).get("supplier")))
            query.addBindValue(_to_int((header_payload or {}).get("rep")))
            query.addBindValue((header_payload or {}).get("grn_number") or None)
            query.addBindValue((header_payload or {}).get("grn_date") or None)
            query.addBindValue(encoded_header)
            query.addBindValue(encoded_payment)
            query.addBindValue(_to_int((header_payload or {}).get("user_id")))
            query.addBindValue(_to_int((header_payload or {}).get("session_id")))

        if not query.exec():
            raise Exception(f"Failed to save GRN draft header: {query.lastError().text()}")

        if not draft_id:
            draft_id = _to_int(query.lastInsertId())
            if not draft_id:
                raise Exception("GRN draft saved but no draft ID was returned.")

        delete_rows = _new_query()
        delete_rows.prepare("DELETE FROM grn_draft_item WHERE draft_id = ?")
        delete_rows.addBindValue(draft_id)
        if not delete_rows.exec():
            raise Exception(f"Failed to clear previous GRN draft rows: {delete_rows.lastError().text()}")

        for index, row in enumerate(item_rows or [], start=1):
            row_query = _new_query()
            row_query.prepare(
                """
                INSERT INTO grn_draft_item (
                    draft_id, line_no, po_line_id, product_id, product_name, batch_no, expiry_date,
                    qty_received, unit_price, discount_mode, discount_value, tax
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            )
            row_query.addBindValue(draft_id)
            row_query.addBindValue(index)
            row_query.addBindValue(_to_int(row.get("po_line_id")))
            row_query.addBindValue(_to_int(row.get("product_id")))
            row_query.addBindValue(row.get("product_name") or None)
            row_query.addBindValue(row.get("batch_no") or None)
            row_query.addBindValue(row.get("expiry_date") or None)
            row_query.addBindValue(_to_int(row.get("qty_received")))
            row_query.addBindValue(_to_float(row.get("unit_price"), 0.0))
            row_query.addBindValue(row.get("discount_mode") or None)
            row_query.addBindValue(_to_float(row.get("discount_value"), 0.0))
            row_query.addBindValue(_to_float(row.get("tax"), 0.0))
            if not row_query.exec():
                raise Exception(f"Failed to save GRN draft row {index}: {row_query.lastError().text()}")

        if started_transaction and not db.commit():
            raise Exception("Failed to commit GRN draft save.")

        return draft_id
    except Exception:
        if started_transaction:
            db.rollback()
        raise


def load_latest_grn_draft(*, user_id=None, session_id=None):
    filters = ["status = 'active'"]
    binds = []
    if user_id not in (None, ""):
        filters.append("user_id = ?")
        binds.append(_to_int(user_id))
    if session_id not in (None, ""):
        filters.append("session_id = ?")
        binds.append(_to_int(session_id))

    query = _new_query()
    query.prepare(
        f"""
        SELECT id, draft_data, payment_data
        FROM grn_draft
        WHERE {' AND '.join(filters)}
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """
    )
    for bind in binds:
        query.addBindValue(bind)

    if not query.exec():
        raise Exception(f"Failed to load GRN draft header: {query.lastError().text()}")
    if not query.next():
        return None

    draft_id = _to_int(query.value(0))
    header = json.loads(str(query.value(1) or "{}"))
    payment_data = json.loads(str(query.value(2) or "{}"))

    row_query = _new_query()
    row_query.prepare(
        """
        SELECT line_no, po_line_id, product_id, product_name, batch_no, expiry_date,
               qty_received, unit_price, discount_mode, discount_value, tax
        FROM grn_draft_item
        WHERE draft_id = ?
        ORDER BY line_no ASC, id ASC
        """
    )
    row_query.addBindValue(draft_id)
    if not row_query.exec():
        raise Exception(f"Failed to load GRN draft rows: {row_query.lastError().text()}")

    rows = []
    while row_query.next():
        rows.append(
            {
                "line_no": _to_int(row_query.value(0)) or 0,
                "po_line_id": _to_int(row_query.value(1)),
                "product_id": _to_int(row_query.value(2)),
                "product_name": str(row_query.value(3) or ""),
                "batch_no": str(row_query.value(4) or ""),
                "expiry_date": str(row_query.value(5) or ""),
                "qty_received": _to_int(row_query.value(6)) or 0,
                "unit_price": _to_float(row_query.value(7), 0.0),
                "discount_mode": str(row_query.value(8) or "percent"),
                "discount_value": _to_float(row_query.value(9), 0.0),
                "tax": _to_float(row_query.value(10), 0.0),
            }
        )

    header["payment_data"] = payment_data
    return {"id": draft_id, "header": header, "rows": rows}


def delete_grn_draft(draft_id):
    if draft_id in (None, ""):
        return False

    db = QSqlDatabase.database()
    started_transaction = db.transaction()
    try:
        row_delete = _new_query()
        row_delete.prepare("DELETE FROM grn_draft_item WHERE draft_id = ?")
        row_delete.addBindValue(_to_int(draft_id))
        if not row_delete.exec():
            raise Exception(f"Failed to delete GRN draft rows: {row_delete.lastError().text()}")

        header_delete = _new_query()
        header_delete.prepare("DELETE FROM grn_draft WHERE id = ?")
        header_delete.addBindValue(_to_int(draft_id))
        if not header_delete.exec():
            raise Exception(f"Failed to delete GRN draft header: {header_delete.lastError().text()}")

        if started_transaction and not db.commit():
            raise Exception("Failed to commit GRN draft delete.")

        return True
    except Exception:
        if started_transaction:
            db.rollback()
        raise
