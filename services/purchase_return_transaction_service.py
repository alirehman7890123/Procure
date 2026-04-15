def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


from services.inventory_movement_service import (
    decrement_batch_quantity_by_number as decrement_batch_quantity_by_number_from_inventory,
    fetch_batch_remaining as fetch_batch_remaining_from_inventory,
)


def insert_purchase_return_header(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO purchase_return
        (
            supplier, rep, subtotal, roundoff, total, received, remaining,
            writeoff, payable, receiveable, session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(payload["supplier"])
    query.addBindValue(payload["rep"])
    query.addBindValue(payload["subtotal"])
    query.addBindValue(payload["roundoff"])
    query.addBindValue(payload["total"])
    query.addBindValue(payload["received"])
    query.addBindValue(payload["remaining"])
    query.addBindValue(payload["writeoff"])
    query.addBindValue(payload["payable"])
    query.addBindValue(payload["receiveable"])
    query.addBindValue(payload["session_id"])
    if not query.exec():
        raise Exception(query.lastError().text())
    return query.lastInsertId()


def fetch_supplier_balances_for_return(supplier_id):
    query = _new_query()
    query.prepare("SELECT payable, receiveable FROM supplier WHERE id = ?")
    query.addBindValue(supplier_id)
    if not query.exec() or not query.next():
        raise Exception("Supplier not found or database error.")
    return {
        "payable_before": float(query.value(0) or 0.0),
        "receiveable_before": float(query.value(1) or 0.0),
    }


def insert_supplier_return_transaction(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO supplier_transaction
        (
            supplier, transaction_type, ref, return_ref,
            payable_before, due_amount, paid, remaining_due, payable_after,
            receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
            payment_method, bank_name, account_no, transaction_mode,
            wallet_provider, wallet_no, payment_reference,
            rep, note, session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    query.addBindValue(payload.get("payment_method") or None)
    query.addBindValue(payload.get("bank_name") or None)
    query.addBindValue(payload.get("account_no") or None)
    query.addBindValue(payload.get("transaction_mode") or None)
    query.addBindValue(payload.get("wallet_provider") or None)
    query.addBindValue(payload.get("wallet_no") or None)
    query.addBindValue(payload.get("payment_reference") or None)
    query.addBindValue(payload["rep"])
    query.addBindValue(payload["note"])
    query.addBindValue(payload["session_id"])
    if not query.exec():
        raise Exception(query.lastError().text())
    return query.lastInsertId()


def update_supplier_return_balances(supplier_id, *, payable_after, receiveable_after):
    query = _new_query()
    query.prepare("UPDATE supplier SET payable = ?, receiveable = ? WHERE id = ?")
    query.addBindValue(payable_after)
    query.addBindValue(receiveable_after)
    query.addBindValue(supplier_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    return True


def fetch_batch_remaining_for_return(batch_no, product_id):
    return fetch_batch_remaining_from_inventory(batch_no, product_id)


def insert_purchase_return_item(return_id, row_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO purchase_return_item
        (purchase_return, product, batch, purchased, returned, rate, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(return_id)
    query.addBindValue(row_payload["product"])
    query.addBindValue(row_payload["batch"])
    query.addBindValue(row_payload["purchased"])
    query.addBindValue(row_payload["returned"])
    query.addBindValue(round(row_payload["rate"], 4))
    query.addBindValue(round(row_payload["total"], 2))
    if not query.exec():
        raise Exception(query.lastError().text())
    return query.lastInsertId()


def decrement_batch_quantity_for_purchase_return(batch_no, product_id, qty):
    return decrement_batch_quantity_by_number_from_inventory(batch_no, product_id, qty)
