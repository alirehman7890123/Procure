def compute_purchase_return_settlement(*, total, received, writeoff_enabled=False):
    total = float(total or 0.0)
    received = float(received or 0.0)
    remaining = round(total - received, 2)

    settlement = {
        "total": total,
        "received": received,
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
            settlement["receiveable"] = remaining
        return settlement

    settlement["payable"] = abs(remaining)
    return settlement


def build_purchase_return_header_payload(
    *,
    supplier_id,
    rep_id,
    subtotal,
    roundoff,
    total,
    received,
    session_id,
    settlement,
):
    settlement = dict(settlement or {})
    return {
        "supplier": int(supplier_id),
        "rep": int(rep_id),
        "subtotal": float(subtotal or 0.0),
        "roundoff": float(roundoff or 0.0),
        "total": float(total or 0.0),
        "received": float(received or 0.0),
        "remaining": float(settlement.get("remaining") or 0.0),
        "writeoff": float(settlement.get("writeoff") or 0.0),
        "payable": float(settlement.get("payable") or 0.0),
        "receiveable": float(settlement.get("receiveable") or 0.0),
        "session_id": session_id,
    }


def build_purchase_return_transaction_payload(
    *,
    return_id,
    supplier_id,
    rep_id,
    total,
    received,
    session_id,
    payment,
    payable_before,
    receiveable_before,
    writeoff=0.0,
):
    total = float(total or 0.0)
    received = float(received or 0.0)
    remaining = round(total - received, 2)
    payment = dict(payment or {})

    current_receiveable = max(remaining, 0.0)
    current_payable = abs(remaining) if remaining < 0.0 else 0.0

    payable_after = float(payable_before or 0.0) + current_payable
    receiveable_after = float(receiveable_before or 0.0) + current_receiveable

    if current_receiveable > 0.0:
        due_amount = 0.0
        remaining_due = float(payable_before or 0.0)
        receiveable_now = current_receiveable
        remaining_now = receiveable_after
    else:
        due_amount = current_payable
        remaining_due = payable_after
        receiveable_now = 0.0
        remaining_now = float(receiveable_before or 0.0)

    return {
        "supplier": int(supplier_id),
        "transaction_type": "PURCHASE RETURN",
        "ref": None,
        "return_ref": return_id,
        "payable_before": float(payable_before or 0.0),
        "due_amount": due_amount,
        "paid": 0.0,
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
        "rep": int(rep_id),
        "note": (
            "Purchase Return recorded with total amount " + str(total) +
            ". Received: " + str(received) +
            ". Remaining: " + str(remaining_now) +
            ". Write-off: " + str(float(writeoff or 0.0))
        ),
        "session_id": session_id,
    }


def normalize_purchase_return_item_row(
    *,
    row_number,
    product_id,
    batch_no,
    purchased_qty,
    return_qty,
    rate,
    total,
    current_batch_qty,
):
    try:
        normalized_product_id = int(product_id)
        normalized_purchased_qty = int(purchased_qty)
        normalized_return_qty = int(return_qty)
        normalized_rate = float(rate)
        normalized_total = float(total)
        normalized_current_batch_qty = int(current_batch_qty)
    except (TypeError, ValueError):
        raise ValueError(f"Row {row_number}: Invalid purchase return row data.")

    normalized_batch_no = str(batch_no or "").strip()
    if not normalized_batch_no:
        raise ValueError(f"Row {row_number}: Batch is required.")
    if normalized_return_qty <= 0:
        raise ValueError(f"Row {row_number}: Return quantity must be greater than zero.")
    if normalized_return_qty > normalized_purchased_qty:
        raise ValueError(f"Row {row_number}: Return qty exceeds purchased qty.")
    if normalized_return_qty > normalized_current_batch_qty:
        raise ValueError(f"Row {row_number}: Insufficient stock in batch.")
    if normalized_rate < 0:
        raise ValueError(f"Row {row_number}: Rate cannot be negative.")
    if normalized_total < 0:
        raise ValueError(f"Row {row_number}: Total cannot be negative.")

    return {
        "product": normalized_product_id,
        "batch": normalized_batch_no,
        "purchased": normalized_purchased_qty,
        "returned": normalized_return_qty,
        "rate": normalized_rate,
        "total": normalized_total,
    }
