from datetime import datetime, timedelta


def compute_due_date_from_option(due_date_option_text, today=None):
    option = str(due_date_option_text or "").strip()
    if option == "None" or not option.startswith("+"):
        return None

    try:
        days = int(option.split()[0][1:])
    except (ValueError, IndexError):
        return None

    base_date = today or datetime.now()
    return (base_date + timedelta(days=days)).strftime("%Y-%m-%d")


def resolve_sales_settlement(
    *,
    customer_id,
    remaining,
    writeoff_enabled=False,
    due_date_option_text="None",
    today=None,
):
    remaining = float(remaining or 0.0)

    settlement = {
        "writeoff": 0.0,
        "payable": 0.0,
        "receiveable": 0.0,
        "due_date": None,
    }

    if remaining > 0:
        if writeoff_enabled:
            settlement["writeoff"] = remaining
            return settlement

        if customer_id is None:
            raise ValueError(
                "Walk-In Customer Can't Have Remaining Amount\n"
                "Receive Full amount or Write off"
            )

        settlement["receiveable"] = remaining
        settlement["due_date"] = compute_due_date_from_option(
            due_date_option_text,
            today=today,
        )
        return settlement

    if remaining < 0:
        settlement["payable"] = abs(remaining)

    if customer_id is None:
        settlement["payable"] = 0.0
        settlement["receiveable"] = 0.0
        settlement["due_date"] = None

    return settlement


def build_sales_header_payload(
    *,
    customer_id,
    salesman_id,
    subtotal,
    discount,
    taxable,
    tax,
    net_amount,
    additional_charges,
    total,
    received,
    remaining,
    session_id,
    settlement,
):
    settlement = dict(settlement or {})
    return {
        "customer_id": customer_id,
        "salesman_id": salesman_id,
        "subtotal": float(subtotal or 0.0),
        "discount": float(discount or 0.0),
        "taxable": float(taxable or 0.0),
        "tax": float(tax or 0.0),
        "net_amount": float(net_amount or 0.0),
        "additional_charges": float(additional_charges or 0.0),
        "total": float(total or 0.0),
        "received": float(received or 0.0),
        "remaining": float(remaining or 0.0),
        "writeoff": float(settlement.get("writeoff") or 0.0),
        "payable": float(settlement.get("payable") or 0.0),
        "receiveable": float(settlement.get("receiveable") or 0.0),
        "session_id": session_id,
        "due_date": settlement.get("due_date"),
    }


def compute_customer_transaction_balances(
    *,
    payable_before,
    receiveable_before,
    remaining,
):
    payable_before = float(payable_before or 0.0)
    receiveable_before = float(receiveable_before or 0.0)
    remaining = float(remaining or 0.0)

    payable_now = 0.0
    receiveable_now = 0.0
    remaining_due = 0.0
    remaining_now = 0.0

    if remaining > 0:
        receiveable_now = remaining
        remaining_now = remaining
    elif remaining < 0:
        payable_now = abs(remaining)
        remaining_due = abs(remaining)

    payable_after = payable_before + payable_now
    receiveable_after = receiveable_before + receiveable_now

    return {
        "payable_before": payable_before,
        "receiveable_before": receiveable_before,
        "payable_now": payable_now,
        "receiveable_now": receiveable_now,
        "remaining_due": remaining_due,
        "remaining_now": remaining_now,
        "payable_after": payable_after,
        "receiveable_after": receiveable_after,
    }


def build_customer_transaction_note(*, sales_id, total_amount, received, remaining):
    return (
        f"Sale ID {sales_id} recorded with total {float(total_amount or 0.0)}, "
        f"received {float(received or 0.0)}, remaining {float(remaining or 0.0)}"
    )
