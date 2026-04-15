def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


def insert_goods_receipt_header(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO goods_receipt (
            grn_number,
            po_id,
            grn_date,
            status,
            total_value,
            header_discount,
            header_tax,
            discount,
            tax_236g,
            tax_236h,
            salestax,
            cn_adjustment,
            taxable,
            netamount,
            session_id,
            notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(payload["grn_number"])
    query.addBindValue(payload["po_id"])
    query.addBindValue(payload["grn_date"])
    query.addBindValue(payload["status"])
    query.addBindValue(payload["total_value"])
    query.addBindValue(payload["header_discount"])
    query.addBindValue(payload["header_tax"])
    query.addBindValue(payload["discount"])
    query.addBindValue(payload["tax_236g"])
    query.addBindValue(payload["tax_236h"])
    query.addBindValue(payload["salestax"])
    query.addBindValue(payload["cn_adjustment"])
    query.addBindValue(payload["taxable"])
    query.addBindValue(payload["netamount"])
    query.addBindValue(payload["session_id"])
    query.addBindValue(payload["notes"])

    if not query.exec():
        raise Exception(query.lastError().text())

    return int(query.lastInsertId())


def insert_goods_receipt_line(grn_id, line_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO goods_receipt_line (
            grn_id, po_line_id, qty_received, unit_price_received, total_received,
            batch_no, expiry_date, discount, tax, landing_cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(grn_id)
    query.addBindValue(line_payload["po_line_id"])
    query.addBindValue(line_payload["qty_received"])
    query.addBindValue(line_payload["unit_price"])
    query.addBindValue(line_payload["total_received"])
    query.addBindValue(line_payload["batch_no"])
    query.addBindValue(line_payload["expiry_date"])
    query.addBindValue(line_payload["discount"])
    query.addBindValue(line_payload["tax"])
    query.addBindValue(line_payload["landing_cost"])

    if not query.exec():
        raise Exception(query.lastError().text())

    return int(query.lastInsertId())


def update_goods_receipt_status(grn_number, status):
    query = _new_query()
    query.prepare("UPDATE goods_receipt SET status = ? WHERE grn_number = ?")
    query.addBindValue(status)
    query.addBindValue(grn_number)
    if not query.exec():
        raise Exception(f"GRN status update failed: {query.lastError().text()}")
    return True
