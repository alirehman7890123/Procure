def compute_sales_return_settlement(*, total, paid, writeoff_enabled=False):
    total = float(total or 0.0)
    paid = float(paid or 0.0)
    remaining = round(total - paid, 2)

    settlement = {
        "total": total,
        "paid": paid,
        "remaining": remaining,
        "writeoff": 0.0,
        "payable": 0.0,
        "receiveable": 0.0,
    }

    if remaining == 0.0:
        return settlement

    if remaining > 0.0:
        if writeoff_enabled:
            settlement["writeoff"] = remaining
        else:
            settlement["payable"] = remaining
        return settlement

    settlement["receiveable"] = abs(remaining)
    return settlement


def build_sales_return_header_payload(
    *,
    salesorder_id,
    customer_id,
    salesman_id,
    subtotal,
    roundoff,
    total,
    paid,
    session_id,
    settlement,
):
    settlement = dict(settlement or {})
    return {
        "salesorder": int(salesorder_id),
        "customer": customer_id if customer_id not in ("", None) else None,
        "salesman": int(salesman_id),
        "subtotal": float(subtotal or 0.0),
        "roundoff": float(roundoff or 0.0),
        "total": float(total or 0.0),
        "paid": float(paid or 0.0),
        "remaining": float(settlement.get("remaining") or 0.0),
        "writeoff": float(settlement.get("writeoff") or 0.0),
        "payable": float(settlement.get("payable") or 0.0),
        "receiveable": float(settlement.get("receiveable") or 0.0),
        "session_id": session_id,
    }


def build_sales_return_transaction_payload(
    *,
    return_id,
    customer_id,
    salesman_id,
    total,
    paid,
    session_id,
    payment,
    payable_before,
    receiveable_before,
):
    total = float(total or 0.0)
    paid = float(paid or 0.0)
    remaining = round(total - paid, 2)
    payment = dict(payment or {})

    current_payable = max(remaining, 0.0)
    current_receiveable = abs(remaining) if remaining < 0.0 else 0.0

    payable_after = float(payable_before or 0.0) + current_payable
    receiveable_after = float(receiveable_before or 0.0) + current_receiveable

    if current_payable > 0.0:
        due_amount = total
        remaining_due = current_payable
        receiveable_now = 0.0
        received = 0.0
        remaining_now = float(receiveable_before or 0.0)
    else:
        due_amount = 0.0
        remaining_due = float(payable_before or 0.0)
        receiveable_now = current_receiveable
        received = 0.0
        remaining_now = receiveable_after

    return {
        "customer": customer_id if customer_id not in ("", None) else None,
        "transaction_type": "SALES RETURN",
        "ref": None,
        "return_ref": return_id,
        "payable_before": float(payable_before or 0.0),
        "due_amount": due_amount,
        "paid": paid,
        "remaining_due": remaining_due,
        "payable_after": payable_after,
        "receiveable_before": float(receiveable_before or 0.0),
        "receiveable_now": receiveable_now,
        "received": received,
        "remaining_now": remaining_now,
        "receiveable_after": receiveable_after,
        "payment_method": payment.get("payment_method"),
        "bank_name": payment.get("bank_name"),
        "account_no": payment.get("account_no"),
        "transaction_mode": payment.get("transaction_mode"),
        "wallet_provider": payment.get("wallet_provider"),
        "wallet_no": payment.get("wallet_no"),
        "payment_reference": payment.get("payment_reference"),
        "salesman": int(salesman_id),
        "note": (
            f"Sales Return ID {return_id} recorded with total {total}, "
            f"paid {paid}, remaining {remaining}"
        ),
        "session_id": session_id,
    }


def normalize_sales_return_item_row(
    *,
    row_number,
    salesitem_id,
    product_id,
    sold_qty,
    return_qty,
    rate,
    total,
):
    try:
        normalized_salesitem_id = int(salesitem_id)
        normalized_product_id = int(product_id)
        normalized_sold_qty = int(sold_qty)
        normalized_return_qty = int(return_qty)
        normalized_rate = float(rate)
        normalized_total = float(total)
    except (TypeError, ValueError):
        raise ValueError(f"Row {row_number}: Invalid sales return row data.")

    if normalized_return_qty <= 0:
        raise ValueError(f"Row {row_number}: Return quantity must be greater than zero.")
    if normalized_return_qty > normalized_sold_qty:
        raise ValueError(f"Row {row_number}: Return quantity exceeds sold quantity.")
    if normalized_rate < 0:
        raise ValueError(f"Row {row_number}: Rate cannot be negative.")
    if normalized_total < 0:
        raise ValueError(f"Row {row_number}: Total cannot be negative.")

    return {
        "salesitem_id": normalized_salesitem_id,
        "product_id": normalized_product_id,
        "sold": normalized_sold_qty,
        "returned": normalized_return_qty,
        "rate": normalized_rate,
        "total": normalized_total,
    }


def compute_sales_return_inventory_plan(*, qty_sold, already_returned, return_qty, sold_batch_rows):
    qty_sold = int(qty_sold or 0)
    already_returned = int(already_returned or 0)
    return_qty = int(return_qty or 0)

    if return_qty <= 0:
        raise ValueError("Return quantity must be greater than zero.")
    if already_returned + return_qty > qty_sold:
        raise ValueError("Return quantity exceeds sold quantity.")

    remaining = return_qty
    plan = []

    for batch in sold_batch_rows or []:
        if remaining <= 0:
            break

        sold_batch_id = int(batch["sold_batch_id"])
        batch_id = int(batch["batch_id"])
        qty_taken = int(batch["qty_taken"] or 0)
        qty_returned = int(batch.get("qty_returned") or 0)
        available = qty_taken - qty_returned
        if available <= 0:
            continue

        qty_to_restore = min(available, remaining)
        plan.append(
            {
                "sold_batch_id": sold_batch_id,
                "batch_id": batch_id,
                "qty_taken": qty_taken,
                "qty_returned": qty_returned,
                "qty_to_restore": qty_to_restore,
                "remaining_after": remaining - qty_to_restore,
            }
        )
        remaining -= qty_to_restore

    if not plan:
        raise ValueError("No sold batch allocations found for this sales item.")
    if remaining > 0:
        raise ValueError("Not enough batch quantity to restore.")

    return {
        "allocations": plan,
        "remaining_qty": remaining,
    }
