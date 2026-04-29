"""Sales feature bridge for sales transaction helpers."""

from services.sales_transaction_service import *  # noqa: F403

from PySide6.QtSql import QSqlQuery

from features.sales.services.sales_posting_service import (
    build_customer_transaction_note,
    compute_customer_transaction_balances,
)
from features.sales.services.sales_items_service import compute_fifo_allocation_plan


def upsert_hold_sale_header(payload, hold_id=None):
    query = QSqlQuery()

    if hold_id is not None:
        query.prepare(
            """
            UPDATE holdsale
            SET customer = ?, salesman = ?, status = ?,
                subtotal = ?, discount_amount = ?, taxable_amount = ?, tax_amount = ?,
                additional_charges = ?, final_amount = ?, received_amount = ?,
                remaining_amount = ?, payment_method = ?, due_date = ?
            WHERE id = ?
            """
        )
    else:
        query.prepare(
            """
            INSERT INTO holdsale (
                customer, salesman, status,
                subtotal, discount_amount, taxable_amount, tax_amount,
                additional_charges, final_amount, received_amount,
                remaining_amount, payment_method, due_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        )

    query.addBindValue(payload.get("customer"))
    query.addBindValue(payload.get("salesman"))
    query.addBindValue(payload.get("status"))
    query.addBindValue(payload.get("subtotal"))
    query.addBindValue(payload.get("discount_amount"))
    query.addBindValue(payload.get("taxable_amount"))
    query.addBindValue(payload.get("tax_amount"))
    query.addBindValue(payload.get("additional_charges"))
    query.addBindValue(payload.get("final_amount"))
    query.addBindValue(payload.get("received_amount"))
    query.addBindValue(payload.get("remaining_amount"))
    query.addBindValue(payload.get("payment_method"))
    query.addBindValue(payload.get("due_date"))
    if hold_id is not None:
        query.addBindValue(int(hold_id))

    if not query.exec():
        raise Exception(query.lastError().text())

    if hold_id is None:
        hold_id = query.lastInsertId()
    try:
        return int(hold_id)
    except Exception:
        return hold_id


def replace_hold_sale_items(hold_id, item_rows):
    hold_id = int(hold_id)

    clear_query = QSqlQuery()
    clear_query.prepare("DELETE FROM holditems WHERE holdsale = ?")
    clear_query.addBindValue(hold_id)
    if not clear_query.exec():
        raise Exception(clear_query.lastError().text())

    for row in item_rows:
        item_query = QSqlQuery()
        item_query.prepare(
            """
            INSERT INTO holditems (
                holdsale, product, qty, unitrate, discount,
                discountamount, tax, taxamount, discount_input_mode, total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        )
        item_query.addBindValue(hold_id)
        item_query.addBindValue(row["product_id"])
        item_query.addBindValue(row["qty"])
        item_query.addBindValue(row["rate"])
        item_query.addBindValue(row["discount"])
        item_query.addBindValue(row["discountamount"])
        item_query.addBindValue(row["tax"])
        item_query.addBindValue(row["taxamount"])
        item_query.addBindValue(row["discount_input_mode"])
        item_query.addBindValue(row["total"])

        if not item_query.exec():
            raise Exception(
                f"Failed to insert hold item for product_id {row['product_id']}: {item_query.lastError().text()}"
            )


def delete_hold_sale(hold_id):
    hold_id = int(hold_id)

    item_delete = QSqlQuery()
    item_delete.prepare("DELETE FROM holditems WHERE holdsale = ?")
    item_delete.addBindValue(hold_id)
    if not item_delete.exec():
        raise Exception(item_delete.lastError().text())

    hold_delete = QSqlQuery()
    hold_delete.prepare("DELETE FROM holdsale WHERE id = ?")
    hold_delete.addBindValue(hold_id)
    if not hold_delete.exec():
        raise Exception(hold_delete.lastError().text())


def resolve_salesman_id(username):
    query = QSqlQuery()
    query.prepare("SELECT id FROM auth WHERE username = ?;")
    query.addBindValue(username)
    if not query.exec():
        raise Exception(query.lastError().text())
    if not query.next():
        raise Exception("Salesman account not found.")
    return query.value(0)


def fetch_customer_credit_position(customer_id):
    query = QSqlQuery()
    query.prepare(
        """
        SELECT
            COALESCE(name, 'Walk-in Customer'),
            COALESCE(receiveable, 0),
            COALESCE(credit_limit, 0)
        FROM customer
        WHERE id = ?
        """
    )
    query.addBindValue(customer_id)

    if not query.exec() or not query.next():
        raise Exception("Could not load customer credit information.")

    return {
        "customer_name": str(query.value(0) or ""),
        "current_receivable": float(query.value(1) or 0.0),
        "credit_limit": float(query.value(2) or 0.0),
    }


def persist_sales_customer_transaction(
    *,
    sales_id,
    customer_id,
    total_amount,
    received,
    remaining,
    salesman_id,
    session_id,
    payment,
):
    payable_before = 0.0
    receiveable_before = 0.0
    balance_state = compute_customer_transaction_balances(
        payable_before=0.0,
        receiveable_before=0.0,
        remaining=remaining,
    )

    if customer_id is not None:
        existing_balances = fetch_customer_balances(customer_id)
        payable_before = existing_balances["payable_before"]
        receiveable_before = existing_balances["receiveable_before"]
        balance_state = compute_customer_transaction_balances(
            payable_before=payable_before,
            receiveable_before=receiveable_before,
            remaining=remaining,
        )

    note = build_customer_transaction_note(
        sales_id=sales_id,
        total_amount=total_amount,
        received=received,
        remaining=remaining,
    )
    txn_payload = build_customer_transaction_payload(
        sales_id=sales_id,
        customer_id=customer_id,
        total_amount=float(total_amount or 0.0),
        received=float(received or 0.0),
        salesman_id=salesman_id,
        session_id=session_id,
        payment=payment,
        note=note,
        balance_state=balance_state,
    )
    transaction_id = insert_customer_transaction_record(txn_payload)

    if customer_id is not None:
        update_customer_running_balance(
            customer_id,
            payable_after=balance_state["payable_after"],
            receiveable_after=balance_state["receiveable_after"],
        )

    return {
        "transaction_id": transaction_id,
        "balance_state": balance_state,
        "payable_before": payable_before,
        "receiveable_before": receiveable_before,
    }


def persist_sales_receipt_header_and_prescription(header_payload, sales_prescription_payload=None):
    sales_id = insert_sales_header(header_payload)

    if sales_prescription_payload:
        prescription_payload = dict(sales_prescription_payload)
        attachment_source_paths = list(prescription_payload.pop("attachment_source_paths", []) or [])
        prescription_payload["sales_id"] = sales_id
        prescription_id = insert_sales_prescription_record(prescription_payload)
        for attachment_source_path in attachment_source_paths:
            if not attachment_source_path:
                continue
            save_sales_prescription_attachment(
                sales_prescription_id=int(prescription_id),
                sales_id=sales_id,
                source_path=attachment_source_path,
                uploaded_by=prescription_payload.get("created_by"),
            )

    return sales_id


def persist_sales_item_with_fifo(*, sales_id, row_payload, row_number):
    product_id = int(row_payload["product_id"])
    qty_needed = float(row_payload["qty"] or 0.0)

    total_available = fetch_total_available_stock(product_id)
    if qty_needed > total_available:
        raise Exception(f"Row {row_number}: Insufficient stock for product ID {product_id}.")

    sale_item_id = insert_sales_item_record(sales_id, row_payload)

    batch_rows = fetch_fifo_batch_rows(product_id)
    allocation_result = compute_fifo_allocation_plan(batch_rows, qty_needed)

    for allocation in allocation_result["allocations"]:
        batch_id = allocation["batch_id"]
        take_qty = allocation["take_qty"]
        decrement_batch_quantity(batch_id, take_qty)
        insert_sold_batch_record(sale_item_id, allocation)

    if allocation_result["remaining_qty"] > 0:
        raise Exception(
            f"FIFO allocation failed for product ID {product_id}. "
            f"Unallocated qty: {allocation_result['remaining_qty']}"
        )

    return {
        "sale_item_id": sale_item_id,
        "total_available": total_available,
        "allocation_result": allocation_result,
    }
