def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()

from medic.services.db_transaction_service import run_in_transaction
from medic.services.inventory_movement_service import (
    fetch_sold_batch_rows_for_return as fetch_sold_batch_rows_for_return_from_inventory,
    increment_sold_batch_returned as increment_sold_batch_returned_in_inventory,
    restore_batch_quantity as restore_batch_quantity_in_inventory,
)


def insert_sales_return_header(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO salesreturn
        (salesorder, customer, salesman, subtotal, roundoff, total, paid, remaining, writeoff, payable, receiveable, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(payload["salesorder"])
    query.addBindValue(payload["customer"])
    query.addBindValue(payload["salesman"])
    query.addBindValue(payload["subtotal"])
    query.addBindValue(payload["roundoff"])
    query.addBindValue(payload["total"])
    query.addBindValue(payload["paid"])
    query.addBindValue(payload["remaining"])
    query.addBindValue(payload["writeoff"])
    query.addBindValue(payload["payable"])
    query.addBindValue(payload["receiveable"])
    query.addBindValue(payload["session_id"])
    if not query.exec():
        raise Exception(query.lastError().text())
    return query.lastInsertId()


def fetch_customer_balances_for_return(customer_id):
    query = _new_query()
    query.prepare("SELECT payable, receiveable FROM customer WHERE id = ?")
    query.addBindValue(customer_id)
    if not query.exec() or not query.next():
        raise Exception("Customer not found.")
    return {
        "payable_before": float(query.value(0) or 0.0),
        "receiveable_before": float(query.value(1) or 0.0),
    }


def insert_customer_return_transaction(payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO customer_transaction
        (
            customer, transaction_type, ref, return_ref,
            payable_before, due_amount, paid, remaining_due, payable_after,
            receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
            payment_method, bank_name, account_no, transaction_mode,
            wallet_provider, wallet_no, payment_reference,
            salesman, note, session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(payload["customer"])
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
    query.addBindValue(payload["salesman"])
    query.addBindValue(payload["note"])
    query.addBindValue(payload["session_id"])
    if not query.exec():
        raise Exception(query.lastError().text())
    return query.lastInsertId()


def update_customer_return_balances(customer_id, *, payable_after, receiveable_after):
    query = _new_query()
    query.prepare("UPDATE customer SET payable = ?, receiveable = ? WHERE id = ?")
    query.addBindValue(payable_after)
    query.addBindValue(receiveable_after)
    query.addBindValue(customer_id)
    if not query.exec():
        raise Exception(query.lastError().text())
    return True


def insert_sales_return_item(return_id, row_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO salesreturn_item
        (salesreturn, salesitem_id, product, sold, returned, rate, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(return_id)
    query.addBindValue(row_payload["salesitem_id"])
    query.addBindValue(row_payload["product_id"])
    query.addBindValue(row_payload["sold"])
    query.addBindValue(row_payload["returned"])
    query.addBindValue(row_payload["rate"])
    query.addBindValue(row_payload["total"])
    if not query.exec():
        raise Exception(query.lastError().text())
    return query.lastInsertId()


def fetch_sales_item_qty_sold(sales_item_id):
    query = _new_query()
    query.prepare("SELECT qty_sold FROM salesitem WHERE id = ?")
    query.addBindValue(sales_item_id)
    if not query.exec() or not query.next():
        raise Exception("Invalid sales_item_id")
    return int(query.value(0) or 0)


def fetch_already_returned_qty(sales_item_id):
    query = _new_query()
    query.prepare("SELECT COALESCE(SUM(returned), 0) FROM salesreturn_item WHERE salesitem_id = ?")
    query.addBindValue(sales_item_id)
    if not query.exec() or not query.next():
        raise Exception("Failed checking returned qty")
    return int(query.value(0) or 0)


def fetch_sold_batch_rows_for_return(sales_item_id):
    return fetch_sold_batch_rows_for_return_from_inventory(sales_item_id)


def restore_batch_quantity(batch_id, qty):
    return restore_batch_quantity_in_inventory(batch_id, qty)


def increment_sold_batch_returned(sold_batch_id, qty):
    return increment_sold_batch_returned_in_inventory(sold_batch_id, qty)


def apply_sales_return_inventory_reversal(sales_item_id: int, return_qty: int):
    try:
        sales_item_id = int(sales_item_id)
        return_qty = int(return_qty)
        if return_qty <= 0:
            raise Exception("Return quantity must be greater than zero")

        qty_sold = fetch_sales_item_qty_sold(sales_item_id)
        already_returned = fetch_already_returned_qty(sales_item_id)
        if already_returned + return_qty > qty_sold:
            raise Exception("Return quantity exceeds sold quantity")

        batch_rows = fetch_sold_batch_rows_for_return(sales_item_id)
        plan = compute_sales_return_inventory_plan(
            qty_sold=qty_sold,
            already_returned=already_returned,
            return_qty=return_qty,
            sold_batch_rows=batch_rows,
        )

        for allocation in plan["allocations"]:
            restore_batch_quantity(allocation["batch_id"], allocation["qty_to_restore"])
            increment_sold_batch_returned(allocation["sold_batch_id"], allocation["qty_to_restore"])
    except Exception as exc:
        raise Exception(f"Sales return inventory reversal failed: {exc}")


def save_sales_return_entry(*, header_payload, transaction_payload, customer_id, item_rows):
    normalized_rows = [row for row in list(item_rows or []) if row is not None]
    if not normalized_rows:
        raise ValueError("Enter at least one returned item before saving the sales return.")

    def _work():
        return_id = insert_sales_return_header(header_payload)

        normalized_transaction_payload = dict(transaction_payload or {})
        normalized_transaction_payload["ref"] = int(return_id)
        normalized_transaction_payload["return_ref"] = int(return_id)
        normalized_transaction_payload["note"] = (
            f"Sales Return ID {return_id} recorded with total "
            f"{float(header_payload.get('total') or 0.0)}, "
            f"paid {normalized_transaction_payload.get('paid', 0.0)}, "
            f"remaining {float(header_payload.get('remaining') or 0.0)}"
        )

        insert_customer_return_transaction(normalized_transaction_payload)
        if customer_id is not None:
            update_customer_return_balances(
                customer_id,
                payable_after=normalized_transaction_payload["payable_after"],
                receiveable_after=normalized_transaction_payload["receiveable_after"],
            )

        for row in normalized_rows:
            apply_sales_return_inventory_reversal(row["salesitem_id"], row["returned"])
            insert_sales_return_item(return_id, row)

        return int(return_id)

    return run_in_transaction(
        _work,
        start_error_message="Could not start sales return transaction.",
        commit_error_message="Could not commit sales return transaction.",
    )
