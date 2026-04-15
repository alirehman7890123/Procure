def _new_query():
    from PySide6.QtSql import QSqlQuery

    return QSqlQuery()


from services.inventory_movement_service import (
    decrement_batch_quantity as decrement_batch_quantity_from_inventory,
    fetch_fifo_batch_rows as fetch_fifo_batch_rows_from_inventory,
    fetch_total_available_stock as fetch_total_available_stock_from_inventory,
    insert_sold_batch_record as insert_sold_batch_record_from_inventory,
)


def build_customer_transaction_payload(
    *,
    sales_id,
    customer_id,
    total_amount,
    received,
    salesman_id,
    session_id,
    payment,
    note,
    balance_state,
):
    balance_state = dict(balance_state or {})
    payment = dict(payment or {})
    return {
        "customer_id": customer_id,
        "transaction_type": "SALE",
        "ref": sales_id,
        "return_ref": None,
        "payable_before": float(balance_state.get("payable_before") or 0.0),
        "due_amount": float(total_amount or 0.0),
        "paid": 0.0,
        "remaining_due": float(balance_state.get("remaining_due") or 0.0),
        "payable_after": float(balance_state.get("payable_after") or 0.0),
        "receiveable_before": float(balance_state.get("receiveable_before") or 0.0),
        "receiveable_now": float(balance_state.get("receiveable_now") or 0.0),
        "received": float(received or 0.0),
        "remaining_now": float(balance_state.get("remaining_now") or 0.0),
        "receiveable_after": float(balance_state.get("receiveable_after") or 0.0),
        "payment_method": payment.get("payment_method"),
        "bank_name": payment.get("bank_name"),
        "account_no": payment.get("account_no"),
        "transaction_mode": payment.get("transaction_mode"),
        "wallet_provider": payment.get("wallet_provider"),
        "wallet_no": payment.get("wallet_no"),
        "payment_reference": payment.get("payment_reference"),
        "salesman_id": salesman_id,
        "note": note,
        "session_id": session_id,
    }


def insert_sales_header(header_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO sales
        (customer, salesman, subtotal, discount, taxable, tax,
        net_amount, additional_charges, total, received,
        remaining, writeoff, payable, receiveable, session_id, due_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )

    query.addBindValue(header_payload["customer_id"])
    query.addBindValue(header_payload["salesman_id"])
    query.addBindValue(header_payload["subtotal"])
    query.addBindValue(header_payload["discount"])
    query.addBindValue(header_payload["taxable"])
    query.addBindValue(header_payload["tax"])
    query.addBindValue(header_payload["net_amount"])
    query.addBindValue(header_payload["additional_charges"])
    query.addBindValue(header_payload["total"])
    query.addBindValue(header_payload["received"])
    query.addBindValue(header_payload["remaining"])
    query.addBindValue(header_payload["writeoff"])
    query.addBindValue(header_payload["payable"])
    query.addBindValue(header_payload["receiveable"])
    query.addBindValue(header_payload["session_id"])
    query.addBindValue(header_payload["due_date"])

    if not query.exec():
        raise Exception(query.lastError().text())

    return query.lastInsertId()


def fetch_customer_balances(customer_id):
    query = _new_query()
    query.prepare(
        """
        SELECT payable, receiveable
        FROM customer
        WHERE id = ?
        """
    )
    query.addBindValue(customer_id)

    if not query.exec() or not query.next():
        raise Exception("Failed to fetch customer balance.")

    return {
        "payable_before": float(query.value(0) or 0.0),
        "receiveable_before": float(query.value(1) or 0.0),
    }


def insert_customer_transaction_record(payload):
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

    query.addBindValue(payload["customer_id"])
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
    query.addBindValue(payload["salesman_id"])
    query.addBindValue(payload["note"])
    query.addBindValue(payload["session_id"])

    if not query.exec():
        raise Exception(query.lastError().text())

    return query.lastInsertId()


def update_customer_running_balance(customer_id, *, payable_after, receiveable_after):
    query = _new_query()
    query.prepare(
        """
        UPDATE customer
        SET payable = ?, receiveable = ?
        WHERE id = ?
        """
    )
    query.addBindValue(payable_after)
    query.addBindValue(receiveable_after)
    query.addBindValue(customer_id)

    if not query.exec():
        raise Exception(query.lastError().text())

    return True


def fetch_total_available_stock(product_id):
    return fetch_total_available_stock_from_inventory(product_id)


def insert_sales_item_record(sales_id, row_payload):
    query = _new_query()
    query.prepare(
        """
        INSERT INTO salesitem
        (sales_id, product_id, qty_sold, unit_price,
        discount, tax, discount_amount, tax_amount, discount_input_mode,
        default_discount_group_id, default_tax_group_id,
        discount_group_id, tax_group_id, discount_source, tax_source,
        line_total, line_weight, effective_line_total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    )
    query.addBindValue(sales_id)
    query.addBindValue(row_payload["product_id"])
    query.addBindValue(row_payload["qty"])
    query.addBindValue(row_payload["rate"])
    query.addBindValue(row_payload["discount_percent"])
    query.addBindValue(row_payload["tax_percent"])
    query.addBindValue(row_payload["discount_amount"])
    query.addBindValue(row_payload["tax_amount"])
    query.addBindValue(row_payload["discount_input_mode"])
    query.addBindValue(row_payload["default_discount_group_id"])
    query.addBindValue(row_payload["default_tax_group_id"])
    query.addBindValue(row_payload["discount_group_id"])
    query.addBindValue(row_payload["tax_group_id"])
    query.addBindValue(row_payload["discount_source"])
    query.addBindValue(row_payload["tax_source"])
    query.addBindValue(row_payload["line_total"])
    query.addBindValue(row_payload["line_weight"])
    query.addBindValue(row_payload["effective_line_total"])

    if not query.exec():
        raise Exception(f"Failed to insert sales item: {query.lastError().text()}")

    return query.lastInsertId()


def fetch_fifo_batch_rows(product_id):
    return fetch_fifo_batch_rows_from_inventory(product_id)


def decrement_batch_quantity(batch_id, take_qty):
    return decrement_batch_quantity_from_inventory(batch_id, take_qty)


def insert_sold_batch_record(sale_item_id, allocation):
    return insert_sold_batch_record_from_inventory(sale_item_id, allocation)
