def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()

from medic.services.db_transaction_service import run_in_transaction


VALID_ADJUSTMENT_TYPES = {"addition", "deduction"}


def fetch_adjustable_products():
    query = _new_query()
    query.prepare(
        """
        SELECT id, display_name
        FROM product
        WHERE status = 'used'
        ORDER BY display_name ASC
        """
    )

    if not query.exec():
        raise Exception(f"Failed to load products: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "product_id": int(query.value(0) or 0),
                "display_name": str(query.value(1) or ""),
            }
        )
    return rows


def fetch_adjustment_batches_for_product(product_id, *, include_sold_out=False):
    query = _new_query()
    sql = """
        SELECT
            id,
            COALESCE(batch_no, ''),
            COALESCE(expiry_date, ''),
            COALESCE(quantity_remaining, 0)
        FROM batch
        WHERE product_id = ?
    """

    if not include_sold_out:
        sql += "\n          AND COALESCE(quantity_remaining, 0) > 0"

    sql += """
        ORDER BY received_at ASC, id ASC
    """

    query.prepare(sql)
    query.addBindValue(product_id)

    if not query.exec():
        raise Exception(f"Failed to load batches: {query.lastError().text()}")

    rows = []
    total_stock = 0
    while query.next():
        system_qty = int(query.value(3) or 0)
        total_stock += system_qty
        rows.append(
            {
                "batch_id": int(query.value(0) or 0),
                "batch_no": str(query.value(1) or ""),
                "expiry_date": str(query.value(2) or ""),
                "system_qty": system_qty,
            }
        )

    return {
        "rows": rows,
        "total_stock": total_stock,
    }


def normalize_stock_adjustment_row(
    *,
    row_number,
    batch_id,
    batch_no,
    old_qty,
    new_qty,
    reason,
    note="",
):
    try:
        normalized_batch_id = int(batch_id)
    except (TypeError, ValueError):
        raise ValueError(f"Row {row_number}: invalid batch.")

    try:
        normalized_old_qty = int(old_qty)
        normalized_new_qty = int(new_qty)
    except (TypeError, ValueError):
        raise ValueError(f"Row {row_number}: quantities must be whole numbers.")

    if normalized_old_qty < 0 or normalized_new_qty < 0:
        raise ValueError(f"Row {row_number}: quantities cannot be negative.")

    if normalized_new_qty == normalized_old_qty:
        return None

    normalized_reason = str(reason or "").strip()
    if not normalized_reason or normalized_reason == "Select reason...":
        raise ValueError(f"Row {row_number}: reason is required.")

    delta = normalized_new_qty - normalized_old_qty
    adjustment_type = "addition" if delta > 0 else "deduction"
    qty = abs(delta)

    return {
        "batch_id": normalized_batch_id,
        "batch_no": str(batch_no or "").strip(),
        "old_qty": normalized_old_qty,
        "new_qty": normalized_new_qty,
        "qty": qty,
        "adjustment_type": adjustment_type,
        "reason": normalized_reason,
        "note": str(note or "").strip(),
    }


def insert_inventory_adjustment(row_payload, adjusted_by):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO inventory_adjustment (
            batch_id, qty, adjustment_type, old_qty, new_qty, reason, note, adjusted_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(row_payload["batch_id"])
    query.addBindValue(row_payload["qty"])
    query.addBindValue(row_payload["adjustment_type"])
    query.addBindValue(row_payload["old_qty"])
    query.addBindValue(row_payload["new_qty"])
    query.addBindValue(row_payload["reason"])
    query.addBindValue(row_payload["note"])
    query.addBindValue(adjusted_by)

    if not query.exec():
        raise Exception(f"Failed to insert adjustment: {query.lastError().text()}")

    return query.lastInsertId()


def update_batch_quantity_to(batch_id, new_qty):
    query = _new_query()
    query.prepare(
        """
        UPDATE batch
        SET quantity_remaining = ?
        WHERE id = ?
        """
    )
    query.addBindValue(new_qty)
    query.addBindValue(batch_id)

    if not query.exec():
        raise Exception(f"Failed to update batch stock: {query.lastError().text()}")
    if query.numRowsAffected() == 0:
        raise Exception(f"Batch {batch_id} was not found for stock adjustment.")

    return True


def apply_stock_adjustments(changed_rows, adjusted_by):
    changed_rows = list(changed_rows or [])
    if not changed_rows:
        return 0

    for row in changed_rows:
        adjustment_type = row.get("adjustment_type")
        if adjustment_type not in VALID_ADJUSTMENT_TYPES:
            raise ValueError(f"Invalid adjustment type: {adjustment_type}")
        insert_inventory_adjustment(row, adjusted_by)
        update_batch_quantity_to(row["batch_id"], row["new_qty"])

    return len(changed_rows)


def save_stock_adjustments(changed_rows, adjusted_by):
    normalized_rows = list(changed_rows or [])
    if not normalized_rows:
        return 0

    return run_in_transaction(
        lambda: apply_stock_adjustments(normalized_rows, adjusted_by),
        start_error_message="Failed to start inventory adjustment transaction.",
        commit_error_message="Failed to commit inventory adjustment transaction.",
    )


def build_stock_adjustment_log_note(product_name, row_payload):
    direction = "increased" if row_payload["adjustment_type"] == "addition" else "decreased"
    batch_label = row_payload["batch_no"] or str(row_payload["batch_id"])
    return (
        f"Stock was {direction} for {product_name}, batch {batch_label}. "
        f"Quantity changed from {row_payload['old_qty']} to {row_payload['new_qty']}. "
        f"Reason: {row_payload['reason']}."
    )
