def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


def fetch_total_available_stock(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT COALESCE(SUM(quantity_remaining), 0)
        FROM batch
        WHERE product_id = ?
        AND quantity_remaining > 0
        AND (
            expiry_date IS NULL
            OR (
                CASE
                    WHEN expiry_date LIKE '____-__-__' THEN date(expiry_date)
                    WHEN expiry_date LIKE '__-__-____'
                        THEN date(substr(expiry_date, 7, 4) || '-' || substr(expiry_date, 4, 2) || '-' || substr(expiry_date, 1, 2))
                    ELSE NULL
                END
            ) >= date('now', 'localtime')
        )
        """
    )
    query.addBindValue(product_id)

    if not query.exec() or not query.next():
        raise Exception(f"Stock check failed for product ID {product_id}.")

    return int(query.value(0) or 0)


def fetch_fifo_batch_rows(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT id, quantity_remaining, unit_cost
        FROM batch
        WHERE product_id = ?
        AND quantity_remaining > 0
        AND (
            expiry_date IS NULL
            OR (
                CASE
                    WHEN expiry_date LIKE '____-__-__' THEN date(expiry_date)
                    WHEN expiry_date LIKE '__-__-____'
                        THEN date(substr(expiry_date, 7, 4) || '-' || substr(expiry_date, 4, 2) || '-' || substr(expiry_date, 1, 2))
                    ELSE NULL
                END
            ) >= date('now', 'localtime')
        )
        ORDER BY received_at ASC, id ASC
        """
    )
    query.addBindValue(product_id)

    if not query.exec():
        raise Exception(f"Failed to fetch FIFO batches: {query.lastError().text()}")

    rows = []
    while query.next():
        rows.append(
            {
                "batch_id": int(query.value(0)),
                "available": query.value(1),
                "unit_cost": query.value(2),
            }
        )
    return rows


def insert_batch_record(batch_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO batch (
            batch_no,
            expiry_date,
            product_id,
            purchaseitem_id,
            total_received,
            paid_qty,
            quantity_remaining,
            unit_cost,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )

    query.addBindValue(batch_payload["batch_no"])
    query.addBindValue(batch_payload["expiry_date"])
    query.addBindValue(batch_payload["product_id"])
    query.addBindValue(batch_payload["purchaseitem_id"])
    query.addBindValue(batch_payload["total_received"])
    query.addBindValue(batch_payload["paid_qty"])
    query.addBindValue(batch_payload["quantity_remaining"])
    query.addBindValue(batch_payload["unit_cost"])
    query.addBindValue(batch_payload["source"])

    if not query.exec():
        raise Exception(f"Failed to save batch: {query.lastError().text()}")

    return query.lastInsertId()


def fetch_batch_remaining(batch_no, product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT quantity_remaining
        FROM batch
        WHERE batch_no = ? AND product_id = ?
        """
    )
    query.addBindValue(batch_no)
    query.addBindValue(product_id)
    if not query.exec() or not query.next():
        raise Exception("Batch not found.")
    return query.value(0)


def fetch_batch_snapshot(batch_no, product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT quantity_remaining, unit_cost
        FROM batch
        WHERE batch_no = ? AND product_id = ?
        LIMIT 1
        """
    )
    query.addBindValue(batch_no)
    query.addBindValue(product_id)
    if not query.exec() or not query.next():
        return None
    return {
        "quantity_remaining": query.value(0),
        "unit_cost": query.value(1),
    }


def fetch_supplier_purchase_batches(product_id, supplier_id):
    query = _new_query()
    query.prepare(
        """
        SELECT DISTINCT b.batch_no
        FROM batch b
        JOIN purchaseitem pi ON pi.id = b.purchaseitem_id
        JOIN purchase p ON p.id = pi.purchase
        WHERE b.product_id = ?
          AND p.supplier = ?
          AND b.quantity_remaining > 0
          AND COALESCE(b.source, '') = 'PURCHASE'
          AND b.batch_no IS NOT NULL
          AND TRIM(b.batch_no) <> ''
        """
    )
    query.addBindValue(product_id)
    query.addBindValue(supplier_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    rows = []
    while query.next():
        rows.append(query.value(0))
    return rows


def fetch_product_batch_numbers(product_id):
    query = _new_query()
    query.prepare(
        """
        SELECT DISTINCT batch_no
        FROM batch
        WHERE product_id = ?
          AND batch_no IS NOT NULL
          AND TRIM(batch_no) <> ''
        ORDER BY received_at DESC, id DESC
        """
    )
    query.addBindValue(product_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    rows = []
    while query.next():
        rows.append(query.value(0))
    return rows


def decrement_batch_quantity(batch_id, take_qty):
    query = _new_query()
    query.prepare(
        """
        UPDATE batch
        SET quantity_remaining = quantity_remaining - ?
        WHERE id = ?
        """
    )
    query.addBindValue(take_qty)
    query.addBindValue(batch_id)

    if not query.exec():
        raise Exception(f"Failed to update batch {batch_id}: {query.lastError().text()}")
    if query.numRowsAffected() == 0:
        raise Exception(f"Batch {batch_id} not found for decrement")
    return True


def decrement_batch_quantity_by_number(batch_no, product_id, qty):
    query = _new_query()
    query.prepare(
        """
        UPDATE batch
        SET quantity_remaining = quantity_remaining - ?
        WHERE batch_no = ? AND product_id = ?
        """
    )
    query.addBindValue(qty)
    query.addBindValue(batch_no)
    query.addBindValue(product_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    if query.numRowsAffected() == 0:
        raise Exception("Batch quantity update failed.")
    return True


def restore_batch_quantity(batch_id, qty):
    query = _new_query()
    query.prepare("UPDATE batch SET quantity_remaining = quantity_remaining + ? WHERE id = ?")
    query.addBindValue(qty)
    query.addBindValue(batch_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    if query.numRowsAffected() == 0:
        raise Exception(f"Batch {batch_id} not found for restore")
    return True


def insert_sold_batch_record(sale_item_id, allocation):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO sold_batch
        (sale_item_id, batch_id, qty_taken, unit_cost, line_cost)
        VALUES (?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(sale_item_id)
    query.addBindValue(allocation["batch_id"])
    query.addBindValue(allocation["take_qty"])
    query.addBindValue(allocation["unit_cost"])
    query.addBindValue(allocation["line_cost"])

    if not query.exec():
        raise Exception(f"Failed to insert sold batch: {query.lastError().text()}")

    return query.lastInsertId()


def fetch_sold_batch_rows_for_return(sales_item_id):
    query = _new_query()
    query.prepare(
        """
        SELECT id, batch_id, qty_taken, COALESCE(qty_returned, 0)
        FROM sold_batch
        WHERE sale_item_id = ?
        ORDER BY id DESC
        """
    )
    query.addBindValue(sales_item_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    rows = []
    while query.next():
        rows.append(
            {
                "sold_batch_id": int(query.value(0)),
                "batch_id": int(query.value(1)),
                "qty_taken": int(query.value(2) or 0),
                "qty_returned": int(query.value(3) or 0),
            }
        )
    return rows


def increment_sold_batch_returned(sold_batch_id, qty):
    query = _new_query()
    query.prepare("UPDATE sold_batch SET qty_returned = COALESCE(qty_returned, 0) + ? WHERE id = ?")
    query.addBindValue(qty)
    query.addBindValue(sold_batch_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    if query.numRowsAffected() == 0:
        raise Exception(f"Sold batch {sold_batch_id} not found for update")
    return True
