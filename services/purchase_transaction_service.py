def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


from services.inventory_movement_service import insert_batch_record as insert_batch_record_from_inventory


def insert_purchase_header(header_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO purchase (
            supplier,
            rep,
            sellerinvoice,
            subtotal,
            discount,
            tax_236g,
            tax_236h,
            salestax,
            netamount,
            cn_adjustment,
            total,
            paid,
            remaining,
            writeoff,
            payable,
            receivable,
            due_date,
            session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )

    query.addBindValue(header_payload["supplier"])
    query.addBindValue(header_payload["rep"])
    query.addBindValue(header_payload["sellerinvoice"])
    query.addBindValue(header_payload["subtotal"])
    query.addBindValue(header_payload["discount"])
    query.addBindValue(header_payload["tax_236g"])
    query.addBindValue(header_payload["tax_236h"])
    query.addBindValue(header_payload["sales_tax"])
    query.addBindValue(header_payload["netamount"])
    query.addBindValue(header_payload["cn_adjustment"])
    query.addBindValue(header_payload["total"])
    query.addBindValue(header_payload["paid"])
    query.addBindValue(header_payload["remaining"])
    query.addBindValue(header_payload["writeoff"])
    query.addBindValue(header_payload["payable"])
    query.addBindValue(header_payload["receivable"])
    query.addBindValue(header_payload["due_date"])
    query.addBindValue(header_payload["session_id"])

    if not query.exec():
        raise Exception(f"Failed to save purchase header: {query.lastError().text()}")

    purchase_id = query.lastInsertId()
    if purchase_id is None:
        raise Exception("Purchase header saved, but could not retrieve purchase ID.")

    try:
        return int(purchase_id)
    except (TypeError, ValueError):
        raise Exception("Purchase header saved, but returned purchase ID was invalid.")


def insert_purchase_item(purchase_id, row_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO purchaseitem (
            purchase,
            product,
            qty,
            bonus,
            rate,
            discount,
            tax,
            total,
            landing_cost
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )

    query.addBindValue(purchase_id)
    query.addBindValue(row_payload["product"])
    query.addBindValue(row_payload["qty"])
    query.addBindValue(row_payload["bonus"])
    query.addBindValue(row_payload["rate"])
    query.addBindValue(row_payload["item_discount"])
    query.addBindValue(row_payload["item_tax"])
    query.addBindValue(row_payload["item_total"])
    query.addBindValue(row_payload["landing_cost"])

    if not query.exec():
        raise Exception(f"Failed to save purchase item: {query.lastError().text()}")

    purchase_item_id = query.lastInsertId()
    if purchase_item_id is None:
        raise Exception("Purchase item saved, but no ID was returned.")

    try:
        return int(purchase_item_id)
    except (TypeError, ValueError):
        raise Exception("Purchase item saved, but returned item ID was invalid.")


def fetch_product_pack_size(product_id):
    query = _new_query()
    query.prepare("SELECT pack_size FROM price_pack WHERE product_id = ?")
    query.addBindValue(product_id)

    if not query.exec() or not query.next():
        raise Exception(f"Failed to fetch pack size for product ID {product_id}: {query.lastError().text()}")

    return query.value(0)


def insert_batch_record(batch_payload):
    return insert_batch_record_from_inventory(batch_payload)


def mark_product_used(product_id):
    query = _new_query()
    query.prepare(
        """
        UPDATE product
        SET status = 'used'
        WHERE id = ?
        """
    )
    query.addBindValue(product_id)

    if not query.exec():
        raise Exception(f"Failed to update product status: {query.lastError().text()}")

    return True


def fetch_supplier_balances(supplier_id):
    query = _new_query()
    query.prepare("SELECT payable, receiveable FROM supplier WHERE id = ?")
    query.addBindValue(supplier_id)

    if not query.exec() or not query.next():
        raise Exception("Failed to fetch supplier balances.")

    return {
        "payable_before": float(query.value(0) or 0.0),
        "receiveable_before": float(query.value(1) or 0.0),
    }


def insert_supplier_transaction(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO supplier_transaction 
        (
            supplier, transaction_type, ref, return_ref,
            payable_before, due_amount, paid, remaining_due, payable_after,
            receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
            rep, session_id,
            payment_method, bank_name, account_no, transaction_mode,
            wallet_provider, wallet_no, payment_reference
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )

    query.addBindValue(payload["supplier"])
    query.addBindValue(payload["transaction_type"])
    query.addBindValue(payload["ref"])
    query.addBindValue(payload["return_ref"])
    query.addBindValue(payload["payable_before"])
    query.addBindValue(payload["due_amount"])
    query.addBindValue(payload["paid"])
    query.addBindValue(payload["remaining_due"])
    query.addBindValue(payload["payable_after"])
    query.addBindValue(payload["receiveable_before"])
    query.addBindValue(payload["receiveable_now"])
    query.addBindValue(payload["received"])
    query.addBindValue(payload["remaining_now"])
    query.addBindValue(payload["receiveable_after"])
    query.addBindValue(payload["rep"])
    query.addBindValue(payload["session_id"])
    query.addBindValue(payload["payment_method"])
    query.addBindValue(payload["bank_name"])
    query.addBindValue(payload["account_no"])
    query.addBindValue(payload["transaction_mode"])
    query.addBindValue(payload["wallet_provider"])
    query.addBindValue(payload["wallet_no"])
    query.addBindValue(payload["payment_reference"])

    if not query.exec():
        raise Exception(f"Failed to save supplier transaction: {query.lastError().text()}")

    return query.lastInsertId()


def update_supplier_balances(supplier_id, *, payable_after, receiveable_after):
    query = _new_query()
    query.prepare(
        """
        UPDATE supplier
        SET payable = ?, receiveable = ?
        WHERE id = ?
        """
    )
    query.addBindValue(payable_after)
    query.addBindValue(receiveable_after)
    query.addBindValue(supplier_id)

    if not query.exec():
        raise Exception(f"Failed to update supplier balances: {query.lastError().text()}")

    return True
